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

import React, { ComponentType, ReactElement } from "react"
import styled from "@emotion/styled"
import Icon from "components/shared/Icon"
import { SortDirection } from "./SortDirection"

export interface DataFrameCellProps {
  /** The cell's column index in the DataFrame */
  columnIndex: number

  /** The cell's row index in the DataFrame */
  rowIndex: number

  /** The cell's component to render */
  as: ComponentType

  /** Additional css styling for the cell */
  style: Record<string, unknown>

  /**
   * The HTML contents of the cell. Added to the DOM as a child of this
   * DataFrameCel.
   */
  contents: string

  /**
   * If true, then the table's sorting was manually set by the user, by
   * clicking on a column header. We only show the sort arrow when this is
   * true.
   */
  sortedByUser: boolean

  /**
   * The {@link SortDirection} for this column, or undefined if the column is
   * unsorted. No sorting is done here - this property is used to determine
   * which, if any, sort icon to draw in column-header cells.
   */
  columnSortDirection?: SortDirection

  /**
   * An optional callback that will be called when a column header is clicked.
   * (The property is ignored for non-header cells). The callback will be passed this
   * cell's columnIndex.
   *
   * {@link DataFrame} uses this to toggle column sorting.
   */
  headerClickedCallback?: (columnIndex: number) => void
}

const SortArrowIcon = styled(Icon)(({ theme }) => ({
  fontSize: theme.fontSizes.xs,
  marginRight: theme.spacing.twoXS,
  opacity: 0.3,
  verticalAlign: "top",
}))

export default function DataFrameCell({
  as,
  columnIndex,
  contents,
  rowIndex,
  sortedByUser,
  style,
  columnSortDirection,
  headerClickedCallback,
}: DataFrameCellProps): ReactElement {
  let onClick
  let role
  let tabIndex
  let title = contents

  const isDescending = columnSortDirection === SortDirection.DESCENDING

  if (headerClickedCallback != null && rowIndex === 0) {
    onClick = () => headerClickedCallback(columnIndex)
    role = "button"
    tabIndex = 0
    title =
      columnSortDirection == null
        ? `Sort by column "${contents}"`
        : `Sorted by column "${contents}" (${
            isDescending ? "descending" : "ascending"
          })`
  }

  // The sort icon is only drawn in the top row
  const sortIcon =
    rowIndex === 0 ? drawSortIcon(columnSortDirection) : undefined
  const Component = as

  return (
    // (ESLint erroneously believes we're not assigning a role to our clickable div)
    // eslint-disable-next-line

    <Component
      // @ts-ignore
      style={style}
      onClick={onClick}
      role={role}
      tabIndex={tabIndex}
      title={title}
    >
      {sortedByUser ? sortIcon : ""}
      {contents}
    </Component>
  )
}

function drawSortIcon(sortDirection?: SortDirection): React.ReactNode {
  // If these icons are changed, you may also need to update DataFrame.SORT_ICON_WIDTH
  // to ensure proper column width padding
  switch (sortDirection) {
    case SortDirection.ASCENDING:
      return <SortArrowIcon type="chevron-top" />

    case SortDirection.DESCENDING:
      return <SortArrowIcon type="chevron-bottom" />

    case undefined:
    default:
      return null
  }
}
