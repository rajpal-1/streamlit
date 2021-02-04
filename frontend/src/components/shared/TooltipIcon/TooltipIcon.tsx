import React, { ReactElement } from "react"
import Tooltip, { Placement } from "components/shared/Tooltip"
import { Info as InfoIcon } from "react-feather"
import StreamlitMarkdown from "components/shared/StreamlitMarkdown"
import { useTheme } from "emotion-theming"
import { Theme } from "theme"
import {
  StyledTooltipIconWrapper,
  StyledTooltipContentWrapper,
} from "./styled-components"

export interface TooltipIconProps {
  placement?: Placement
  iconSize?: string
  content: string
}

function TooltipIcon({
  placement = Placement.AUTO,
  iconSize = "16",
  content,
}: TooltipIconProps): ReactElement {
  const theme: Theme = useTheme()
  return (
    <StyledTooltipIconWrapper className="stTooltipIcon">
      <Tooltip
        content={
          <StyledTooltipContentWrapper>
            <StreamlitMarkdown
              style={{ fontSize: theme.fontSizes.sm }}
              source={content}
              allowHTML
            />
          </StyledTooltipContentWrapper>
        }
        placement={placement}
        inline
      >
        <InfoIcon className="icon" size={iconSize} />
      </Tooltip>
    </StyledTooltipIconWrapper>
  )
}

export default TooltipIcon
