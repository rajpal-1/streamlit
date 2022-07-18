import asyncio
import traceback
from asyncio import AbstractEventLoop
from enum import Enum
from typing import Optional, Dict, Protocol, NamedTuple, Callable, Any

from streamlit import config
from streamlit.app_session import AppSession
from streamlit.caching import get_memo_stats_provider, \
    get_singleton_stats_provider
from streamlit.forward_msg_cache import (
    ForwardMsgCache,
    populate_hash_if_needed,
    create_reference_msg,
)
from streamlit.in_memory_file_manager import in_memory_file_manager
from streamlit.legacy_caching.caching import _mem_caches
from streamlit.logger import get_logger
from streamlit.proto.BackMsg_pb2 import BackMsg
from streamlit.proto.ForwardMsg_pb2 import ForwardMsg
from streamlit.session_data import SessionData
from streamlit.state import SessionStateStatProvider
from streamlit.stats import StatsManager
from streamlit.uploaded_file_manager import UploadedFileManager
from streamlit.watcher import LocalSourcesWatcher
from streamlit.web.server.server_util import is_cacheable_msg

LOGGER = get_logger(__name__)


class SessionClientDisconnectedError(Exception):
    """Raised by operations on a disconnected SessionClient."""


class SessionClient(Protocol):
    """Interface for sending data to a session's client."""

    def write_forward_msg(self, msg: ForwardMsg) -> None:
        """Deliver a ForwardMsg to the client.

        If the SessionClient has been disconnected, it should raise a
        SessionClientDisconnectedError.
        """


class RuntimeConfig(NamedTuple):
    """Config options for StreamlitRuntime."""

    # The filesystem path of the Streamlit script to run.
    script_path: str

    # The (optional) command line that Streamlit was started with
    # (e.g. "streamlit run app.py")
    command_line: Optional[str] = None

    # This will grow to contain various injectable dependencies!


class SessionInfo:
    """Type stored in our _session_info_by_id dict.

    For each AppSession, the server tracks that session's
    script_run_count. This is used to track the age of messages in
    the ForwardMsgCache.
    """

    def __init__(self, client: SessionClient, session: AppSession):
        """Initialize a SessionInfo instance.

        Parameters
        ----------
        session : AppSession
            The AppSession object.
        client : SessionClient
            The concrete SessionClient for this session.
        """
        self.session = session
        self.client = client
        self.script_run_count = 0


class State(Enum):
    INITIAL = "INITIAL"
    WAITING_FOR_FIRST_SESSION = "WAITING_FOR_FIRST_SESSION"
    ONE_OR_MORE_SESSIONS_CONNECTED = "ONE_OR_MORE_SESSIONS_CONNECTED"
    NO_SESSIONS_CONNECTED = "NO_SESSIONS_CONNECTED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"


