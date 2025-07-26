import os


# ==========================================
# USD HDA functions to solve the env variables

def get_env_group():
    return os.environ.get("PR_GROUP")


def get_env_item():
    return os.environ.get("PR_ITEM")


def get_env_task():
    return os.environ.get("PR_TASK")
