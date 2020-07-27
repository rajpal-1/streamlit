#!/usr/bin/env python

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

import os
import pathlib
import shutil
import signal
import subprocess
import sys
from contextlib import contextmanager
from os.path import dirname, abspath, basename, splitext, join
from typing import List

import click

ROOT_DIR = dirname(dirname(abspath(__file__)))  # streamlit root directory
FRONTEND_DIR = join(ROOT_DIR, "frontend")
COMPONENT_TEMPLATE_DIRS = [
    join(ROOT_DIR, "component-template/template/my_component"),
    join(ROOT_DIR, "component-template/template-reactless/my_component"),
]

CREDENTIALS_FILE = os.path.expanduser("~/.streamlit/credentials.toml")


class Context:
    def __init__(self):
        # Whether to prompt to continue on failure or run all
        self.always_continue = False
        # True if Cypress will record videos of our results.
        self.record_results = False
        # True if we're automatically updating snapshots.
        self.update_snapshots = False
        # Parent folder of the specs and scripts.
        # 'e2e' for tests we expect to pass or 'e2e_flaky' for tests with
        # known issues.
        self.tests_dir_name = "e2e"
        # Set to True if any test fails.
        self.any_failed = False

    @property
    def tests_dir(self) -> str:
        return join(ROOT_DIR, self.tests_dir_name)

    @property
    def cypress_flags(self) -> List[str]:
        """Flags to pass to Cypress"""
        flags = ["--config", f"integrationFolder={self.tests_dir}/specs"]
        if self.record_results:
            flags.append("--record")
        if self.update_snapshots:
            flags.extend(["--env", "updateSnapshots=true"])
        return flags


def remove_if_exists(path):
    """Remove the given folder or file if it exists"""
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


@contextmanager
def move_aside_file(path):
    """Move a file aside if it exists; restore it on completion"""
    moved = False
    if os.path.exists(path):
        os.rename(path, f"{path}.bak")
        moved = True

    try:
        yield None
    finally:
        if moved:
            os.rename(f"{path}.bak", path)


def create_credentials_toml(contents):
    """Writes ~/.streamlit/credentials.toml"""
    # Ensure our parent directory exists
    os.makedirs(dirname(CREDENTIALS_FILE), exist_ok=True)

    with open(CREDENTIALS_FILE, "w") as f:
        f.write(contents)


def kill_streamlits():
    """Kill any active `streamlit run` processes"""
    result = subprocess.run(
        "pgrep -f 'streamlit run'",
        shell=True,
        universal_newlines=True,
        capture_output=True,
    )

    if result.returncode == 0:
        for pid in result.stdout.split():
            try:
                os.kill(int(pid), signal.SIGTERM)
            except Exception as e:
                print("Failed to kill Streamlit instance", e)


def generate_mochawesome_report():
    """Generate the test report. This should be called right before exit."""
    subprocess.run(
        "npx -q mochawesome-merge --reportDir cypress/mochawesome > mochawesome.json",
        cwd=FRONTEND_DIR,
        shell=True,
    )

    subprocess.run(
        "npx -q mochawesome-report-generator mochawesome.json",
        cwd=FRONTEND_DIR,
        shell=True,
    )


def run_test(
    ctx: Context,
    specpath: str,
    streamlit_command: List[str],
    no_credentials: bool = False,
) -> None:
    """Run a single e2e test.

     An e2e test consists of a Streamlit script that produces a result, and
     a Cypress test file that asserts that result is as expected.

    Parameters
    ----------
    ctx : Context
        The Context object that contains our global testing parameters.
    specpath : str
        The path of the Cypress spec file to run.
    streamlit_command : list of str
        The Streamlit command to run (passed directly to subprocess.Popen()).
    no_credentials : bool
        Any existing ~/.streamlit/credentials.toml file will be moved aside
        for the test, and by default a bare-bones placeholder credentials file
        will be created in its place. But if `no_credentials` is True, the test
        will be run without a credentials file.

    """
    # Move existing credentials file aside, and create a new one if the
    # tests call for it.
    with move_aside_file(CREDENTIALS_FILE):
        if not no_credentials:
            create_credentials_toml('[general]\nemail="test@streamlit.io"')

        # Infinite loop to support retries
        while True:
            try:
                # Start the Streamlit script. It will continue running until
                # we terminate it below.
                streamlit_proc = subprocess.Popen(streamlit_command, cwd=FRONTEND_DIR)

                # Run the Cypress spec.
                cypress_command = ["yarn", "cy:run", "--spec", specpath]
                cypress_command.extend(ctx.cypress_flags)
                cypress_result = subprocess.run(cypress_command, cwd=FRONTEND_DIR)
            finally:
                # Kill the Streamlit script.
                streamlit_proc.terminate()
                streamlit_proc.wait()

            if cypress_result.returncode != 0:
                # The test failed!
                if not ctx.always_continue:
                    # Prompt the user for what to do next.
                    user_input = click.prompt(
                        "[R]etry, [U]pdate snapshots, [S]kip, or [Q]uit?"
                    )
                    key = user_input[0].lower()
                    if key == "s":
                        break
                    elif key == "q":
                        ctx.any_failed = True
                        raise RuntimeError("Terminating early")
                    elif key == "r":
                        continue
                    elif key == "u":
                        ctx.update_snapshots = True
                        continue
                    else:
                        # Retry if key not recognized
                        continue
                else:
                    ctx.any_failed = True

            # The test succeeded! Break out of the loop.
            break


