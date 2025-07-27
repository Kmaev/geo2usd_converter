echo "[TRACEPATH] show_nav.sh sourced successfully"

load() {
    export PR_SHOW="$1"

    export PR_SHOW_ROOT="$PR_PROJECTS_PATH/$PR_SHOW"
    echo "[DEBUG] PR_SHOW=$PR_SHOW"
}

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

