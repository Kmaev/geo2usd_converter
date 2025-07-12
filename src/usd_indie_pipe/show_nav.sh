#!/bin/bash

# Root directory for all projects
export PR_ROOT="/Users/kmaev/Documents/hou_dev/houdini_scenes/Projects"

# Load project-specific environment
load() {
    export PR_SHOW="$1"
    export PR_SHOW_ROOT="$PR_ROOT/$PR_SHOW"
    echo "[DEBUG] PR_ROOT=$PR_ROOT"
    echo "[DEBUG] PR_SHOW=$PR_SHOW"
    echo "[DEBUG] PR_SHOW_ROOT=$PR_SHOW_ROOT"


    #local show_env="$PR_SHOW_ROOT/utils/show.env"
    #if [[ -f "$show_env" ]]; then
    #    set -a
    #    source "$show_env"
    #    set +a
    #    echo "[INFO] Loaded context: PR_SHOW=$PR_SHOW"
    #else
    #    echo "[WARNING] No show.env found for: $PR_SHOW"
    #fi
}

# Navigate to a task folder
cdtask() {
    export PR_GROUP="$1"
    export PR_ITEM="$2"
    export PR_TASK="$3"

    local path="$PR_SHOW_ROOT/$PR_GROUP/$PR_ITEM/$PR_TASK"

    if [[ -d "$path" ]]; then
        cd "$path" || {
            echo "[ERROR] Failed to change directory to: $path"
            return 1
        }
        echo "[INFO] Moved to: $path"
    else
        echo "[ERROR] Path does not exist: $path"
        return 1
    fi
}

# Launch Houdini Indie
houdini() {
    local houdini_app="/Applications/Houdini/Houdini20.5.653/Houdini Indie 20.5.653.app"

    if [[ ! -d "$houdini_app" ]]; then
        echo "[ERROR] Houdini app not found at: $houdini_app"
        return 1
    fi

    echo "[INFO] Launching Houdini with:"
    echo "       PR_SHOW=$PR_SHOW | GROUP=$PR_GROUP | ITEM=$PR_ITEM | TASK=$PR_TASK"

    open -a "$houdini_app"
}

# Launch PyCharm
pycharm() {
    local pycharm_app="/Applications/PyCharm.app"
    if [[ -d "$pycharm_app" ]]; then
        open -a "$pycharm_app"
    else
        echo "[ERROR] PyCharm not found at: $pycharm_app"
        return 1
    fi
}
