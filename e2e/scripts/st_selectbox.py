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

import streamlit as st

options = ("male", "female")
i1 = st.selectbox("selectbox 1", options, 1)
st.write("value 1:", i1)

i2 = st.selectbox("selectbox 2", options, 0, format_func=lambda x: x.capitalize())
st.write("value 2:", i2)

i3 = st.selectbox("selectbox 3", [])
st.write("value 3:", i3)

more_options = [
    "e2e/scripts/components_iframe.py",
    "e2e/scripts/st_warning.py",
    "e2e/scripts/st_container.py",
    "e2e/scripts/st_dataframe_sort_column.py",
    "e2e/scripts/app_hotkeys.py",
    "e2e/scripts/st_info.py",
    "e2e/scripts/st_echo.py",
    "e2e/scripts/st_json.py",
    "e2e/scripts/st_experimental_get_query_params.py",
    "e2e/scripts/st_markdown.py",
    "e2e/scripts/st_color_picker.py",
    "e2e/scripts/st_expander.py",
]
i4 = st.selectbox("selectbox 4", options, 0)
st.write("value 4:", i4)