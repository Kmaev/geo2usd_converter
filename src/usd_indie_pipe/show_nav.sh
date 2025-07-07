#!/bin/bash

export PROJECTS_ROOT="/Users/kmaev/Documents/hou_dev/houdini_scenes/Projects"

load() {
    export SHOW=$1
    export REALM=$2
    export SHOW_ROOT="$PROJECTS_ROOT/$SHOW/$REALM"

    local show_env="$PROJECTS_ROOT/$SHOW/utils/show.env"
    if [[ -f "$show_env" ]]; then
        set -a
        source "$show_env"
        set +a
        echo "[INFO] Loaded context: SHOW=$SHOW, REALM=$REALM"
    else
        echo "[WARNING] No show.env found for: $SHOW"
    fi
}

cdtask() {
    local path=""

    if [[ "$REALM" == "shots" ]]; then
        export SEQUENCE=$1
        export SHOT=$2
        export TASK=$3
        export SUBTASK=$4
        path="$SHOW_ROOT/$REALM/$SEQUENCE/$SHOT/$TASK/$SUBTASK"
    else
        export ASSET_NAME=$1
        export TASK=$2
        export SUBTASK=$3
        path="$SHOW_ROOT/$REALM/$ASSET_NAME/$TASK/$SUBTASK"
    fi

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

houdini() {
    local houdini_app="/Applications/Houdini/Houdini20.5.613/Houdini Indie 20.5.613.app"

    if [[ ! -d "$houdini_app" ]]; then
        echo "[ERROR] Houdini app not found at: $houdini_app"
        return 1
    fi

    echo "[INFO] Launching Houdini with:"
    if [[ "$REALM" == "shots" ]]; then
        echo "  SHOW=$SHOW | REALM=$REALM | SEQUENCE=$SEQUENCE | SHOT=$SHOT | TASK=$TASK | SUBTASK=$SUBTASK"
    else
        echo "  SHOW=$SHOW | REALM=$REALM | ASSET=$ASSET_NAME | TASK=$TASK | SUBTASK=$SUBTASK"
    fi

    open -a "$houdini_app"
}
