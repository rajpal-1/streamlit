# Copyright 2018-2022 Streamlit Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Provides global MediaFileManager object as `media_file_manager`."""

import collections
import threading
from enum import Enum
from typing import Dict, Set, Optional, Union

from streamlit import util
from streamlit.logger import get_logger
from .media_file_storage import MediaFileStorage

LOGGER = get_logger(__name__)

STATIC_MEDIA_ENDPOINT = "/media"


class MediaFileType(Enum):
    # used for images and videos in st.image() and st.video()
    MEDIA = "media"

    # used for st.download_button files
    DOWNLOADABLE = "downloadable"


def _get_session_id() -> str:
    """Get the active AppSession's session_id."""
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    ctx = get_script_run_ctx()
    if ctx is None:
        # This is only None when running "python myscript.py" rather than
        # "streamlit run myscript.py". In which case the session ID doesn't
        # matter and can just be a constant, as there's only ever "session".
        return "dontcare"
    else:
        return ctx.session_id


class MediaFileMetadata:
    def __init__(
        self,
        file_id: str,
        file_name: Optional[str] = None,
        file_type: MediaFileType = MediaFileType.MEDIA,
    ):
        self._file_id = file_id
        self._file_name = file_name
        self._file_type = file_type
        self._is_marked_for_delete = False

    def __repr__(self) -> str:
        return util.repr_(self)

    @property
    def id(self) -> str:
        return self._file_id

    @property
    def file_type(self) -> MediaFileType:
        return self._file_type

    @property
    def file_name(self) -> Optional[str]:
        return self._file_name

    def _mark_for_delete(self) -> None:
        self._is_marked_for_delete = True


