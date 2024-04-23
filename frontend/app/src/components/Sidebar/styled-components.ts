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

import styled from "@emotion/styled"
import { keyframes } from "@emotion/react"
import {
  getWrappedHeadersStyle,
  hasLightBackgroundColor,
} from "@streamlit/lib/src/theme/utils"
export interface StyledSidebarProps {
  isCollapsed: boolean
  adjustTop: boolean
  sidebarWidth: string
}

export const StyledSidebar = styled.section<StyledSidebarProps>(
  ({ theme, isCollapsed, adjustTop, sidebarWidth }) => {
    const minWidth = isCollapsed ? 0 : Math.min(244, window.innerWidth)
    const maxWidth = isCollapsed ? 0 : Math.min(550, window.innerWidth * 0.9)

    return {
      // Nudge the sidebar by 2px so the header decoration doesn't go below it
      position: "relative",
      top: adjustTop ? "2px" : "0px",
      backgroundColor: theme.colors.bgColor,
      zIndex: theme.zIndices.header + 1,

      minWidth,
      maxWidth,
      transform: isCollapsed ? `translateX(-${sidebarWidth}px)` : "none",
      transition: "transform 300ms, min-width 300ms, max-width 300ms",

      "&:focus": {
        outline: "none",
      },

      [`@media (max-width: ${theme.breakpoints.md})`]: {
        boxShadow: `-2rem 0 2rem 2rem ${
          isCollapsed ? "transparent" : "#00000029"
        }`,
      },

      [`@media print`]: {
        display: isCollapsed ? "none" : "initial",
        // set to auto, otherwise the sidebar does not take up the whole page
        height: "auto !important",
        // set maxHeight to little bit less than 100%, otherwise the sidebar might start a mostly blank page
        maxHeight: "99%",
        // on Chrome, sth. adds a box-shadow in printing mode which looks weird
        boxShadow: "none",
      },
    }
  }
)

export const StyledSidebarNavContainer = styled.div(() => ({
  position: "relative",
}))

export interface StyledSidebarNavItemsProps {
  isExpanded: boolean
  isOverflowing: boolean
  hasSidebarElements: boolean
}

export const StyledSidebarNavItems = styled.ul<StyledSidebarNavItemsProps>(
  ({ isExpanded, isOverflowing, hasSidebarElements, theme }) => {
    const isExpandedMaxHeight = isExpanded ? "75vh" : "33vh"
    const maxHeight = hasSidebarElements ? isExpandedMaxHeight : "100vh"

    return {
      maxHeight,
      listStyle: "none",
      overflow: ["auto", "overlay"],
      margin: 0,
      paddingTop: theme.spacing.lg,
      paddingBottom: theme.spacing.lg,

      "@media print": {
        paddingTop: theme.spacing.threeXL,
      },

      "&::before": isOverflowing
        ? {
            content: '" "',
            backgroundImage: `linear-gradient(0deg, transparent, ${theme.colors.bgColor})`,
            width: "100%",
            height: "2rem",
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            pointerEvents: "none",
          }
        : null,

      "&::after": isOverflowing
        ? {
            content: '" "',
            backgroundImage: `linear-gradient(0deg, ${theme.colors.bgColor}, transparent)`,
            height: "2rem",
            position: "absolute",
            bottom: 0,
            left: 0,
            right: 0,
            pointerEvents: "none",
          }
        : null,
    }
  }
)

export interface StyledSidebarNavSeparatorContainerProps {
  isExpanded: boolean
  isOverflowing: boolean
}

const bounceAnimation = keyframes`
  from, to {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-0.25rem);
  }
`

export const StyledSidebarNavSeparatorContainer =
  styled.div<StyledSidebarNavSeparatorContainerProps>(
    ({ isExpanded, isOverflowing, theme }) => ({
      cursor: isExpanded || isOverflowing ? "pointer" : "default",
      position: "absolute",
      height: theme.spacing.lg,
      left: 0,
      right: 0,
      bottom: 0,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: theme.colors.fadedText60,
      borderBottom: `1px solid ${theme.colors.fadedText10}`,
      transition: "color 500ms",

      ...((isExpanded || isOverflowing) && {
        "&:hover": {
          color: theme.colors.bodyText,
          background: `linear-gradient(0deg, ${theme.colors.darkenedBgMix15}, transparent)`,

          "& > *": {
            animation: `${bounceAnimation} 0.5s ease infinite`,
          },
        },
      }),
    })
  )

export const StyledSidebarNavLinkContainer = styled.div(() => ({
  display: "flex",
  flexDirection: "column",
}))

export interface StyledSidebarNavLinkProps {
  isActive: boolean
}

