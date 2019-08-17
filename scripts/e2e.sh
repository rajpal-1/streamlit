#!/bin/sh
## Used to run end-to-end tests

# Change working directory so script is run as ./scripts/e2e.sh
cwd=.

# Whether to prompt to continue on failure or run all
always_continue=false

# Records if any test fails so we can return appropriately after all run
any_failed=false

# Handle command line named arguments, passed as `-c .. -a true`
while getopts ":c:a:" opt; do
  case $opt in
    c) cwd="$OPTARG"
    ;;
    a) always_continue="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

# Ensure -a is passed an allowed value
if [ "$always_continue" != "false" ] && [ "$always_continue" != "true" ]
then
  echo "-a must be true or false"
  exit 1
fi

# Kill all active "streamlit run" processes
pids=$(pgrep -f 'streamlit run')

if [ "$pids" ]
then
  kill -9 $pids
fi

# Set working directory
cd "$cwd"

# Generate report on exit
generate_report() {
  npx -q mochawesome-merge --reportDir frontend/cypress/results > frontend/mochawesome.json
  npx -q mochawesome-report-generator frontend/mochawesome.json
}
trap generate_report EXIT

# Clear old results
rm frontend/cypress/results/* || true
rm frontend/mochawesome.json || true

# Test core streamlit elements
for file in examples/core/*.py
do
  # Run next test
  streamlit run $file &
  yarn --cwd "frontend" cy:run --spec "cypress/integration/${file%.*}.spec.ts"

  EXITCODE="$?"

  # Kill the last process executed in the background
  kill -9 $!

  # If exit code is nonzero, prompt user to continue or continue without prompting
  if [ "$EXITCODE" -ne "0" ] && [ "$always_continue" = "false" ]; then
    read -p "Continue? [y/n] " yn
    case $yn in
      [Yy]* ) continue ;;
      * ) exit 1 ;;
    esac
  elif [ "$EXITCODE" -ne "0" ] && [ "$always_continue" = "true" ]; then
    any_failed=true
  fi
done

if [ "$any_failed" = "true" ]
then
  exit 1
fi
