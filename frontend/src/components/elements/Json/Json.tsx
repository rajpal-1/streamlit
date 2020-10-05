/**
 * @license
 * Copyright 2018-2020 Streamlit Inc.
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

import "assets/css/write.scss"
import { IJson } from "autogen/proto"
import { requireNonNull } from "lib/utils"
import React, { ReactElement } from "react"

import ReactJson from "react-json-view"

export interface JsonProps {
  width: number
  element: IJson
}

/**
 * Functional element representing JSON structured text.
 */
export default function Json({ width, element }: JsonProps): ReactElement {
  const body = requireNonNull(element.body)
  const styleProp = { width }

  let bodyObject
  try {
    bodyObject = JSON.parse(body)
  } catch (e) {
    // If content fails to parse as Json, rebuild the error message
    // to show where the problem occurred.
    const pos = parseInt(e.message.replace(/[^0-9]/g, ""), 10)
    e.message += `\n${body.substr(0, pos + 1)} ← here`
    throw e
  }
  return (
    <div className="json-text-container stJson" style={styleProp}>
      <ReactJson
        src={bodyObject}
        displayDataTypes={false}
        displayObjectSize={false}
        name={false}
        style={{ font: "" }} // Unset so we can style via a CSS file.
      />
    </div>
  )
}
