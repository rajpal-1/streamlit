#!/usr/bin/env python

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

"""Process Mypy line precision report into useful statistics."""

from __future__ import annotations


import itertools
import os
import shlex
import sys
import tempfile

import click
import mypy.main as mypy_main

PATHS = ["lib/streamlit/", "lib/tests/streamlit/typing/", "scripts/", "e2e/scripts/"]


class Module:
    _COLUMNS = (56, 5, 5, 7)
    _HEADERS = ("Module", "Lines", "Typed", "Percent")

    def __init__(self, name: str, lines: int = 0, precise: int = 0):
        self.name = name
        self.lines = lines
        self.precise = precise

    @classmethod
    def header(cls) -> str:
        fmt = "%-*s  %-*s  %-*s  %-*s"
        return ("%s\n%s" % (fmt, fmt)) % tuple(
            itertools.chain(
                *zip(cls._COLUMNS, cls._HEADERS),
                *zip(cls._COLUMNS, ["-" * len(h) for h in cls._HEADERS]),
            )
        )

    def __str__(self) -> str:
        cols = self._COLUMNS
        return "%-*s  %*d  %*d % 7.02f%%" % (
            cols[0],
            self.name,
            cols[1],
            self.lines,
            cols[2],
            self.precise,
            self.precise * 100 / self.lines,
        )


def process_report(path: str) -> None:
    modules: list[Module] = []
    totals = Module("Total")

    with open(path) as f:
        for line in f.readlines()[2:]:  # Skip two header lines.
            parts = line.split()
            name = parts[0]
            if name.endswith("_pb2"):
                continue
            total_lines = int(parts[1])
            empty_lines = int(parts[5])
            lines = total_lines - empty_lines
            if not lines:
                continue
            precise = int(parts[2])
            modules.append(Module(name, lines, precise))
            totals.lines += lines
            totals.precise += precise

    print(Module.header())
    for module in sorted(modules, key=lambda m: m.name):
        print(str(module))
    print(str(totals))


@click.command()
@click.option("--report", is_flag=True, help="Emit line coverage report for all files")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help=("Verbose mode. Causes this command to print mypy command being executed."),
)
def main(report: bool = False, verbose: bool = False) -> None:
    args = ["--config-file=lib/mypy.ini", "--namespace-packages"]
    if report:
        tempdir = tempfile.TemporaryDirectory()
        args.append("--lineprecision-report=%s" % tempdir.name)
    args.append("--")
    args.extend(PATHS)

    if verbose:
        shell_command = shlex.join(itertools.chain(["mypy"], args))
        print("Executing command:", shell_command)
    mypy_main.main(stdout=sys.stdout, stderr=sys.stderr, args=args)
    if report:
        process_report(os.path.join(tempdir.name, "lineprecision.txt"))


if __name__ == "__main__":
    main()
