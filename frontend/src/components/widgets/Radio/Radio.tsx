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

import { Radio as RadioProto } from "autogen/proto"
import { Radio as UIRadio, RadioGroup } from "baseui/radio"
import { Source, WidgetStateManager } from "lib/WidgetStateManager"
import { radioOverrides } from "lib/widgetTheme"
import React from "react"

export interface Props {
  disabled: boolean
  element: RadioProto
  widgetMgr: WidgetStateManager
  width: number
}

interface State {
  /**
   * The value specified by the user via the UI. If the user didn't touch this
   * widget's UI, the default value is used.
   */
  value: number
}

class Radio extends React.PureComponent<Props, State> {
  public state: State = {
    value: this.initialValue,
  }

  get initialValue(): number {
    // If WidgetStateManager knew a value for this widget, initialize to that.
    // Otherwise, use the default value from the widget protobuf.
    const widgetId = this.props.element.id
    const storedValue = this.props.widgetMgr.getIntValue(widgetId)
    return storedValue !== undefined ? storedValue : this.props.element.default
  }

  public componentDidMount(): void {
    this.setWidgetValue({ fromUi: false })
  }

  private setWidgetValue = (source: Source): void => {
    const widgetId = this.props.element.id
    this.props.widgetMgr.setIntValue(widgetId, this.state.value, source)
  }

  private onChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const value = parseInt(e.target.value, 10)
    this.setState({ value }, () => this.setWidgetValue({ fromUi: true }))
  }

  public render = (): React.ReactNode => {
    const style = { width: this.props.width }
    let { options } = this.props.element
    let { disabled } = this.props

    if (options.length === 0) {
      options = ["No options to select."]
      disabled = true
    }

    return (
      <div className="Widget row-widget stRadio" style={style}>
        <label>{this.props.element.label}</label>
        <RadioGroup
          onChange={this.onChange}
          value={this.state.value.toString()}
          disabled={disabled}
        >
          {options.map((option: string, index: number) => (
            <UIRadio
              key={index}
              value={index.toString()}
              overrides={radioOverrides}
            >
              {option}
            </UIRadio>
          ))}
        </RadioGroup>
      </div>
    )
  }
}

export default Radio