export const StyledSidebarNavLink = styled.a<StyledSidebarNavLinkProps>(
  ({ isActive, theme }) => {
    const defaultPageLinkStyles = {
      textDecoration: "none",
      fontWeight: isActive ? 600 : 400,
    }

    return {
      ...defaultPageLinkStyles,
      display: "flex",
      flexDirection: "row",
      alignItems: "center",
      gap: theme.spacing.sm,
      borderRadius: theme.spacing.twoXS,

      paddingLeft: theme.spacing.sm,
      paddingRight: theme.spacing.sm,
      marginLeft: theme.spacing.lg,
      marginRight: theme.spacing.lg,
      marginTop: theme.spacing.threeXS,
      marginBottom: theme.spacing.threeXS,
      lineHeight: theme.lineHeights.menuItem,

      backgroundColor: isActive ? theme.colors.darkenedBgMix15 : "transparent",

      "&:hover": {
        backgroundColor: isActive
          ? theme.colors.darkenedBgMix25
          : theme.colors.darkenedBgMix15,
      },

      "&:active,&:visited,&:hover": {
        ...defaultPageLinkStyles,
      },

      "&:focus": {
        outline: "none",
      },

      "&:focus-visible": {
        backgroundColor: theme.colors.darkenedBgMix15,
      },

      [`@media print`]: {
        paddingLeft: theme.spacing.none,
      },
    }
  }
)

export const StyledSidebarLinkText = styled.span<StyledSidebarNavLinkProps>(
  ({ isActive, theme }) => ({
    color: isActive ? theme.colors.bodyText : theme.colors.fadedText60,
    overflow: "hidden",
    whiteSpace: "nowrap",
    textOverflow: "ellipsis",
    display: "table-cell",
  })
)

export const StyledSidebarUserContent = styled.div(({ theme }) => ({
  paddingTop: theme.spacing.lg,
  paddingBottom: theme.sizes.sidebarTopSpace,
  paddingLeft: theme.spacing.twoXL,
  paddingRight: theme.spacing.twoXL,

  ...getWrappedHeadersStyle(theme),
}))

export interface StyledSidebarContentProps {
  hideScrollbar: boolean
}

export const StyledSidebarContent = styled.div<StyledSidebarContentProps>(
  ({ hideScrollbar }) => ({
    position: "relative",
    height: "100%",
    width: "100%",
    overflow: hideScrollbar ? "hidden" : ["auto", "overlay"],
  })
)

export const StyledResizeHandle = styled.div(({ theme }) => ({
  position: "absolute",
  width: "8px",
  height: "100%",
  cursor: "col-resize",
  zIndex: theme.zIndices.sidebarMobile,

  "&:hover": {
    backgroundImage: `linear-gradient(to right, transparent 20%, ${theme.colors.fadedText20} 28%, transparent 36%)`,
  },
}))

export const StyledSidebarHeaderContainer = styled.div(({ theme }) => ({
  display: "flex",
  justifyContent: "space-between",
  alignItems: "start",
  padding: `${theme.spacing.xl} ${theme.spacing.twoXL} ${theme.spacing.twoXL} ${theme.spacing.twoXL}`,
}))

export const StyledLogoLink = styled.a(({}) => ({
  maxWidth: "15rem",
  "&:hover": {
    opacity: "0.7",
  },
}))

export const StyledLogo = styled.img(({ theme }) => ({
  height: "1.5rem",
  maxWidth: "15rem",
  margin: "0.25rem 0 0.25rem 0",
  zIndex: theme.zIndices.header,
}))

export const StyledNoLogoSpacer = styled.div(({}) => ({
  height: "2.0rem",
  marginRight: "-1rem",
}))

export interface StyledSidebarOpenContainerProps {
  chevronDownshift: number
  isCollapsed: boolean
}

export const StyledSidebarOpenContainer =
  styled.div<StyledSidebarOpenContainerProps>(
    ({ theme, chevronDownshift, isCollapsed }) => ({
      position: "fixed",
      top: chevronDownshift ? `${chevronDownshift}px` : theme.spacing.xl,
      left: isCollapsed ? theme.spacing.twoXL : `-${theme.spacing.twoXL}`,
      zIndex: theme.zIndices.header,
      display: "flex",
      justifyContent: "center",
      alignItems: "start",

      transition: "left 300ms",
      transitionDelay: "left 300ms",

      [`@media print`]: {
        position: "static",
      },
    })
  )

export const StyledOpenSidebarButton = styled.div(({ theme }) => {
  const isLightTheme = hasLightBackgroundColor(theme)

  return {
    zIndex: theme.zIndices.header,
    marginLeft: theme.spacing.sm,
    color: isLightTheme ? theme.colors.gray70 : theme.colors.bodyText,

    button: {
      "&:hover": {
        backgroundColor: theme.colors.darkenedBgMix25,
      },
    },

    [`@media print`]: {
      display: "none",
    },
  }
})

export const StyledCollapseSidebarButton = styled.div(({ theme }) => {
  const isLightTheme = hasLightBackgroundColor(theme)

  return {
    display: "auto",
    transition: "left 300ms",
    transitionDelay: "left 300ms",
    color: isLightTheme ? theme.colors.gray70 : theme.colors.bodyText,
    lineHeight: "0",

    button: {
      padding: "0.25rem",
      "&:hover": {
        backgroundColor: theme.colors.darkenedBgMix25,
      },
    },

    [`@media print`]: {
      display: "none",
    },
  }
})
