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

import axios, { AxiosRequestConfig } from "axios"
import { BaseUriParts } from "lib/UriUtil"
import { getCookie } from "lib/utils"

/**
 * Base class for HTTP Clients
 */
export default class HttpClient {
  protected readonly getServerUri: () => BaseUriParts | undefined
  protected readonly csrfEnabled: boolean

  public constructor(
    getServerUri: () => BaseUriParts | undefined,
    csrfEnabled: boolean
  ) {
    this.getServerUri = getServerUri
    this.csrfEnabled = csrfEnabled
  }

  public request(params: AxiosRequestConfig) {
    if (this.csrfEnabled) {
      const xsrf_cookie = getCookie("_xsrf")
      if (xsrf_cookie != null) {
        params.headers = Object.assign(
          { "X-Xsrftoken": xsrf_cookie },
          params.headers || {}
        )
        params.withCredentials = true
      }
    }
    return axios.request(params)
  }
}
