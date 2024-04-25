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

from __future__ import annotations

import pandas as pd


class DataFrame:
    """This is dummy DataFrame class,
    which imitates pyspark.sql.dataframe.DataFrame class
    for testing purposes."""

    __module__ = "pyspark.sql.dataframe"

    def __init__(self, data: pd.DataFrame):
        self._data: pd.DataFrame = data

    def limit(self, n: int) -> "DataFrame":
        """Returns the top n element of a mock version of pyspark dataframe"""
        return DataFrame(self._data.head(n))

    def toPandas(self) -> pd.DataFrame:
        return self._data
