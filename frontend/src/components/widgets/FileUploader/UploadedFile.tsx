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

import React from "react"
import { Delete } from "baseui/icon"
import { styled, withStyleDeep } from "styletron-react"

import { IconButton } from "components/shared/Button"
import { MaterialIcon } from "components/shared/Icon"
import ProgressBar from "components/shared/ProgressBar"
import { Small, Error } from "components/shared/TextElements"
import { ExtendedFile, FileStatuses, getSizeDisplay } from "lib/FileHelper"
import {
  colors,
  Sizes,
  utilityClasses,
  spacingCalculator,
} from "lib/widgetTheme"

import "./FileUploader.scss"

export interface Props {
  file: ExtendedFile
  progress: number | undefined
  onDelete: (
    event: React.SyntheticEvent<HTMLElement> | null,
    id?: string
  ) => void
}

export interface FileStatusProps {
  file: ExtendedFile
  progress: number | undefined
}

const UploadedFileData = styled("div", {
  display: "flex",
  alignItems: "baseline",
  flex: 1,
  paddingLeft: spacingCalculator(),
  overflow: "hidden",
})

const UploadedFileName = withStyleDeep(
  styled("div", {
    marginRight: spacingCalculator(0.5),
  }),
  utilityClasses.ellipsis
)

const StyledUploadedFile = styled("div", {
  display: "flex",
  alignItems: "center",
  marginBottom: spacingCalculator(0.25),
})

export const ErrorMessage = styled("span", {
  marginRight: spacingCalculator(0.25),
})

export const FileIcon = styled("div", {
  display: "flex",
  padding: spacingCalculator(0.25),
  color: colors.secondary,
})

export const FileStatus = ({
  file,
  progress,
}: FileStatusProps): React.ReactElement | null => {
  if (progress) {
    return (
      <ProgressBar
        value={progress}
        size={Sizes.SMALL}
        overrides={{
          Bar: {
            style: {
              marginLeft: 0,
              marginTop: "4px",
            },
          },
        }}
      />
    )
  }

  if (file.status === FileStatuses.ERROR) {
    return (
      <Error className="fileError">
        <ErrorMessage>{file.errorMessage || "error"}</ErrorMessage>
        <MaterialIcon icon="error" />
      </Error>
    )
  }

  if (file.status === FileStatuses.UPLOADED) {
    return <Small>{getSizeDisplay(file.size, "b")}</Small>
  }

  if (file.status === FileStatuses.DELETING) {
    return <Small>Removing file</Small>
  }

  return null
}

const UploadedFile = ({
  file,
  progress,
  onDelete,
}: Props): React.ReactElement => {
  return (
    <StyledUploadedFile className="uploadedFile">
      <FileIcon>
        <MaterialIcon
          type="outlined"
          icon="insert_drive_file"
          size={Sizes.MEDIUM}
        />
      </FileIcon>
      <UploadedFileData className="uploadedFileData">
        <UploadedFileName className="uploadedFileName" title={file.name}>
          {file.name}
        </UploadedFileName>
        <FileStatus file={file} progress={progress} />
      </UploadedFileData>
      <IconButton onClick={onDelete} id={file.id}>
        <Delete size={22} />
      </IconButton>
    </StyledUploadedFile>
  )
}

export default UploadedFile
