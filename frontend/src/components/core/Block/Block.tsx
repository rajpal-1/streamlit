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

import React, { PureComponent, ReactNode, Suspense } from 'react'
import { Progress } from 'reactstrap'
import { AutoSizer } from 'react-virtualized'
import { List, Map as ImmutableMap } from 'immutable'
import { dispatchOneOf } from 'lib/immutableProto'
import { ReportRunState } from 'lib/ReportRunState'
import { WidgetStateManager } from 'lib/WidgetStateManager'
import { makeElementWithInfoText } from 'lib/utils'

// Load (non-lazy) elements.
import Chart from 'components/elements/Chart/'
import DocString from 'components/elements/DocString/'
import ErrorBoundary from 'components/shared/ErrorBoundary/'
import ExceptionElement from 'components/elements/ExceptionElement/'
import Table from 'components/elements/Table/'
import Text from 'components/elements/Text/'

// Lazy-load elements.
const Audio = React.lazy(() => import('components/elements/Audio/'))
const Balloons = React.lazy(() => import('components/elements/Balloons/'))
const BokehChart = React.lazy(() => import('components/elements/BokehChart/'))
const DataFrame = React.lazy(() => import('components/elements/DataFrame/'))
const DeckGlChart = React.lazy(() => import('components/elements/DeckGlChart/'))
const ImageList = React.lazy(() => import('components/elements/ImageList/'))
const GraphVizChart = React.lazy(() => import('components/elements/GraphVizChart/'))
const PlotlyChart = React.lazy(() => import('components/elements/PlotlyChart/'))
const VegaLiteChart = React.lazy(() => import('components/elements/VegaLiteChart/'))
const Video = React.lazy(() => import('components/elements/Video/'))

// Lazy-load widgets.
const Button = React.lazy(() => import('components/widgets/Button/'))
const Checkbox = React.lazy(() => import('components/widgets/Checkbox/'))
const DateInput = React.lazy(() => import('components/widgets/DateInput/'))
const Radio = React.lazy(() => import('components/widgets/Radio/'))
const Selectbox = React.lazy(() => import('components/widgets/Selectbox/'))
const Slider = React.lazy(() => import('components/widgets/Slider/'))
const TextArea = React.lazy(() => import('components/widgets/TextArea/'))
const TextInput = React.lazy(() => import('components/widgets/TextInput/'))
const TimeInput = React.lazy(() => import('components/widgets/TimeInput/'))

type SimpleElement = ImmutableMap<string, any>
type Element = SimpleElement | BlockElement
interface BlockElement extends List<Element> { }

interface Props {
  elements: BlockElement;
  reportId: string;
  reportRunState: ReportRunState;
  showStaleElementIndicator: boolean;
  widgetMgr: WidgetStateManager;
  widgetsDisabled: boolean;
}

class Block extends PureComponent<Props> {
  private renderElements = (width: number): ReactNode[] => {
    const elementsToRender = this.handleEmptyElements()

    // Transform Streamlit elements into ReactNodes.
    const nodes: ReactNode[] = []
    elementsToRender.forEach((element, index) => {
      if (element instanceof List) {
        nodes.push(
          <div key={index} className="stBlock" style={{ width }}>
            <Block
              elements={element as BlockElement}
              reportId={this.props.reportId}
              reportRunState={this.props.reportRunState}
              showStaleElementIndicator={this.props.showStaleElementIndicator}
              widgetMgr={this.props.widgetMgr}
              widgetsDisabled={this.props.widgetsDisabled}
            />
          </div>
        )
      } else {
        const component = this.renderElement(element as SimpleElement, index, width)
        if (!component) {
          // Do not transform an empty element into a ReactNode.
          return
        }

        const showStaleState = this.props.showStaleElementIndicator && this.isStaleElement(element as SimpleElement)
        const className = showStaleState ? 'element-container stale-element' : 'element-container'

        nodes.push(
          <div key={index} className={className} style={{ width }}>
            <ErrorBoundary width={width}>
              <Suspense fallback={
                <Text
                  element={makeElementWithInfoText('Loading...').get('text')}
                  width={width}
                />
              }>
                {component}
              </Suspense>
            </ErrorBoundary>
          </div>
        )
      }
    })
    return nodes
  }

