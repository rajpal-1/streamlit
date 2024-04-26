/**
 * Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2024)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React, {
  ReactElement,
  useCallback,
  useRef,
  useState,
  useEffect,
} from "react"
import { AppContext } from "@streamlit/app/src/components/AppContext"
// We import react-device-detect in this way so that tests can mock its
// isMobile field sanely.
import * as reactDeviceDetect from "react-device-detect"

import {
  EmojiIcon,
  useIsOverflowing,
  StreamlitEndpoints,
  IAppPage,
} from "@streamlit/lib"

import {
  StyledSidebarNavContainer,
  StyledSidebarNavItems,
  StyledSidebarNavLink,
  StyledSidebarLinkText,
  StyledSidebarNavLinkContainer,
  StyledViewButton,
  StyledSidebarNavSeparator,
} from "./styled-components"

export interface Props {
  endpoints: StreamlitEndpoints
  appPages: IAppPage[]
  collapseSidebar: () => void
  currentPageScriptHash: string
  hasSidebarElements: boolean
  onPageChange: (pageName: string) => void
}

/** Displays a list of navigable app page links for multi-page apps. */
const SidebarNav = ({
  endpoints,
  appPages,
  collapseSidebar,
  currentPageScriptHash,
  hasSidebarElements,
  onPageChange,
}: Props): ReactElement | null => {
  const { pageLinkBaseUrl } = React.useContext(AppContext)
  const [expanded, setExpanded] = useState(hasSidebarElements ? false : true)
  const navItemsRef = useRef<HTMLUListElement>(null)
  const isOverflowing = useIsOverflowing(navItemsRef, expanded)

  if (appPages.length < 2) {
    return null
  }

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const toggleExpanded = useCallback(() => {
    if (!expanded && isOverflowing) {
      setExpanded(true)
    } else if (expanded) {
      setExpanded(false)
    }
  }, [expanded, isOverflowing])

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    if (hasSidebarElements && expanded) {
      setExpanded(false)
    }
    if (!hasSidebarElements && !expanded) {
      setExpanded(true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPageScriptHash, hasSidebarElements])

  return (
    <StyledSidebarNavContainer data-testid="stSidebarNav">
      <StyledSidebarNavItems
        ref={navItemsRef}
        isExpanded={expanded}
        hasSidebarElements={hasSidebarElements}
        data-testid="stSidebarNavItems"
      >
        {appPages.map((page: IAppPage, pageIndex: number) => {
          const pageUrl = endpoints.buildAppPageURL(
            pageLinkBaseUrl,
            page,
            pageIndex
          )

          const pageName = page.pageName as string
          const tooltipContent = pageName.replace(/_/g, " ")
          const isActive = page.pageScriptHash === currentPageScriptHash

          return (
            <li key={pageName}>
              <StyledSidebarNavLinkContainer>
                <StyledSidebarNavLink
                  data-testid="stSidebarNavLink"
                  isActive={isActive}
                  href={pageUrl}
                  onClick={e => {
                    e.preventDefault()
                    onPageChange(page.pageScriptHash as string)
                    if (reactDeviceDetect.isMobile) {
                      collapseSidebar()
                    }
                  }}
                >
                  {page.icon && page.icon.length && (
                    <EmojiIcon size="lg">{page.icon}</EmojiIcon>
                  )}
                  <StyledSidebarLinkText isActive={isActive}>
                    {tooltipContent}
                  </StyledSidebarLinkText>
                </StyledSidebarNavLink>
              </StyledSidebarNavLinkContainer>
            </li>
          )
        })}
      </StyledSidebarNavItems>

      {hasSidebarElements && (
        <>
          {isOverflowing && !expanded && (
            <StyledViewButton
              onClick={toggleExpanded}
              data-testid="stSidebarNavViewMore"
            >
              View more
            </StyledViewButton>
          )}
          {expanded && (
            <StyledViewButton
              onClick={toggleExpanded}
              data-testid="stSidebarNavViewLess"
            >
              View less
            </StyledViewButton>
          )}
          <StyledSidebarNavSeparator data-testid="stSidebarNavSeparator" />
        </>
      )}
    </StyledSidebarNavContainer>
  )
}

export default SidebarNav
