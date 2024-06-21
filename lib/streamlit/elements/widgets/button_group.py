# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2024)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, Sequence, cast

from streamlit.elements.lib.policies import (
    check_cache_replay_rules,
    check_callback_rules,
    check_fragment_path_policy,
    check_session_state_rules,
)
from streamlit.errors import StreamlitAPIException
from streamlit.proto.ButtonGroup_pb2 import ButtonGroup as ButtonGroupProto
from streamlit.runtime.metrics_util import gather_metrics
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.runtime.state import (
    register_widget,
)
from streamlit.runtime.state.common import compute_widget_id, save_for_app_testing
from streamlit.type_util import (
    Key,
    OptionSequence,
    T,
    check_python_comparable,
    ensure_indexable,
    is_type,
    to_key,
)

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator
    from streamlit.runtime.state import (
        WidgetArgs,
        WidgetCallback,
        WidgetKwargs,
    )


def _check_and_convert_to_indices(
    opt: Sequence[Any], default_values: Sequence[Any] | Any | None
) -> list[int]:
    """Perform validation checks and return indices based on the default values."""
    if default_values is None and None not in opt:
        return None

    if not isinstance(default_values, list):
        # This if is done before others because calling if not x (done
        # right below) when x is of type pd.Series() or np.array() throws a
        # ValueError exception.
        if is_type(default_values, "numpy.ndarray") or is_type(
            default_values, "pandas.core.series.Series"
        ):
            default_values = list(cast(Sequence[Any], default_values))
        elif (
            isinstance(default_values, (tuple, set))
            or default_values
            and default_values not in opt
        ):
            default_values = list(default_values)
        else:
            default_values = [default_values]
    for value in default_values:
        if value not in opt:
            raise StreamlitAPIException(
                f"The default value '{value}' is not part of the options. "
                "Please make sure that every default values also exists in the options."
            )

    return [opt.index(value) for value in default_values]


@dataclass
class ButtonGroupSerde(Generic[T]):
    options: Sequence[T]

    def serialize(self, value: list[T] | None) -> list[int]:
        return (
            _check_and_convert_to_indices(self.options, value)
            if value is not None
            else []
        )

    def deserialize(self, ui_value: list[int] | None, widget_id: str = "") -> list[T]:
        # print(f"ui value: {ui_value}")
        return [self.options[val] for val in ui_value] if ui_value is not None else []


