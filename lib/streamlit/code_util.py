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

"""A bunch of useful code utilities."""

import os
import re

import streamlit as st


def extract_args(line):
    """Parse argument strings from all outer parentheses in a line of code.

    Parameters
    ----------
    line : str
        A line of code

    Returns
    -------
    list of strings
        Contents of the outer parentheses

    Example
    -------
    >>> line = 'foo(bar, baz), "a", my(func)'
    >>> extract_args(line)
    ['bar, baz', 'func']

    """
    stack = 0
    startIndex = None
    results = []

    for i, c in enumerate(line):
        if c == "(":
            if stack == 0:
                startIndex = i + 1
            stack += 1
        elif c == ")":
            stack -= 1
            if stack == 0:
                results.append(line[startIndex:i])
    return results


def get_method_args_from_code(args, line):
    """Parse arguments from a stringified arguments list inside parentheses

    Parameters
    ----------
    args : list
        A list where it's size matches the expected number of parsed arguments
    line : list
        Stringified line of code with method arguments inside parentheses

    Returns
    -------
    list of strings
        Parsed arguments

    Example
    -------
    >>> line = 'foo(bar, baz, my(func, tion))'
    >>>
    >>> get_method_args_from_code(range(0, 3), line)
    ['bar', 'baz', 'my(func, tion)']

    """
    line_args = extract_args(line)[0]

    # Split arguments, https://stackoverflow.com/a/26634150
    if len(args) > 1:
        inputs = re.split(",\\s*(?![^(){}[\]]*\\))", line_args)
        assert len(inputs) == len(args), "Could not split arguments"
    else:
        inputs = [line_args]
    return inputs


# Extract the streamlit package path
_streamlit_dir = os.path.dirname(st.__file__)
# Make it absolute, and ensure there's a trailing path separator
_streamlit_dir = os.path.join(os.path.realpath(_streamlit_dir), "")


def _is_in_streamlit_package(file):
    """True if the given file is part of the streamlit package."""
    return (
        os.path.commonprefix([os.path.realpath(file), _streamlit_dir]) == _streamlit_dir
    )


def get_nonstreamlit_frameinfos(frameinfos=None):
    if frameinfos is None:
        import inspect

        frameinfos = inspect.stack()

    return [
        frameinfo
        for frameinfo in frameinfos
        if not _is_in_streamlit_package(frameinfo.filename)
    ]