class MediaFileManager:
    """In-memory file manager for MediaFile objects.

    This keeps track of:
    - Which files exist, and what their IDs are. This is important so we can
      serve files by ID -- that's the whole point of this class!
    - Which files are being used by which AppSession (by ID). This is
      important so we can remove files from memory when no more sessions need
      them.
    - The exact location in the app where each file is being used (i.e. the
      file's "coordinates"). This is is important so we can mark a file as "not
      being used by a certain session" if it gets replaced by another file at
      the same coordinates. For example, when doing an animation where the same
      image is constantly replace with new frames. (This doesn't solve the case
      where the file's coordinates keep changing for some reason, though! e.g.
      if new elements keep being prepended to the app. Unlikely to happen, but
      we should address it at some point.)
    """

    def __init__(self, storage: MediaFileStorage):
        self._storage = storage

        # Dict of file ID to MediaFile.
        self._files_by_id: Dict[str, MediaFileMetadata] = dict()

        # Dict[session ID][coordinates] -> file_id.
        self._files_by_session_and_coord: Dict[
            str, Dict[str, str]
        ] = collections.defaultdict(dict)

        # MediaFileManager is used from multiple threads, so all operations
        # need to be protected with a Lock. (This is not an RLock, which
        # means taking it multiple times from the same thread will deadlock.)
        self._lock = threading.Lock()

    def _get_inactive_file_ids(self) -> Set[str]:
        """Compute the set of files that are stored in the manager, but are
        not referenced by any active session. These are files that can be
        safely deleted.

        Thread safety: callers must hold `self._lock`.
        """
        # Get the set of all our file IDs.
        file_ids = set(self._files_by_id.keys())

        # Subtract all IDs that are in use by each session
        for session_file_ids_by_coord in self._files_by_session_and_coord.values():
            file_ids.difference_update(session_file_ids_by_coord.values())

        return file_ids

    def remove_orphaned_files(self) -> None:
        """Remove all files that are no longer referenced by any active session.

        Safe to call from any thread.
        """
        LOGGER.debug("Removing orphaned files...")

        with self._lock:
            for file_id in self._get_inactive_file_ids():
                file = self._files_by_id[file_id]
                if file.file_type == MediaFileType.MEDIA:
                    self._delete_file(file_id)
                elif file.file_type == MediaFileType.DOWNLOADABLE:
                    if file._is_marked_for_delete:
                        self._delete_file(file_id)
                    else:
                        file._mark_for_delete()

    def _delete_file(self, file_id: str) -> None:
        """Delete the given file from storage, and remove its metadata from
        self._files_by_id.

        Thread safety: callers must hold `self._lock`.
        """
        LOGGER.debug("Deleting File: %s", file_id)
        self._storage.delete_file(file_id)
        del self._files_by_id[file_id]

    def clear_session_refs(self, session_id: Optional[str] = None) -> None:
        """Remove the given session's file references.

        (This does not remove any files from the manager - you must call
        `remove_orphaned_files` for that.)

        Should be called whenever ScriptRunner completes and when a session ends.

        Safe to call from any thread.
        """
        if session_id is None:
            session_id = _get_session_id()

        LOGGER.debug("Disconnecting files for session with ID %s", session_id)

        with self._lock:
            if session_id in self._files_by_session_and_coord:
                del self._files_by_session_and_coord[session_id]

        LOGGER.debug(
            "Sessions still active: %r", self._files_by_session_and_coord.keys()
        )

        LOGGER.debug(
            "Files: %s; Sessions with files: %s",
            len(self._files_by_id),
            len(self._files_by_session_and_coord),
        )

    def add(
        self,
        path_or_data: Union[bytes, str],
        mimetype: str,
        coordinates: str,
        file_name: Optional[str] = None,
        is_for_static_download: bool = False,
    ) -> str:
        """Add a new MediaFile with the given parameters and return its URL.

        If an identical file already exists, return the existing URL
        and registers the current session as a user.

        Safe to call from any thread.

        Parameters
        ----------
        path_or_data : bytes or str
            If bytes: the media file's raw data. If str: the name of a file
            to load from disk.
        mimetype : str
            The mime type for the file. E.g. "audio/mpeg".
            This string will be used in the "Content-Type" header when the file
            is served over HTTP.
        coordinates : str
            Unique string identifying an element's location.
            Prevents memory leak of "forgotten" file IDs when element media
            is being replaced-in-place (e.g. an st.image stream).
            coordinates should be of the form: "1.(3.-14).5"
        file_name : str or None
            Optional file_name. Used to set the filename in the response header.
        is_for_static_download: bool
            Indicate that data stored for downloading as a file,
            not as a media for rendering at page. [default: False]

        Returns
        -------
        str
            The url that the frontend can use to fetch the media.

        Raises
        ------
        If a filename is passed, any Exception raised when trying to read the
        file will be re-raised.
        """

        session_id = _get_session_id()

        with self._lock:
            file_id = self._storage.load_and_get_id(path_or_data, mimetype, file_name)
            metadata = MediaFileMetadata(
                file_id=file_id,
                file_name=file_name,
                file_type=MediaFileType.DOWNLOADABLE
                if is_for_static_download
                else MediaFileType.MEDIA,
            )

            self._files_by_id[file_id] = metadata
            self._files_by_session_and_coord[session_id][coordinates] = file_id

            return self._storage.get_url(file_id)

    def get(self, filename: str) -> MediaFileMetadata:
        """Returns the MediaFile for the given filename.

        Raises KeyError if not found.

        Safe to call from any thread.
        """
        # Filename is {file_id}.{extension} but MediaFileManager
        # is indexed by requested_hash.
        file_id = filename.split(".")[0]

        # dictionary access is atomic, so no need to take a lock.
        return self._files_by_id[file_id]

    def __contains__(self, file_id: str) -> bool:
        return file_id in self._files_by_id

    def __len__(self):
        return len(self._files_by_id)


# Singleton MediaFileManager instance. The Runtime will initialize
# this during startup.
_media_file_manager: Optional[MediaFileManager] = None


def set_media_file_manager(manager: MediaFileManager) -> None:
    """Set the singleton MediaFileManager instance."""
    global _media_file_manager
    if _media_file_manager is not None:
        raise RuntimeError("MediaFileManager singleton already exists!")
    _media_file_manager = manager


def get_media_file_manager() -> MediaFileManager:
    """Return the singleton MediaFileManager instance. Raise an error
    if it hasn't been instantiated yet.
    """
    if _media_file_manager is None:
        raise RuntimeError("MediaFileManager hasn't been created!")
    return _media_file_manager
