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
import Dropzone, { FileRejection } from "react-dropzone"
import { styled } from "styletron-react"

import Button, { Kind } from "components/shared/Button"
import { ExtendedFile } from "lib/FileHelper"
import { colors, spacing, variables } from "lib/widgetTheme"

import FileDropzoneInstructions from "./FileDropzoneInstructions"

export interface Props {
  disabled: boolean
  onDrop: (
    acceptedFiles: ExtendedFile[],
    rejectedFiles: FileRejection[]
  ) => void
  multiple: boolean
  acceptedExtensions: string[]
  maxSizeBytes: number
}

const StyledDropzoneSection = styled("section", {
  ":focus": {
    outline: "none",
    boxShadow: `0 0 0 1px ${colors.primary}`,
  },
  padding: variables.spacer,
  paddingRight: spacing.xxxl,
  backgroundColor: colors.grayLightest,
  borderRadius: variables.borderRadius,
  alignItems: "center",
  display: "flex",
})

const FileDropzone = ({
  onDrop,
  multiple,
  acceptedExtensions,
  maxSizeBytes,
  disabled,
}: Props): React.ReactElement => (
  <Dropzone
    onDrop={onDrop}
    multiple={multiple}
    accept={
      acceptedExtensions.length
        ? acceptedExtensions.map((value: string): string => `.${value}`)
        : undefined
    }
    maxSize={maxSizeBytes}
    disabled={disabled}
  >
    {({ getRootProps, getInputProps }) => (
      <StyledDropzoneSection
        {...getRootProps()}
        className={`fileUploadDropzone ${disabled ? "disabled" : ""}`}
      >
        <input {...getInputProps()} />
        <FileDropzoneInstructions
          multiple={multiple}
          acceptedExtensions={acceptedExtensions}
          maxSizeBytes={maxSizeBytes}
        />
        <Button kind={Kind.PRIMARY} disabled={disabled}>
          {"Browse files"}
        </Button>
      </StyledDropzoneSection>
    )}
  </Dropzone>
)

export default FileDropzone
