# Copyright 2018-2020 Streamlit Inc.
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

"""slider unit test."""

import pytest
from parameterized import parameterized

import streamlit as st
from streamlit.errors import StreamlitAPIException
from streamlit.js_number import JSNumber
from tests import testutil

from datetime import datetime
from datetime import timezone
from datetime import timedelta


class SliderTest(testutil.DeltaGeneratorTestCase):
    """Test ability to marshall slider protos."""

    def test_just_label(self):
        """Test that it can be called with no value."""
        st.slider("the label")

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, [0])

    PST = timezone(timedelta(hours=-8), "PST")
    AWARE_START = datetime(2020, 1, 1, tzinfo=PST)
    AWARE_END = datetime(2020, 1, 5, tzinfo=PST)
    # datetimes are serialized in proto as micros since epoch
    AWARE_START_MICROS = 1577865600000000
    AWARE_END_MICROS = 1578211200000000

    @parameterized.expand(
        [
            (1, [1], 1),  # int
            ((0, 1), [0, 1], (0, 1)),  # int tuple
            ([0, 1], [0, 1], (0, 1)),  # int list
            (0.5, [0.5], 0.5),  # float
            ((0.2, 0.5), [0.2, 0.5], (0.2, 0.5)),  # float tuple
            ([0.2, 0.5], [0.2, 0.5], (0.2, 0.5)),  # float list
            (AWARE_START, [AWARE_START_MICROS], AWARE_START),  # datetime
            (
                (AWARE_START, AWARE_END),  # datetime tuple
                [AWARE_START_MICROS, AWARE_END_MICROS],
                (AWARE_START, AWARE_END),
            ),
            (
                [AWARE_START, AWARE_END],  # datetime list
                [AWARE_START_MICROS, AWARE_END_MICROS],
                (AWARE_START, AWARE_END),
            ),
        ]
    )
    def test_value_types(self, value, proto_value, return_value):
        """Test that it supports different types of values."""
        ret = st.slider("the label", value=value)

        self.assertEqual(ret, return_value)

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, proto_value)

    NAIVE_START = datetime(2020, 2, 1)
    NAIVE_END = datetime(2020, 2, 4)

    @parameterized.expand(
        [
            (NAIVE_START, NAIVE_START),  # naive datetime
            ((NAIVE_START, NAIVE_END), (NAIVE_START, NAIVE_END),),  # naive tuple
            ([NAIVE_START, NAIVE_END], (NAIVE_START, NAIVE_END),),  # naive list
        ]
    )
    def test_naive_datetime(self, value, return_value):
        """Ignore proto values (they change based on testing machine's timezone)"""
        ret = st.slider("the label", value=value)
        c = self.get_delta_from_queue().new_element.slider

        self.assertEqual(ret, return_value)
        self.assertEqual(c.label, "the label")

    def test_value_greater_than_min(self):
        ret = st.slider("Slider label", 10, 100, 0)
        c = self.get_delta_from_queue().new_element.slider

        self.assertEqual(ret, 0)
        self.assertEqual(c.min, 0)

    def test_value_smaller_than_max(self):
        ret = st.slider("Slider label", 10, 100, 101)
        c = self.get_delta_from_queue().new_element.slider

        self.assertEqual(ret, 101)
        self.assertEqual(c.max, 101)

    def test_max_min(self):
        ret = st.slider("Slider label", 101, 100, 101)
        c = self.get_delta_from_queue().new_element.slider

        self.assertEqual(ret, 101),
        self.assertEqual(c.min, 100)
        self.assertEqual(c.max, 101)

    def test_value_out_of_bounds(self):
        # Max int
        with pytest.raises(StreamlitAPIException) as exc:
            max_value = JSNumber.MAX_SAFE_INTEGER + 1
            st.slider("Label", max_value=max_value)
        self.assertEqual(
            "`max_value` (%s) must be <= (1 << 53) - 1" % str(max_value), str(exc.value)
        )

        # Min int
        with pytest.raises(StreamlitAPIException) as exc:
            min_value = JSNumber.MIN_SAFE_INTEGER - 1
            st.slider("Label", min_value=min_value)
        self.assertEqual(
            "`min_value` (%s) must be >= -((1 << 53) - 1)" % str(min_value),
            str(exc.value),
        )

        # Max float
        with pytest.raises(StreamlitAPIException) as exc:
            max_value = 2e308
            st.slider("Label", value=0.5, max_value=max_value)
        self.assertEqual(
            "`max_value` (%s) must be <= 1.797e+308" % str(max_value), str(exc.value)
        )

        # Min float
        with pytest.raises(StreamlitAPIException) as exc:
            min_value = -2e308
            st.slider("Label", value=0.5, min_value=min_value)
        self.assertEqual(
            "`min_value` (%s) must be >= -1.797e+308" % str(min_value), str(exc.value)
        )
