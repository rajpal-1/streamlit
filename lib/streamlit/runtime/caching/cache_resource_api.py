# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""@st.cache_resource implementation"""

from __future__ import annotations

import threading
import types
from typing import Any, Callable, TypeVar, cast, overload

from pympler import asizeof

import streamlit as st
from streamlit.logger import get_logger
from streamlit.runtime.caching.cache_errors import CacheKeyNotFoundError, CacheType
from streamlit.runtime.caching.cache_utils import (
    Cache,
    CachedFunction,
    CachedResult,
    CacheMessagesCallStack,
    CacheWarningCallStack,
    ElementMsgData,
    MsgData,
    MultiCacheResults,
    create_cache_wrapper,
)
from streamlit.runtime.metrics_util import gather_metrics
from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
from streamlit.runtime.stats import CacheStat, CacheStatsProvider

_LOGGER = get_logger(__name__)


CACHE_RESOURCE_CALL_STACK = CacheWarningCallStack(CacheType.RESOURCE)
CACHE_RESOURCE_MESSAGE_CALL_STACK = CacheMessagesCallStack(CacheType.RESOURCE)


class ResourceCaches(CacheStatsProvider):
    """Manages all ResourceCache instances"""

    def __init__(self):
        self._caches_lock = threading.Lock()
        self._function_caches: dict[str, ResourceCache] = {}

    def get_cache(
        self, key: str, display_name: str, allow_widgets: bool
    ) -> ResourceCache:
        """Return the mem cache for the given key.

        If it doesn't exist, create a new one with the given params.
        """

        # Get the existing cache, if it exists, and validate that its params
        # haven't changed.
        with self._caches_lock:
            cache = self._function_caches.get(key)
            if cache is not None:
                return cache

            # Create a new cache object and put it in our dict
            _LOGGER.debug("Creating new ResourceCache (key=%s)", key)
            cache = ResourceCache(
                key=key, display_name=display_name, allow_widgets=allow_widgets
            )
            self._function_caches[key] = cache
            return cache

    def clear_all(self) -> None:
        """Clear all resource caches."""
        with self._caches_lock:
            self._function_caches = {}

    def get_stats(self) -> list[CacheStat]:
        with self._caches_lock:
            # Shallow-clone our caches. We don't want to hold the global
            # lock during stats-gathering.
            function_caches = self._function_caches.copy()

        stats: list[CacheStat] = []
        for cache in function_caches.values():
            stats.extend(cache.get_stats())
        return stats


# Singleton ResourceCaches instance
_resource_caches = ResourceCaches()


def get_resource_cache_stats_provider() -> CacheStatsProvider:
    """Return the StatsProvider for all @st.cache_resource functions."""
    return _resource_caches


class CacheResourceFunction(CachedFunction):
    """Implements the CachedFunction protocol for @st.cache_resource"""

    @property
    def cache_type(self) -> CacheType:
        return CacheType.RESOURCE

    @property
    def warning_call_stack(self) -> CacheWarningCallStack:
        return CACHE_RESOURCE_CALL_STACK

    @property
    def message_call_stack(self) -> CacheMessagesCallStack:
        return CACHE_RESOURCE_MESSAGE_CALL_STACK

    @property
    def display_name(self) -> str:
        """A human-readable name for the cached function"""
        return f"{self.func.__module__}.{self.func.__qualname__}"

    def get_function_cache(self, function_key: str) -> Cache:
        return _resource_caches.get_cache(
            key=function_key,
            display_name=self.display_name,
            allow_widgets=self.allow_widgets,
        )