  private handleEmptyElements = (): BlockElement => {
    let elementsToRender = this.props.elements
    if (this.props.reportRunState === ReportRunState.RUNNING) {
      // (BUG #739) When the report is running, use our most recent list
      // of rendered elements as placeholders for any empty elements we encounter.
      elementsToRender = this.props.elements.map((element: Element, index: number): Element => {
        if (element instanceof ImmutableMap) {
          // Repeat the old element if we encounter st.empty()
          const isEmpty = (element as SimpleElement).get('type') === 'empty'
          return isEmpty ? elementsToRender.get(index, element) : element
        }
        return element
      })
    }
    return elementsToRender
  }

  private isStaleElement(element: SimpleElement): boolean {
    if (this.props.reportRunState === ReportRunState.RERUN_REQUESTED) {
      // If a rerun was just requested, all of our current elements
      // are about to become stale.
      return true
    } else if (this.props.reportRunState === ReportRunState.RUNNING) {
      return element.get('reportId') !== this.props.reportId
    } else {
      return false
    }
  }

  private renderElement = (element: SimpleElement, index: number, width: number): ReactNode | undefined => {
    if (!element) {
      throw new Error('Transmission error.')
    }

    const widgetProps = {
      widgetMgr: this.props.widgetMgr,
      disabled: this.props.widgetsDisabled,
    }

    return dispatchOneOf(element, 'type', {
      // Elements
      audio: (el: SimpleElement) => <Audio element={el} width={width} />,
      balloons: (el: SimpleElement) => <Balloons element={el} width={width} />,
      bokehChart: (el: SimpleElement) => <BokehChart element={el} index={index} width={width} />,
      chart: (el: SimpleElement) => <Chart element={el} width={width} />,
      dataFrame: (el: SimpleElement) => <DataFrame element={el} width={width} />,
      deckGlChart: (el: SimpleElement) => <DeckGlChart element={el} width={width} />,
      docString: (el: SimpleElement) => <DocString element={el} width={width} />,
      empty: () => undefined,
      exception: (el: SimpleElement) => <ExceptionElement element={el} width={width} />,
      graphvizChart: (el: SimpleElement) => <GraphVizChart element={el} index={index} width={width} />,
      imgs: (el: SimpleElement) => <ImageList element={el} width={width} />,
      plotlyChart: (el: SimpleElement) => <PlotlyChart element={el} width={width} />,
      progress: (el: SimpleElement) => <Progress value={el.get('value')} className="stProgress" style={{ width }} />,
      table: (el: SimpleElement) => <Table element={el} width={width} />,
      text: (el: SimpleElement) => <Text element={el} width={width} />,
      vegaLiteChart: (el: SimpleElement) => <VegaLiteChart element={el} width={width} />,
      video: (el: SimpleElement) => <Video element={el} width={width} />,
      // Widgets
      button: (el: SimpleElement) => <Button element={el} width={width} {...widgetProps} />,
      checkbox: (el: SimpleElement) => <Checkbox element={el} width={width} {...widgetProps} />,
      dateInput: (el: SimpleElement) => <DateInput element={el} width={width} {...widgetProps} />,
      textInput: (el: SimpleElement) => <TextInput element={el} width={width} {...widgetProps} />,
      radio: (el: SimpleElement) => <Radio element={el} width={width} {...widgetProps} />,
      selectbox: (el: SimpleElement) => <Selectbox element={el} width={width} {...widgetProps} />,
      slider: (el: SimpleElement) => <Slider element={el} width={width} {...widgetProps} />,
      textArea: (el: SimpleElement) => <TextArea element={el} width={width} {...widgetProps} />,
      timeInput: (el: SimpleElement) => <TimeInput element={el} width={width} {...widgetProps} />,
    })
  }

  public render = () => (
    <AutoSizer disableHeight={true}>
      {({ width }) => this.renderElements(width)}
    </AutoSizer>
  )
}

export default Block