def run_component_template_e2e_test(ctx: Context, template_dir: str):
    """Build a component template and run its e2e tests."""
    frontend_dir = join(template_dir, "frontend")

    # Install the template's npm dependencies into its node_modules.
    subprocess.run(["yarn", "install"], cwd=frontend_dir, check=True)

    # Start the template's dev server.
    webpack_proc = subprocess.Popen(["yarn", "start"], cwd=frontend_dir)

    try:
        # Run the test!
        script_path = join(template_dir, "__init__.py")
        spec_path = join(ROOT_DIR, "e2e/specs/component_template.spec.ts")
        run_test(ctx, spec_path, ["streamlit", "run", script_path])
    finally:
        # Kill the webpack server.
        # TODO: I think we want to ensure the server is not run in "watch" mode.
        # It's not being shut down properly.
        webpack_proc.terminate()
        webpack_proc.wait()


@click.command()
@click.option(
    "-a", "--always-continue", is_flag=True, help="Continue running on test failure."
)
@click.option(
    "-r",
    "--record-results",
    is_flag=True,
    help="Upload video results to the Cypress dashboard. "
    "See https://docs.cypress.io/guides/dashboard/introduction.html for more details.",
)
@click.option(
    "-u",
    "--update-snapshots",
    is_flag=True,
    help="Automatically update snapshots for failing tests.",
)
@click.option(
    "-f",
    "--flaky-tests",
    is_flag=True,
    help="Run tests in 'e2e_flaky' instead of 'e2e'.",
)
def run_e2e_tests(
    always_continue: bool,
    record_results: bool,
    update_snapshots: bool,
    flaky_tests: bool,
):
    """Run e2e tests. If any fail, exit with non-zero status."""
    kill_streamlits()

    # Clear reports from previous runs
    remove_if_exists("frontend/cypress/mochawesome")
    remove_if_exists("frontend/mochawesome-report")
    remove_if_exists("frontend/mochawesome.json")

    ctx = Context()
    ctx.always_continue = always_continue
    ctx.record_results = record_results
    ctx.update_snapshots = update_snapshots
    ctx.tests_dir_name = "e2e_flaky" if flaky_tests else "e2e"

    try:
        # First, test "streamlit hello" in different combinations. We skip
        # `no_credentials=True` for the `--server.headless=false` test, because
        # it'll give a credentials prompt.
        if not flaky_tests:
            hello_spec = join(ROOT_DIR, "e2e/specs/st_hello.spec.ts")
            run_test(
                ctx,
                hello_spec,
                ["streamlit", "hello", "--server.headless=true"],
                no_credentials=False,
            )
            run_test(ctx, hello_spec, ["streamlit", "hello", "--server.headless=false"])
            run_test(ctx, hello_spec, ["streamlit", "hello", "--server.headless=true"])

            # Next, run our component_template tests.
            for template_dir in COMPONENT_TEMPLATE_DIRS:
                run_component_template_e2e_test(ctx, template_dir)

        # Test core streamlit elements
        p = pathlib.Path(join(ROOT_DIR, ctx.tests_dir_name, "scripts")).resolve()
        for test_path in p.glob("*.py"):
            test_name, _ = splitext(basename(test_path.as_posix()))
            specpath = join(ctx.tests_dir, "specs", f"{test_name}.spec.ts")
            run_test(ctx, specpath, ["streamlit", "run", test_path.as_posix()])
    finally:
        generate_mochawesome_report()

    if ctx.any_failed:
        sys.exit(1)


if __name__ == "__main__":
    run_e2e_tests()