class CacheResourceAPI:
    """Implements the public st.cache_resource API: the @st.cache_resource decorator,
    and st.cache_resource.clear().
    """

    # Type-annotate the decorator function.
    # (See https://mypy.readthedocs.io/en/stable/generics.html#decorator-factories)

    F = TypeVar("F", bound=Callable[..., Any])

    # Bare decorator usage
    @overload
    def __call__(self, func: F) -> F:
        ...

    # Decorator with arguments
    @overload
    def __call__(
        self,
        *,
        show_spinner: bool | str = True,
        suppress_st_warning=False,
        experimental_allow_widgets: bool = False,
    ) -> Callable[[F], F]:
        ...

    # __call__ should be a static method, but there's a mypy bug that
    # breaks type checking for overloaded static functions:
    # https://github.com/python/mypy/issues/7781
    @gather_metrics("cache_resource")
    def __call__(
        self,
        func: F | None = None,
        *,
        show_spinner: bool | str = True,
        suppress_st_warning=False,
        experimental_allow_widgets: bool = False,
    ):
        """Function decorator to store cached resources.

        Each cache_resource object is shared across all users connected to the app.
        Cached resources *must* be thread-safe, because they can be accessed from
        multiple threads concurrently.

        (If thread-safety is an issue, consider using ``st.session_state`` to
        store per-session cached resources instead.)

        You can clear a cache_resource function's cache with f.clear().

        Parameters
        ----------
        func : callable
            The function that creates the cached resource. Streamlit hashes the
            function's source code.

        show_spinner : boolean or string
            Enable the spinner. Default is True to show a spinner when there is
            a "cache miss" and the cached resource is being created. If string,
            value of show_spinner param will be used for spinner text.

        suppress_st_warning : boolean
            Suppress warnings about calling Streamlit commands from within
            the cache_resource function.

        experimental_allow_widgets : boolean
            Allow widgets to be used in the cache_resource function. Defaults to False.

        .. note::
            Support for widgets in cached functions is currently experimental.
            To enable it, set the parameter ``experimental_allow_widgets=True``
            in ``@st.cache_resource``. Note that this may lead to excessive
            memory use since the widget value is treated as an additional input
            parameter to the cache. We may remove support for this option at any
            time without notice.

        Example
        -------
        >>> @st.cache_resource
        ... def get_database_session(url):
        ...     # Create a database session object that points to the URL.
        ...     return session
        ...
        >>> s1 = get_database_session(SESSION_URL_1)
        >>> # Actually executes the function, since this is the first time it was
        >>> # encountered.
        >>>
        >>> s2 = get_database_session(SESSION_URL_1)
        >>> # Does not execute the function. Instead, returns its previously computed
        >>> # value. This means that now the connection object in s1 is the same as in s2.
        >>>
        >>> s3 = get_database_session(SESSION_URL_2)
        >>> # This is a different URL, so the function executes.

        By default, all parameters to a cache_resource function must be hashable.
        Any parameter whose name begins with ``_`` will not be hashed. You can use
        this as an "escape hatch" for parameters that are not hashable:

        >>> @st.cache_resource
        ... def get_database_session(_sessionmaker, url):
        ...     # Create a database connection object that points to the URL.
        ...     return connection
        ...
        >>> s1 = get_database_session(create_sessionmaker(), DATA_URL_1)
        >>> # Actually executes the function, since this is the first time it was
        >>> # encountered.
        >>>
        >>> s2 = get_database_session(create_sessionmaker(), DATA_URL_1)
        >>> # Does not execute the function. Instead, returns its previously computed
        >>> # value - even though the _sessionmaker parameter was different
        >>> # in both calls.

        A cache_resource function's cache can be procedurally cleared:

        >>> @st.cache_resource
        ... def get_database_session(_sessionmaker, url):
        ...     # Create a database connection object that points to the URL.
        ...     return connection
        ...
        >>> get_database_session.clear()
        >>> # Clear all cached entries for this function.

        """
        # Support passing the params via function decorator, e.g.
        # @st.cache_resource(show_spinner=False)
        if func is None:
            return lambda f: create_cache_wrapper(
                CacheResourceFunction(
                    func=f,
                    show_spinner=show_spinner,
                    suppress_st_warning=suppress_st_warning,
                    allow_widgets=experimental_allow_widgets,
                )
            )

        return create_cache_wrapper(
            CacheResourceFunction(
                func=cast(types.FunctionType, func),
                show_spinner=show_spinner,
                suppress_st_warning=suppress_st_warning,
                allow_widgets=experimental_allow_widgets,
            )
        )

    @staticmethod
    @gather_metrics("clear_resource_caches")
    def clear() -> None:
        """Clear all cache_resource caches."""
        _resource_caches.clear_all()


class ResourceCache(Cache):
    """Manages cached values for a single st.cache_resource function."""

    def __init__(self, key: str, display_name: str, allow_widgets: bool = False):
        self.key = key
        self.display_name = display_name
        self._mem_cache: dict[str, MultiCacheResults] = {}
        self._mem_cache_lock = threading.Lock()
        self.allow_widgets = allow_widgets

    def read_result(self, key: str) -> CachedResult:
        """Read a value and associated messages from the cache.
        Raise `CacheKeyNotFoundError` if the value doesn't exist.
        """
        with self._mem_cache_lock:
            if key in self._mem_cache:
                multi_results = self._mem_cache[key]

                ctx = get_script_run_ctx()
                if not ctx:
                    raise CacheKeyNotFoundError()

                widget_key = multi_results.get_current_widget_key(
                    ctx, CacheType.RESOURCE
                )
                if widget_key in multi_results.results:
                    return multi_results.results[widget_key]
                else:
                    raise CacheKeyNotFoundError()
            else:
                raise CacheKeyNotFoundError()

    @gather_metrics("_cache_resource_object")
    def write_result(self, key: str, value: Any, messages: list[MsgData]) -> None:
        """Write a value and associated messages to the cache."""
        ctx = get_script_run_ctx()
        if ctx is None:
            return

        main_id = st._main.id
        sidebar_id = st.sidebar.id
        if self.allow_widgets:
            widgets = {
                msg.widget_metadata.widget_id
                for msg in messages
                if isinstance(msg, ElementMsgData) and msg.widget_metadata is not None
            }
        else:
            widgets = set()

        with self._mem_cache_lock:
            try:
                multi_results = self._mem_cache[key]
            except KeyError:
                multi_results = MultiCacheResults(widget_ids=widgets, results={})

            multi_results.widget_ids.update(widgets)
            widget_key = multi_results.get_current_widget_key(ctx, CacheType.RESOURCE)

            result = CachedResult(value, messages, main_id, sidebar_id)
            multi_results.results[widget_key] = result
            self._mem_cache[key] = multi_results

    def clear(self) -> None:
        with self._mem_cache_lock:
            self._mem_cache.clear()

    def get_stats(self) -> list[CacheStat]:
        # Shallow clone our cache. Computing item sizes is potentially
        # expensive, and we want to minimize the time we spend holding
        # the lock.
        with self._mem_cache_lock:
            mem_cache = self._mem_cache.copy()

        stats: list[CacheStat] = []
        for item_key, item_value in mem_cache.items():
            stats.append(
                CacheStat(
                    category_name="st_cache_resource",
                    cache_name=self.display_name,
                    byte_length=asizeof.asizeof(item_value),
                )
            )
        return stats
