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

import React, {
  ChangeEvent,
  PureComponent,
  ReactElement,
  ReactNode,
} from "react"
import { ThemeConfig } from "theme"
import Button, { Kind } from "components/shared/Button"
import Modal, { ModalHeader, ModalBody } from "components/shared/Modal"
import PageLayoutContext from "components/core/PageLayoutContext"
import UISelectbox from "components/shared/Dropdown"
import {
  StyledHeader,
  StyledHr,
  StyledLabel,
  StyledSmall,
  StyledThemeCreatorButtonWrapper,
} from "./styled-components"
import { UserSettings } from "./UserSettings"

export interface Props {
  isServerConnected: boolean
  onClose: () => void
  onSave: (settings: UserSettings) => void
  settings: UserSettings
  allowRunOnSave: boolean
  developerMode: boolean
  openThemeCreator: () => void
  animateModal: boolean
}

/**
 * Implements a dialog that is used to configure user settings.
 */
export class SettingsDialog extends PureComponent<Props, UserSettings> {
  private activeSettings: UserSettings

  static contextType = PageLayoutContext

  constructor(props: Props) {
    super(props)
    // Holds the settings that will be saved when the "save" button is clicked.
    this.state = { ...this.props.settings }

    // Holds the actual settings that Streamlit is using.
    this.activeSettings = { ...this.props.settings }
  }

  private renderThemeCreatorButton = (): ReactElement | null =>
    this.props.developerMode ? (
      <StyledThemeCreatorButtonWrapper>
        <Button onClick={this.props.openThemeCreator} kind={Kind.PRIMARY}>
          Edit active theme
        </Button>
      </StyledThemeCreatorButtonWrapper>
    ) : null

  public render = (): ReactNode => {
    const themeIndex = this.context.availableThemes.findIndex(
      (theme: ThemeConfig) => theme.name === this.context.activeTheme.name
    )

    return (
      <Modal
        animate={this.props.animateModal}
        isOpen
        onClose={this.handleCancelButtonClick}
      >
        <ModalHeader>Settings</ModalHeader>
        <ModalBody>
          {this.props.allowRunOnSave ? (
            <>
              <StyledHeader>Development</StyledHeader>
              <label>
                <input
                  disabled={!this.props.isServerConnected}
                  type="checkbox"
                  name="runOnSave"
                  checked={
                    this.state.runOnSave && this.props.isServerConnected
                  }
                  onChange={this.handleCheckboxChange}
                />{" "}
                Run on save
              </label>
              <br />
              <StyledSmall>
                Automatically updates the app when the underlying code is
                updated
              </StyledSmall>
            </>
          ) : null}
          <StyledHr />
          <StyledHeader>Appearance</StyledHeader>
          <label>
            <input
              type="checkbox"
              name="wideMode"
              checked={this.state.wideMode}
              onChange={this.handleCheckboxChange}
            />{" "}
            Wide mode
          </label>
          <div>
            <StyledSmall>
              Turn on to make this app occupy the entire width of the screen
            </StyledSmall>
          </div>
          {this.context.availableThemes.length > 1 ? (
            <>
              <StyledLabel>Theme</StyledLabel>
              <StyledSmall>Choose app and font colors/styles</StyledSmall>
              <UISelectbox
                options={this.context.availableThemes.map(
                  (theme: ThemeConfig) => theme.name
                )}
                disabled={false}
                onChange={this.handleThemeChange}
                value={themeIndex}
              />
              {this.renderThemeCreatorButton()}
            </>
          ) : null}
        </ModalBody>
      </Modal>
    )
  }

  public componentDidMount(): void {
    this.setState({ ...this.activeSettings })
  }

  private changeSingleSetting = (name: string, value: boolean): void => {
    // TypeScript doesn't currently have a good solution for setState with
    // a dynamic key name:
    // https://github.com/DefinitelyTyped/DefinitelyTyped/issues/26635
    this.setState(state => ({ ...state, [name]: value }), this.saveSettings)
  }

  private handleCheckboxChange = (e: ChangeEvent<HTMLInputElement>): void => {
    this.changeSingleSetting(e.target.name, e.target.checked)
  }

  private handleThemeChange = (index: number): void => {
    this.context.setTheme(this.context.availableThemes[index])
  }

  private handleCancelButtonClick = (): void => {
    // Discard settings from this.state by not saving them in this.settings.
    // this.settings = {...this.state};
    this.props.onClose()
  }

  private saveSettings = (): void => {
    this.activeSettings = { ...this.state }
    this.props.onSave(this.activeSettings)
  }
}
