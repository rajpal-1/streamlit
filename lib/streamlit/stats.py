# Copyright 2018-2021 Streamlit Inc.
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

import json
import typing
from abc import abstractmethod
from typing import List

import tornado.web

from streamlit.server.routes import allow_cross_origin_requests


class CacheStat(typing.NamedTuple):
    """Describes a single cache entry.

    Properties
    ----------
    category_name : str
        A human-readable name for the cache "category" that the entry belongs
        to - e.g. "st.memo", "session_state", etc.
    cache_name : str
        A human-readable name for cache instance that the entry belongs to.
        For "st.memo" and other function decorator caches, this might be the
        name of the cached function. If the cache category doesn't have
        multiple separate cache instances, this can just be the empty string.
    entry_name : str
        The name of the entry in the cache. It's nice if this is human-readable,
        but that's not always possible.
    byte_length : int
        The entry's memory footprint in bytes.
    """

    category_name: str
    cache_name: str
    entry_name: str
    byte_length: int

    def to_json(self) -> typing.Dict[str, typing.Any]:
        return {
            "category_name": self.category_name,
            "cache_name": self.cache_name,
            "entry_name": self.entry_name,
            "byte_length": self.byte_length,
        }


class CacheStatsProvider:
    @abstractmethod
    def get_stats(self) -> List[CacheStat]:
        raise NotImplementedError


class StatsManager:
    def __init__(self):
        self._cache_stats_providers: List[CacheStatsProvider] = []

    def register_provider(self, provider: CacheStatsProvider) -> None:
        """Register a CacheStatsProvider with the manager.
        This function is not thread-safe. Call it immediately after
        creation.
        """
        self._cache_stats_providers.append(provider)

    def get_stats(self) -> List[CacheStat]:
        """Return a list containing all stats from each registered provider."""
        all_stats: List[CacheStat] = []
        for provider in self._cache_stats_providers:
            all_stats.extend(provider.get_stats())
        return all_stats


class StatsHandler(tornado.web.RequestHandler):
    def initialize(self, stats_manager: StatsManager) -> None:
        self._manager = stats_manager

    def set_default_headers(self):
        if allow_cross_origin_requests():
            self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")

    def options(self):
        """/OPTIONS handler for preflight CORS checks."""
        self.set_status(204)
        self.finish()

    def get(self) -> None:
        json_stats = [stat.to_json() for stat in self._manager.get_stats()]
        self.write(json.dumps(json_stats, indent=2))
        self.set_status(200)
