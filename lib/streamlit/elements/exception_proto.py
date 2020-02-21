# -*- coding: utf-8 -*-
# Copyright 2018-2020 Streamlit Inc.
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

import sys
import traceback

from streamlit.error_util import get_nonstreamlit_traceback
from streamlit.errors import MarkdownFormattedException
from streamlit.errors import StreamlitAPIException
from streamlit.errors import StreamlitAPIWarning
from streamlit.logger import get_logger

LOGGER = get_logger(__name__)


def marshall(exception_proto, exception):
    """Marshalls an Exception.proto message.

    Parameters
    ----------
    exception_proto : Exception.proto
        The Exception protobuf to fill out

    exception : BaseException
        The exception whose data we're extracting
    """
    exception_proto.type = type(exception).__name__

    # If this is a StreamlitAPIException, we prune all Streamlit entries
    # from the exception's stack trace.
    is_api_exception = isinstance(exception, StreamlitAPIException)
    is_markdown_exception = isinstance(exception, MarkdownFormattedException)

    stack_trace = _get_stack_trace_str_list(
        exception, strip_streamlit_stack_entries=is_api_exception
    )

    exception_proto.stack_trace.extend(stack_trace)
    exception_proto.is_warning = isinstance(exception, Warning)

    try:
        if isinstance(exception, SyntaxError):
            # SyntaxErrors have additional fields (filename, text, lineno,
            # offset) that we can use for a nicely-formatted message telling
            # the user what to fix.
            exception_proto.message = _format_syntax_error_message(exception)
        else:
            exception_proto.message = str(exception)
            exception_proto.message_is_markdown = is_markdown_exception
    except Exception as str_exception:
        # Sometimes the exception's __str__/__unicode__ method itself
        # raises an error.
        exception_proto.message = ""
        LOGGER.warning(
            """

Streamlit was unable to parse the data from an exception in the user's script.
This is usually due to a bug in the Exception object itself. Here is some info
about that Exception object, so you can report a bug to the original author:

Exception type:
  %(etype)s

Problem:
  %(str_exception)s

Traceback:
%(str_exception_tb)s

        """
            % {
                "etype": type(exception).__name__,
                "str_exception": str_exception,
                "str_exception_tb": "\n".join(_get_stack_trace_str_list(str_exception)),
            }
        )


def _format_syntax_error_message(exception):
    """Returns a nicely formatted SyntaxError message that emulates
    what the Python interpreter outputs, e.g.:

    > File "raven.py", line 3
    >   st.write('Hello world!!'))
    >                            ^
    > SyntaxError: invalid syntax

    Parameters
    ----------
    exception : SyntaxError

    Returns
    -------
    str

    """
    if exception.text:
        return (
            'File "%(filename)s", line %(lineno)d\n'
            "  %(text)s\n"
            "  %(caret_indent)s^\n"
            "%(errname)s: %(msg)s"
            % {
                "filename": exception.filename,
                "lineno": exception.lineno,
                "text": exception.text.rstrip(),
                "caret_indent": " " * max(exception.offset - 1, 0),
                "errname": type(exception).__name__,
                "msg": exception.msg,
            }
        )
    # If a few edge cases, SyntaxErrors don't have all these nice fields. So we
    # have a fall back here.
    # Example edge case error message: encoding declaration in Unicode string
    return str(exception)


def _get_stack_trace_str_list(exception, strip_streamlit_stack_entries=False):
    """Get the stack trace for the given exception.

    Parameters
    ----------
    exception : BaseException
        The exception to extract the traceback from

    strip_streamlit_stack_entries : bool
        If True, all traceback entries that are in the Streamlit package
        will be removed from the list. We do this for exceptions that result
        from incorrect usage of Streamlit APIs, so that the user doesn't see
        a bunch of noise about ScriptRunner, DeltaGenerator, etc.

    Returns
    -------
    list
        The exception traceback as a list of strings

    """
    if isinstance(exception, StreamlitAPIWarning):
        extracted_traceback = exception.tacked_on_stack
    elif hasattr(exception, "__traceback__"):
        extracted_traceback = traceback.extract_tb(exception.__traceback__)
    else:
        # Hack for Python 2 which will extract the traceback as long as this
        # method was called on the exception as it was caught, which is
        # likely what the user would do.
        _, live_exception, live_traceback = sys.exc_info()
        if exception == live_exception:
            extracted_traceback = traceback.extract_tb(live_traceback)
        else:
            extracted_traceback = None

    # Format the extracted traceback and add it to the protobuf element.
    if extracted_traceback is None:
        stack_trace_str_list = [
            "Cannot extract the stack trace for this exception. "
            "Try calling exception() within the `catch` block."
        ]
    else:
        if strip_streamlit_stack_entries:
            extracted_traceback = get_nonstreamlit_traceback(extracted_traceback)
        stack_trace_str_list = traceback.format_list(extracted_traceback)

    stack_trace_str_list = [item.strip() for item in stack_trace_str_list]

    return stack_trace_str_list
