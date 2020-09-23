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

import React, { ReactElement, memo, forwardRef, MouseEvent } from "react"
import classNames from "classnames"
import { StatefulPopover, PLACEMENT } from "baseui/popover"
import { StatefulMenu } from "baseui/menu"
import Button, { Kind } from "components/shared/Button"

import Icon from "components/shared/Icon"
import {
  IMenuItem,
  IGuestToHostMessage,
} from "hocs/withS4ACommunication/types"

import "./MainMenu.scss"

const ONLINE_DOCS_URL = "https://docs.streamlit.io"
const COMMUNITY_URL = "https://discuss.streamlit.io"
const TEAMS_URL = "https://streamlit.io/forteams"
const BUG_URL = "https://github.com/streamlit/streamlit/issues/new/choose"

const SCREENCAST_LABEL: { [s: string]: string } = {
  COUNTDOWN: "Cancel screencast",
  RECORDING: "Stop recording",
}

export interface Props {
  /** True if report sharing is properly configured and enabled. */
  sharingEnabled: boolean

  /** True if we're connected to the Streamlit server. */
  isServerConnected: boolean

  /** Rerun the report. */
  quickRerunCallback: () => void

  /** Clear the cache. */
  clearCacheCallback: () => void

  /** Show the screen recording dialog. */
  screencastCallback: () => void

  /** Share the report to S3. */
  shareCallback: () => void

  /** Show the Settings dialog. */
  settingsCallback: () => void

  /** Show the About dialog. */
  aboutCallback: () => void

  screenCastState: string

  s4aMenuItems: IMenuItem[]

  sendS4AMessage: (message: IGuestToHostMessage) => void
}

const getOpenInWindowCallback = (url: string) => (): void => {
  window.open(url, "_blank")
}

export interface MenuListItemProps {
  item: any
  "aria-selected": boolean
  onClick: (e: MouseEvent<HTMLLIElement>) => void
  onMouseEnter: (e: MouseEvent<HTMLLIElement>) => void
  $disabled: boolean
  $isHighlighted: boolean
}

const MenuListItem = forwardRef<HTMLLIElement, MenuListItemProps>(
  (
    {
      item,
      "aria-selected": ariaSelected,
      onClick,
      onMouseEnter,
      $disabled,
      $isHighlighted,
    },
    ref
  ) => {
    const { label, shortcut, hasDividerAbove } = item
    const className = classNames({
      "menu-item": true,
      "menu-item-highlighted": $isHighlighted,
      "menu-item-disabled": $disabled,
      "menu-item-stop-recording": Boolean(item.stopRecordingIndicator),
    })
    const interactiveProps = $disabled
      ? {}
      : {
          onClick,
          onMouseEnter,
        }

    return (
      <>
        {hasDividerAbove && <div className="menu-divider" />}
        <li
          ref={ref}
          role="option"
          className={className}
          aria-selected={ariaSelected}
          aria-disabled={$disabled}
          {...interactiveProps}
        >
          {label}
          {shortcut && <span className="shortcut">{shortcut}</span>}
        </li>
      </>
    )
  }
)

function MainMenu(props: Props): ReactElement {
  const isServerDisconnected = !props.isServerConnected

  const S4AMenuOptions = props.s4aMenuItems.map(item => {
    if (item.type === "separator") {
      return null
    }

    return {
      onClick: () =>
        props.sendS4AMessage({
          type: "MENU_ITEM_CALLBACK",
          key: item.key,
        }),
      label: item.label,
    }
  })

  const shouldShowS4AMenu = !!S4AMenuOptions.length

  const coreMenuOptions = {
    rerun: {
      disabled: isServerDisconnected,
      onClick: props.quickRerunCallback,
      label: "Rerun",
      shortcut: "r",
    },
    clearCache: {
      disabled: isServerDisconnected,
      onClick: props.clearCacheCallback,
      label: "Clear cache",
      shortcut: "c",
    },
    recordScreencast: {
      onClick: props.screencastCallback,
      label: SCREENCAST_LABEL[props.screenCastState] || "Record a screencast",
      shortcut: SCREENCAST_LABEL[props.screenCastState] ? "esc" : "",
      stopRecordingIndicator: Boolean(SCREENCAST_LABEL[props.screenCastState]),
    },
    saveSnapshot: {
      disabled: isServerDisconnected,
      onClick: props.shareCallback,
      label: "Save a snapshot",
    },
    documentation: {
      onClick: getOpenInWindowCallback(ONLINE_DOCS_URL),
      label: "Documentation",
    },
    community: {
      onClick: getOpenInWindowCallback(COMMUNITY_URL),
      label: "Ask a question",
    },
    report: {
      onClick: getOpenInWindowCallback(BUG_URL),
      label: "Report a bug",
    },
    s4t: {
      onClick: getOpenInWindowCallback(TEAMS_URL),
      label: "Streamlit for Teams",
    },
    settings: { onClick: props.settingsCallback, label: "Settings" },
    about: { onClick: props.aboutCallback, label: "About" },
  }

  let menuOptions: any[] = [coreMenuOptions.rerun, coreMenuOptions.clearCache]

  if (shouldShowS4AMenu) {
    menuOptions = [
      ...menuOptions,
      coreMenuOptions.settings,
      { ...coreMenuOptions.recordScreencast, hasDividerAbove: true },
      ...S4AMenuOptions,
    ]
  } else {
    menuOptions = [
      ...menuOptions,
      { ...coreMenuOptions.recordScreencast, hasDividerAbove: true },
      { ...coreMenuOptions.documentation, hasDividerAbove: true },
      coreMenuOptions.community,
      coreMenuOptions.report,
      { ...coreMenuOptions.s4t, hasDividerAbove: true },
      coreMenuOptions.settings,
      coreMenuOptions.about,
    ]
  }

  return (
    <StatefulPopover
      focusLock
      placement={PLACEMENT.bottomRight}
      content={({ close }) => (
        <StatefulMenu
          items={menuOptions}
          onItemSelect={({ item }) => {
            item.onClick()
            close()
          }}
          overrides={{
            Option: MenuListItem,
            List: {
              style: {
                ":focus": {
                  outline: "none",
                },
              },
            },
          }}
        />
      )}
    >
      <span id="MainMenu">
        <Button kind={Kind.ICON}>
          <Icon type="menu" />
        </Button>
        {props.screenCastState === "RECORDING" && (
          <span className="recording-indicator" />
        )}
      </span>
    </StatefulPopover>
  )
}

export default memo(MainMenu)
