# Copyright 2018-2021 Streamlit Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import cast

import streamlit
from streamlit.errors import StreamlitAPIException
from streamlit.proto.TextArea_pb2 import TextArea as TextAreaProto
from streamlit.proto.TextInput_pb2 import TextInput as TextInputProto
from .utils import register_widget
from streamlit.session_state import get_session_state


class TextWidgetsMixin:
    def text_input(
        self,
        label,
        value=None,
        max_chars=None,
        key=None,
        type="default",
        on_change=None,
        context=None,
        help=None,
    ):
        """Display a single-line text input widget.

        Parameters
        ----------
        label : str
            A short label explaining to the user what this input is for.
        value : any
            The text value of this widget when it first renders. This will be
            cast to str internally.
        max_chars : int or None
            Max number of characters allowed in text input.
        key : str
            An optional string to use as the unique key for the widget.
            If this is omitted, a key will be generated for the widget
            based on its content. Multiple widgets of the same type may
            not share the same key.
        type : str
            The type of the text input. This can be either "default" (for
            a regular text input), or "password" (for a text input that
            masks the user's typed value). Defaults to "default".
        on_change : callable
            The callable that is invoked when the value changes. The callable
            only has one parameter, the new value.
        help : str
            A tooltip that gets displayed next to the input.

        Returns
        -------
        str
            The current value of the text input widget.

        Example
        -------
        >>> title = st.text_input('Movie title', 'Life of Brian')
        >>> st.write('The current movie title is', title)

        """
        if key is None:
            key = label

        state = get_session_state()
        force_set_value = value is not None or state.is_new_value(key)

        if value is None:
            value = state[key]
        if value is None:
            value = ""

        text_input_proto = TextInputProto()
        text_input_proto.label = label
        text_input_proto.default = str(value)
        if help is not None:
            text_input_proto.help = help

        if max_chars is not None:
            text_input_proto.max_chars = max_chars

        if type == "default":
            text_input_proto.type = TextInputProto.DEFAULT
        elif type == "password":
            text_input_proto.type = TextInputProto.PASSWORD
        else:
            raise StreamlitAPIException(
                "'%s' is not a valid text_input type. Valid types are 'default' and 'password'."
                % type
            )

        if force_set_value:
            text_input_proto.value = value
            text_input_proto.valueSet = True

        def deserialize_text_input(ui_value):
            return ui_value if ui_value is not None else str(value)

        register_widget(
            "text_input",
            text_input_proto,
            user_key=key,
            on_change_handler=on_change,
            context=context,
            deserializer=deserialize_text_input,
        )
        return self.dg._enqueue("text_input", text_input_proto, value)

    def text_area(
        self,
        label,
        value="",
        height=None,
        max_chars=None,
        key=None,
        on_change=None,
        context=None,
        help=None,
    ):
        """Display a multi-line text input widget.

        Parameters
        ----------
        label : str
            A short label explaining to the user what this input is for.
        value : any
            The text value of this widget when it first renders. This will be
            cast to str internally.
        height : int or None
            Desired height of the UI element expressed in pixels. If None, a
            default height is used.
        max_chars : int or None
            Maximum number of characters allowed in text area.
        key : str
            An optional string to use as the unique key for the widget.
            If this is omitted, a key will be generated for the widget
            based on its content. Multiple widgets of the same type may
            not share the same key.
        on_change : callable
            The callable that is invoked when the value changes. The callable
            only has one parameter, the new value.
        help : str
            A tooltip that gets displayed next to the textarea.

        Returns
        -------
        str
            The current value of the text input widget.

        Example
        -------
        >>> txt = st.text_area('Text to analyze', '''
        ...     It was the best of times, it was the worst of times, it was
        ...     the age of wisdom, it was the age of foolishness, it was
        ...     the epoch of belief, it was the epoch of incredulity, it
        ...     was the season of Light, it was the season of Darkness, it
        ...     was the spring of hope, it was the winter of despair, (...)
        ...     ''')
        >>> st.write('Sentiment:', run_sentiment_analysis(txt))

        """
        if key is None:
            key = label

        state = get_session_state()
        force_set_value = value is not None or state.is_new_value(key)

        if value is None:
            value = state[key]
        if value is None:
            value = ""

        text_area_proto = TextAreaProto()
        text_area_proto.label = label
        text_area_proto.default = str(value)
        if help is not None:
            text_area_proto.help = help

        if height is not None:
            text_area_proto.height = height

        if max_chars is not None:
            text_area_proto.max_chars = max_chars

        if force_set_value:
            text_area_proto.value = value
            text_area_proto.valueSet = True

        def deserialize_text_area(ui_value):
            return ui_value if ui_value is not None else str(value)

        register_widget(
            "text_area",
            text_area_proto,
            user_key=key,
            on_change_handler=on_change,
            context=context,
            deserializer=deserialize_text_area,
        )
        return self.dg._enqueue("text_area", text_area_proto, value)

    @property
    def dg(self) -> "streamlit.delta_generator.DeltaGenerator":
        """Get our DeltaGenerator."""
        return cast("streamlit.delta_generator.DeltaGenerator", self)
