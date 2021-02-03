/**
 * @license
 * Copyright 2018-2021 Streamlit Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { LightTheme, DarkTheme } from "baseui"
import { lightBaseUITheme, darkBaseUITheme } from "./baseui"
import base from "./baseTheme"
import light from "./lightTheme"
import dark from "./darkTheme"
import sidebar from "./sidebarTheme"
import { Theme, ThemeConfig } from "./types"

export * from "./baseui"
export * from "./globalStyles"
export * from "./types"
export * from "./utils"
export const sidebarTheme: Theme = sidebar

export const baseTheme: ThemeConfig = {
  name: "base",
  emotion: base,
  baseweb: LightTheme,
  basewebTheme: lightBaseUITheme,
}
export const darkTheme: ThemeConfig = {
  name: "Dark",
  emotion: dark,
  baseweb: DarkTheme,
  basewebTheme: darkBaseUITheme,
}

export const lightTheme: ThemeConfig = {
  name: "Light",
  emotion: light,
  baseweb: LightTheme,
  basewebTheme: lightBaseUITheme,
}
