/**
 * @license
 * Copyright 2018-2019 Streamlit Inc.
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

import React from 'react'
import moment from 'moment'
import { Datepicker as UIDatePicker } from 'baseui/datepicker'
import { Map as ImmutableMap } from 'immutable'
import { WidgetStateManager } from 'lib/WidgetStateManager'
import { datePickerOverrides } from 'lib/widgetTheme'

interface Props {
  disabled: boolean;
  element: ImmutableMap<string, any>;
  widgetMgr: WidgetStateManager;
  width: number;
}

interface State {
  /**
   * The value specified by the user via the UI. If the user didn't touch this
   * widget's UI, the default value is used.
   */
  value: string;
}

class DateInput extends React.PureComponent<Props, State> {
  public state: State = {
    value: this.props.element.get('default'),
  }

  public componentDidUpdate = (prevProps: Props): void => {
    // Reset the widget state when the default value changes
    const oldDefaultValue: string = prevProps.element.get('default')
    const newDefaultValue: string = this.props.element.get('default')
    if (oldDefaultValue !== newDefaultValue) {
      this.setState({ value: newDefaultValue }, this.setWidgetValue)
    }
  }

  private setWidgetValue = (): void => {
    const widgetId: string = this.props.element.get('id')
    this.props.widgetMgr.setStringValue(widgetId, this.state.value)
  }

  private handleChange = ({ date }: { date: Date | Date[] }): void => {
    const value = dateToString(date as Date)
    this.setState({ value }, this.setWidgetValue)
  }

  public render = (): React.ReactNode => {
    const style = { width: this.props.width }
    const label = this.props.element.get('label')

    return (
      <div className="Widget stDateInput" style={style}>
        <label>{label}</label>
        <UIDatePicker
          formatString="yyyy/MM/dd"
          value={stringToDate(this.state.value)}
          onChange={this.handleChange}
          disabled={this.props.disabled}
          overrides={datePickerOverrides}
        />
      </div>
    )
  }
}

function dateToString(date: Date): string {
  return moment(date).format('YYYY/MM/DD')
}

function stringToDate(value: string): Date {
  return moment(value, 'YYYY/MM/DD').toDate()
}

export default DateInput
