# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2024)
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

import asyncio
import gc
import math
import random
import unittest
from datetime import timedelta
from typing import Any, Dict, List, Set
from unittest.mock import patch

import numpy as np
import pytest
from parameterized import parameterized

from streamlit import util

TIME_STRING_TO_SECONDS_PARAMS = [
    ("float", 3.5, 3.5),
    ("timedelta", timedelta(minutes=3), 60 * 3),
    ("str 1 arg", "1d", 24 * 60 * 60),
    ("str 2 args", "1d23h", 24 * 60 * 60 + 23 * 60 * 60),
    (
        "complex str 3 args",
        "1 day 23hr 45minutes",
        24 * 60 * 60 + 23 * 60 * 60 + 45 * 60,
    ),
    ("str 2 args with float", "1.5d23.5h", 1.5 * 24 * 60 * 60 + 23.5 * 60 * 60),
]


class UtilTest(unittest.TestCase):
    """Test Streamlit utility functions."""

    def test_memoization(self):
        """Test that util.memoize works."""
        non_memoized_func = lambda: random.randint(0, 1000000)
        yes_memoized_func = util.memoize(non_memoized_func)
        assert non_memoized_func() != non_memoized_func()
        assert yes_memoized_func() == yes_memoized_func()

    @parameterized.expand(
        [("Linux", False, True), ("Windows", True, False), ("Darwin", False, True)]
    )
    def test_open_browser(self, os_type, webbrowser_expect, popen_expect):
        """Test web browser opening scenarios."""
        from streamlit import env_util

        env_util.IS_WINDOWS = os_type == "Windows"
        env_util.IS_DARWIN = os_type == "Darwin"
        env_util.IS_LINUX_OR_BSD = os_type == "Linux"

        with patch("streamlit.env_util.is_executable_in_path", return_value=True):
            with patch("webbrowser.open") as webbrowser_open:
                with patch("subprocess.Popen") as subprocess_popen:
                    util.open_browser("http://some-url")
                    assert webbrowser_expect == webbrowser_open.called
                    assert popen_expect == subprocess_popen.called

    def test_open_browser_linux_no_xdg(self):
        """Test opening the browser on Linux with no xdg installed"""
        from streamlit import env_util

        env_util.IS_LINUX_OR_BSD = True

        with patch("streamlit.env_util.is_executable_in_path", return_value=False):
            with patch("webbrowser.open") as webbrowser_open:
                with patch("subprocess.Popen") as subprocess_popen:
                    util.open_browser("http://some-url")
                    assert webbrowser_open.called
                    assert not subprocess_popen.called

    def test_functools_wraps(self):
        """Test wrap for functools.wraps"""

        import streamlit as st

        @st.cache
        def f():
            return True

        assert hasattr(f, "__wrapped__")

    @parameterized.expand(
        [
            ({}, {}),
            (
                {
                    "HELLO": 4,
                    "Hello": "world",
                    "hElLo": 5.5,
                    "": "",
                },
                {"hello": 4, "hello": "world", "hello": 5.5, "": ""},
            ),
        ]
    )
    def test_lower_clean_dict_keys(self, input_dict, answer_dict):
        return_dict = util.lower_clean_dict_keys(input_dict)
        assert return_dict == answer_dict

    @parameterized.expand(
        [
            (np.array([1, 2, 3, 4, 5]), 5, 4),
            # This one will have 0.15000000000000002 because of floating point precision
            (np.arange(0.0, 0.25, 0.05), 0.15, 3),
            ([0, 1, 2, 3], 3, 3),
            ([0.1, 0.2, 0.3], 0.2, 1),
            ([0.1, 0.2, None], None, 2),
            ([0.1, 0.2, float("inf")], float("inf"), 2),
            (["He", "ello w", "orld"], "He", 0),
            (list(np.arange(0.0, 0.25, 0.05)), 0.15, 3),
        ]
    )
    def test_successful_index_(self, input, find_value, expected_index):
        actual_index = util.index_(input, find_value)
        assert actual_index == expected_index

    @parameterized.expand(
        [
            (np.array([1, 2, 3, 4, 5]), 6),
            (np.arange(0.0, 0.25, 0.05), 0.1500002),
            ([0, 1, 2, 3], 3.00001),
            ([0.1, 0.2, 0.3], 0.3000004),
            ([0.1, 0.2, 0.3], None),
            (["He", "ello w", "orld"], "world"),
            (list(np.arange(0.0, 0.25, 0.05)), 0.150002),
        ]
    )
    def test_unsuccessful_index_(self, input, find_value):
        with pytest.raises(ValueError):
            util.index_(input, find_value)

    @parameterized.expand(
        [
            ({"x": ["a"]}, ["x"], {}),
            ({"a": ["a1", "a2"], "b": ["b1", "b2"]}, ["a"], {"b": ["b1", "b2"]}),
            ({"c": ["c1", "c2"]}, "no_existing_key", {"c": ["c1", "c2"]}),
            (
                {
                    "embed": ["true"],
                    "embed_options": ["show_padding", "show_colored_line"],
                },
                ["embed", "embed_options"],
                {},
            ),
            (
                {"EMBED": ["TRUE"], "EMBED_OPTIONS": ["DISABLE_SCROLLING"]},
                ["embed", "embed_options"],
                {},
            ),
        ]
    )
    def test_exclude_keys_in_dict(
        self,
        d: Dict[str, List[str]],
        keys_to_drop: List[str],
        result: Dict[str, List[str]],
    ):
        assert util.exclude_keys_in_dict(d, keys_to_drop) == result

    @parameterized.expand(
        [
            ({"x": ["a"]}, "x", {"a"}),
            ({"a": ["a1"], "b": ["b1", "b2"]}, "a", {"a1"}),
            ({"c": ["c1", "c2"]}, "no_existing_key", set()),
            (
                {
                    "embed": ["true"],
                    "embed_options": ["show_padding", "show_colored_line"],
                },
                "embed",
                {"true"},
            ),
            (
                {"EMBED": ["TRUE"], "EMBED_OPTIONS": ["DISABLE_SCROLLING"]},
                "embed_options",
                {"disable_scrolling"},
            ),
        ]
    )
    def test_extract_key_query_params(
        self, query_params: Dict[str, List[str]], param_key: str, result: Set[str]
    ):
        assert util.extract_key_query_params(query_params, param_key) == result

    def test_calc_md5_can_handle_bytes_and_strings(self):
        assert util.calc_md5("eventually bytes") == util.calc_md5(
            "eventually bytes".encode("utf-8")
        )

    def test_timed_cleanup_cache_gc(self):
        """Test that the TimedCleanupCache does not leave behind tasks when
        the cache is not externally reachable"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def create_cache():
            cache = util.TimedCleanupCache(maxsize=2, ttl=10)
            cache["foo"] = "bar"

            # expire_cache and create_cache
            assert len(asyncio.all_tasks()) > 1

        asyncio.run(create_cache())

        gc.collect()

        async def check():
            # Only has this function running
            assert len(asyncio.all_tasks()) == 1

        asyncio.run(check())

    @parameterized.expand(
        [
            *TIME_STRING_TO_SECONDS_PARAMS,
            ("None", None, math.inf),
        ]
    )
    def test_time_to_seconds_coerced(
        self, _, input_value: Any, expected_seconds: float
    ):
        """Test the various types of input that time_to_seconds accepts."""
        assert expected_seconds == util.time_to_seconds(input_value)

    @parameterized.expand(
        [
            *TIME_STRING_TO_SECONDS_PARAMS,
            ("None", None, None),
        ]
    )
    def test_time_to_seconds_not_coerced(
        self, _, input_value: Any, expected_seconds: float
    ):
        """Test the various types of input that time_to_seconds accepts."""
        assert expected_seconds == util.time_to_seconds(
            input_value, coerce_none_to_inf=False
        )

    def test_time_str_exception(self):
        """Test that a badly-formatted time string raises an exception."""
        with pytest.raises(util.BadTimeStringError):
            util.time_to_seconds("")

        with pytest.raises(util.BadTimeStringError):
            util.time_to_seconds("1 flecond")
