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

"""Unit tests for cache's show_spinner option."""

from tests import testutil

import streamlit as st


@st.cache(show_spinner=False)
def function_without_spinner():
    return 3


@st.cache(show_spinner=True)
def function_with_spinner():
    return 3


class CacheSpinnerTest(testutil.DeltaGeneratorTestCase):
    """
    We test the ability to turn on and off the spinner with the show_spinner
    option by inspecting the report queue.
    """

    def test_with_spinner(self):
        """If the show_spinner flag is set, there should be one element in the
        report queue.
        """
        function_with_spinner()
        self.assertFalse(self.forward_msg_queue.is_empty())

    def test_without_spinner(self):
        """If the show_spinner flag is not set, the report queue should be
        empty.
        """
        function_without_spinner()
        self.assertTrue(self.forward_msg_queue.is_empty())
