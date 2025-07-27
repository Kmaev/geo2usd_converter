#!/bin/bash


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PR_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PR_ROOT
echo "Set PR_ROOT to $PR_ROOT"

if [ -z "$PR_PROJECTS_PATH" ]; then
    echo "[ERROR] PR_PROJECTS_PATH not set. Please export it before running this script."
    return 1 2>/dev/null || exit 1
else
    echo "Using PR_PROJECTS_PATH: $PR_PROJECTS_PATH"
fi

export REZ_USED_RESOLVE_ENV=PR_PROJECTS_PATH

rez env trace_terminal