class ButtonGroupMixin:
    @gather_metrics("button_group")
    def button_group(
        self,
        options: list[str],
        *,
        key: Key | None = None,
        default: list[bool] | None = None,
        click_mode: Literal["button", "checkbox", "radio"] = "button",
        disabled: bool = False,
        use_container_width: bool = False,
        format_func: Callable[[str], str] = lambda x: str(x),
        on_click: WidgetCallback | None = None,
        args: WidgetArgs | None = None,
        kwargs: WidgetKwargs | None = None,
    ) -> str | list[str] | None:
        default_values = (
            [index for index, default_val in enumerate(default) if default_val is True]
            if default is not None
            else []
        )
        return self._button_group(
            options,
            key=key,
            default=default_values,
            click_mode=click_mode,
            disabled=disabled,
            use_container_width=use_container_width,
            format_func=format_func,
            on_click=on_click,
            args=args,
            kwargs=kwargs,
        )

        # current_values: list[str] = (
        #     selected_indices if selected_indices is not None else default_values
        # )

        # if len(current_values) == 0:
        #     return None
        # if len(current_values) == 1:
        #     return options[current_values[0]]

        # return [options[val] for val in current_values]

    @gather_metrics("feedback")
    def feedback(
        self,
        options: Literal["thumbs", "smiles", "stars"] = "thumbs",
        *,
        key: str | None = None,
        disabled: bool = False,
        on_click: WidgetCallback | None = None,
        args: Any | None = None,
        kwargs: Any | None = None,
    ) -> float | None:
        def format_func_thumbs(option: float):
            if abs(option - 1.0) < 1e-6:
                return ":material/thumb_up:"
            if abs(option - 0.0) < 1e-6:
                return ":material/thumb_down:"
            return ""

        def format_func_smiles(option: float):
            if abs(option - 0.0) < 1e-6:
                return ":material/sentiment_sad:"
            if abs(option - 0.25) < 1e-6:
                return ":material/sentiment_dissatisfied:"
            if abs(option - 0.5) < 1e-6:
                return ":material/sentiment_neutral:"
            if abs(option - 0.75) < 1e-6:
                return ":material/sentiment_satisfied:"
            if abs(option - 1.0) < 1e-6:
                return ":material/sentiment_very_satisfied:"

            return ""

        def format_func_stars(option: float):
            return ":material/star_rate:"

        actual_options = [1.0, 0.0]
        if options in ["smiles", "stars"]:
            actual_options = [0, 0.25, 0.5, 0.75, 1]

        format_func = None
        if options == "thumbs":
            format_func = format_func_thumbs
            # thumbs_up is 1, thumbs_down is 0; but we want to show thumbs_up first,
            # so its index is 0
        elif options == "smiles":
            format_func = format_func_smiles
            # generates steps from 0 to 1 like [0, 0.25, 0.5, 0.75, 1]
        elif options == "stars":
            format_func = format_func_stars
        else:
            raise StreamlitAPIException(
                "The options argument to st.feedback must be one of "
                "['thumbs', 'smiles', 'stars']. "
                f"The argument passed was '{options}'."
            )

        def _on_click(*args, **kwargs):
            if key is None:
                on_click(*args, **kwargs)
                return

            # Problem: we don't have the widget id here, so the key has to be provided
            ctx = get_script_run_ctx()
            current_value = (
                ctx.session_state[key]
                if key is not None and key in ctx.session_state
                else None
            )
            new_kwargs = dict(kwargs, _st_value=current_value)
            on_click(*args, **new_kwargs)

        sentiment = self._button_group(
            actual_options,
            key=key,
            click_mode="radio",
            disabled=disabled,
            format_func=format_func if format_func is not None else lambda x: str(x),
            on_click=_on_click if on_click else None,
            args=args,
            kwargs=kwargs,
        )
        return sentiment[0] if len(sentiment) > 0 else None

    def _button_group(
        self,
        options: OptionSequence[T],
        *,
        key: Key | None = None,
        default: list[int] | None = None,
        click_mode: Literal["button", "checkbox", "radio"] = "button",
        disabled: bool = False,
        use_container_width: bool = False,
        format_func: Callable[[T], str] = lambda x: str(x),
        on_click: WidgetCallback | None = None,
        args: Any | None = None,
        kwargs: Any | None = None,
    ) -> list[T]:
        if default is None:
            default = []
        key = to_key(key)

        check_fragment_path_policy(self.dg)
        check_cache_replay_rules()
        check_callback_rules(self.dg, on_change=on_click)
        check_session_state_rules(default_value=default, key=key)

        widget_name = "button_group"
        ctx = get_script_run_ctx()

        # TODO: convert default to indices
        indexable_options = ensure_indexable(options)
        check_python_comparable(indexable_options)
        formatted_options = [format_func(o).encode("utf-8") for o in indexable_options]

        widget_id = compute_widget_id(
            widget_name,
            user_key=key,
            key=key,
            options=formatted_options,
            default=default,
            use_container_width=use_container_width,
            page=ctx.active_script_hash if ctx else None,
        )

        default_values = default if default is not None else []
        button_group_proto = ButtonGroupProto()
        button_group_proto.id = widget_id
        button_group_proto.options[:] = formatted_options
        button_group_proto.default[:] = default_values

        button_group_proto.disabled = disabled
        button_group_proto.click_mode = ButtonGroupProto.BUTTON
        if click_mode == "radio":
            button_group_proto.click_mode = ButtonGroupProto.RADIO
        elif click_mode == "checkbox":
            button_group_proto.click_mode = ButtonGroupProto.CHECKBOX

        button_group_proto.use_container_width = use_container_width
        serde = ButtonGroupSerde(indexable_options)
        widget_state = register_widget(
            widget_name,
            button_group_proto,
            # user_key=key,
            on_change_handler=on_click,
            args=args,
            kwargs=kwargs,
            deserializer=serde.deserialize,
            serializer=serde.serialize,
            ctx=ctx,
        )

        value = widget_state.value
        if widget_state.value_changed:
            button_group_proto.value[:] = serde.serialize(value)
            button_group_proto.set_value = True

        if ctx:
            save_for_app_testing(ctx, widget_id, format_func)

        self.dg._enqueue(widget_name, button_group_proto)
        # print(f"widget state: {widget_state}")
        return value

    @property
    def dg(self) -> DeltaGenerator:
        """Get our DeltaGenerator."""
        return cast("DeltaGenerator", self)