class StreamlitRuntime:
    def __init__(self, event_loop: AbstractEventLoop, config: RuntimeConfig):
        """Create a StreamlitRuntime. It won't be started yet.

        StreamlitRuntime is *not* thread-safe. Its public methods are only
        safe to call on the same thread that its event loop runs on.

        Parameters
        ----------
        event_loop
            The asyncio event loop to run on.
        config
            Config options.
        """
        self._event_loop = event_loop
        self._config = config

        # Mapping of AppSession.id -> SessionInfo.
        self._session_info_by_id: Dict[str, SessionInfo] = {}

        self._state = State.INITIAL

        # asyncio eventloop synchronization primitives.
        # Note: these are not thread-safe!
        self._must_stop = asyncio.Event()
        self._has_connection = asyncio.Condition()
        self._need_send_data = asyncio.Event()

        self._message_cache = ForwardMsgCache()
        self._uploaded_file_mgr = UploadedFileManager()
        self._uploaded_file_mgr.on_files_updated.connect(self._on_files_updated)

        # StatsManager
        self._stats_mgr = StatsManager()
        self._stats_mgr.register_provider(get_memo_stats_provider())
        self._stats_mgr.register_provider(get_singleton_stats_provider())
        self._stats_mgr.register_provider(_mem_caches)
        self._stats_mgr.register_provider(self._message_cache)
        self._stats_mgr.register_provider(in_memory_file_manager)
        self._stats_mgr.register_provider(self._uploaded_file_mgr)
        self._stats_mgr.register_provider(
            SessionStateStatProvider(self._session_info_by_id)
        )

    @property
    def config(self) -> RuntimeConfig:
        return self._config

    @property
    def stats_manager(self) -> StatsManager:
        """The runtime's StatsManager instance."""
        return self._stats_mgr

    def _on_files_updated(self, session_id: str) -> None:
        """Event handler for UploadedFileManager.on_file_added.
        Ensures that uploaded files from stale sessions get deleted.

        Threading
        ---------
        May be called on any thread.
        """
        session_info = self._get_session_info(session_id)
        if session_info is None:
            # If an uploaded file doesn't belong to an existing session,
            # remove it so it doesn't stick around forever.
            self._uploaded_file_mgr.remove_session_files(session_id)

    def _get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """Return the SessionInfo with the given id, or None if no such
        session exists.

        Threading
        ---------
        Must be called on the eventloop thread.
        """
        return self._session_info_by_id.get(session_id, None)

    def start(self, on_started: Optional[Callable[[], Any]] = None) -> None:
        """Start the runtime. This must be called only once, before
        any other functions are called.

        Parameters
        ----------
        on_started
            An optional callback that will be called when the runtime's loop
            has started. It will be called on the eventloop thread.

        Returns
        -------
        None

        Threading
        ---------
        Must be called on the eventloop thread.
        """
        self._event_loop.call_soon_threadsafe(self._loop_coroutine, on_started)

    def stop(self) -> None:
        """Request that Streamlit close all sessions and stop running.
        Note that Streamlit won't stop running immediately.

        Threading
        ---------
        May be called on any thread.
        """
        if self._state in (State.STOPPING, State.STOPPED):
            return

        LOGGER.debug("Runtime stopping...")
        self._set_state(State.STOPPING)
        self._event_loop.call_soon_threadsafe(self._must_stop.set)

    def create_session(
        self,
        client: SessionClient,
        user_info: Dict[str, Optional[str]],
    ) -> str:
        """Create a new session and return its unique ID.

        Parameters
        ----------
        client
            A concrete SessionClient implementation for communicating with
            the session's client.
        user_info
            A dict that contains information about the session's user. For now,
            it only (optionally) contains the user's email address.

            {
                "email": "example@example.com"
            }

        Returns
        -------
        The session's unique string ID.

        Threading
        ---------
        Must be called on the eventloop thread.
        """
        if self._state in (State.STOPPING, State.STOPPED):
            raise RuntimeError(f"Can't create_session (state={self._state})")

        session_data = SessionData(
            self._config.script_path, self._config.command_line or ""
        )

        session = AppSession(
            event_loop=self._event_loop,
            session_data=session_data,
            uploaded_file_manager=self._uploaded_file_mgr,
            message_enqueued_callback=self._enqueued_some_message,
            local_sources_watcher=LocalSourcesWatcher(session_data),
            user_info=user_info,
        )

        LOGGER.debug(
            "Created new session for client %s. Session ID: %s", id(client), session.id
        )

        assert (
            session.id not in self._session_info_by_id
        ), f"session.id '{session.id}' registered multiple times!"

        self._session_info_by_id[session.id] = SessionInfo(client, session)
        self._set_state(State.ONE_OR_MORE_SESSIONS_CONNECTED)
        self._has_connection.notify_all()

        return session.id

    def close_session(self, session_id: str) -> None:
        """Close a session. It will stop producing ForwardMsgs.

        This function may be called multiple times for the same session,
        which is not an error. (Subsequent calls just no-op.)

        Parameters
        ----------
        session_id
            The session's unique ID.

        Returns
        -------
        None

        Threading
        ---------
        Must be called on the eventloop thread.
        """
        if session_id in self._session_info_by_id:
            session_info = self._session_info_by_id[session_id]
            del self._session_info_by_id[session_id]
            session_info.session.shutdown()

        if (
            self._state == State.ONE_OR_MORE_SESSIONS_CONNECTED
            and len(self._session_info_by_id) == 0
        ):
            self._set_state(State.NO_SESSIONS_CONNECTED)

    def handle_backmsg(self, session_id: str, msg: BackMsg) -> None:
        """Send a BackMsg to a connected session.

        Parameters
        ----------
        session_id
            The session's unique ID.
        msg
            The BackMsg to deliver to the session.

        Threading
        ---------
        Must be called on the eventloop thread.
        """
        if self._state in (State.STOPPING, State.STOPPED):
            raise RuntimeError(f"Can't handle_backmsg (state={self._state})")

        session_info = self._session_info_by_id.get(session_id)
        if session_info is None:
            LOGGER.debug(
                "Discarding BackMsg for disconnected session (id=%s)", session_id
            )
            return

        session_info.session.handle_backmsg(msg)

    def _set_state(self, new_state: State) -> None:
        LOGGER.debug("Runtime state: %s -> %s", self._state, new_state)
        self._state = new_state

    async def _loop_coroutine(self, on_started: Optional[Callable[[], Any]] = None) -> None:
        """The main Runtime loop.

        Returns
        -------
        None

        Threading
        ---------
        Must be called on the eventloop thread.
        """
        try:
            if self._state == State.INITIAL:
                self._set_state(State.WAITING_FOR_FIRST_SESSION)
            elif self._state == State.ONE_OR_MORE_SESSIONS_CONNECTED:
                pass
            else:
                raise RuntimeError(f"Bad server state at start: {self._state}")

            if on_started is not None:
                on_started()

            while not self._must_stop.is_set():
                if self._state == State.WAITING_FOR_FIRST_SESSION:
                    await asyncio.wait(
                        [self._must_stop.wait(), self._has_connection.wait()],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                elif self._state == State.ONE_OR_MORE_SESSIONS_CONNECTED:
                    self._need_send_data.clear()

                    # Shallow-clone our sessions into a list, so we can iterate
                    # over it and not worry about whether it's being changed
                    # outside this coroutine.
                    session_infos = list(self._session_info_by_id.values())

                    for session_info in session_infos:
                        msg_list = session_info.session.flush_browser_queue()
                        for msg in msg_list:
                            try:
                                self._send_message(session_info, msg)
                            except SessionClientDisconnectedError:
                                self.close_session(session_info.session.id)

                            # Yield for a tick after sending a message.
                            await asyncio.sleep(0)

                    # Yield for a few milliseconds between session message
                    # flushing.
                    await asyncio.sleep(0.01)

                elif self._state == State.NO_SESSIONS_CONNECTED:
                    await asyncio.wait(
                        [self._must_stop.wait(), self._has_connection.wait()],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                else:
                    # Break out of the thread loop if we encounter any other state.
                    break

                await asyncio.wait(
                    [self._must_stop.wait(), self._need_send_data.wait()],
                    return_when=asyncio.FIRST_COMPLETED,
                )

            # Shut down all AppSessions
            for session_info in list(self._session_info_by_id.values()):
                session_info.session.shutdown()

            self._set_state(State.STOPPED)

        except Exception:
            traceback.print_exc()
            LOGGER.info(
                """
Please report this bug at https://github.com/streamlit/streamlit/issues.
"""
            )

        finally:
            self._on_stopped()

    def _on_stopped(self) -> None:
        """Called when our runloop is exiting."""
        raise Exception("TODO")

    def _send_message(self, session_info: SessionInfo, msg: ForwardMsg) -> None:
        """Send a message to a client.

        If the client is likely to have already cached the message, we may
        instead send a "reference" message that contains only the hash of the
        message.

        Parameters
        ----------
        session_info : SessionInfo
            The SessionInfo associated with websocket
        msg : ForwardMsg
            The message to send to the client

        Threading
        ---------
        Must be called on the eventloop thread.
        """
        msg.metadata.cacheable = is_cacheable_msg(msg)
        msg_to_send = msg
        if msg.metadata.cacheable:
            populate_hash_if_needed(msg)

            if self._message_cache.has_message_reference(
                msg, session_info.session, session_info.script_run_count
            ):
                # This session has probably cached this message. Send
                # a reference instead.
                LOGGER.debug("Sending cached message ref (hash=%s)", msg.hash)
                msg_to_send = create_reference_msg(msg)

            # Cache the message so it can be referenced in the future.
            # If the message is already cached, this will reset its
            # age.
            LOGGER.debug("Caching message (hash=%s)", msg.hash)
            self._message_cache.add_message(
                msg, session_info.session, session_info.script_run_count
            )

        # If this was a `script_finished` message, we increment the
        # script_run_count for this session, and update the cache
        if (
            msg.WhichOneof("type") == "script_finished"
            and msg.script_finished == ForwardMsg.FINISHED_SUCCESSFULLY
        ):
            LOGGER.debug(
                "Script run finished successfully; "
                "removing expired entries from MessageCache "
                "(max_age=%s)",
                config.get_option("global.maxCachedMessageAge"),
            )
            session_info.script_run_count += 1
            self._message_cache.remove_expired_session_entries(
                session_info.session, session_info.script_run_count
            )

        # Ship it off!
        session_info.client.write_forward_msg(msg_to_send)

    def _enqueued_some_message(self) -> None:
        self._event_loop.call_soon_threadsafe(self._need_send_data.set)
