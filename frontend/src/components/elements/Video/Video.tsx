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

import { IVideo, Video as VideoProto } from "autogen/proto"
import { buildMediaUri } from "lib/UriUtil"
import { requireNonNull } from "lib/utils"
import React, { ReactElement, useEffect, useRef } from "react"

export interface VideoProps {
  width: number
  element: IVideo
}

export default function Video({ element, width }: VideoProps): ReactElement {
  const videoRef = useRef<HTMLVideoElement>(null)

  /* Element may contain "url" or "data" property. */

  const type = requireNonNull(element.type)
  const url = requireNonNull(element.url)

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.currentTime = requireNonNull(element.startTime)
    }
  }, [element])

  const getYoutubeSrc = (url: string): string => {
    const startTime = requireNonNull(element.startTime)
    if (startTime) {
      return `${url}?start=${startTime}`
    }
    return url
  }

  /* Is this a YouTube link? If so we need a fancier tag.
       NOTE: This part assumes the URL is already an "embed" link.
    */
  if (type === VideoProto.Type.YOUTUBE_IFRAME) {
    const height = width * 0.75

    return (
      <iframe
        title={url}
        src={getYoutubeSrc(url)}
        width={width}
        height={height}
        frameBorder="0"
        allow="autoplay; encrypted-media"
        allowFullScreen
      />
    )
  }

  return (
    <video
      ref={videoRef}
      controls
      src={buildMediaUri(url)}
      className="stVideo"
      style={{ width }}
    />
  )
}
