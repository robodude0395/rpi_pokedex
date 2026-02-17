#!/bin/bash
# Wrapper script for running the pipeline
# Delegates to the main entry point

SCRIPT_DIR="$(dirname "$0")"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec bash "$REPO_ROOT/main.sh" "$@"
