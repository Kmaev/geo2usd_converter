name = "trace_terminal"
version = "1.0.0"
build_command = "python {root}/build.py {install}"

requires = ["tracepath_indie", "houdini"]

def commands():
    import os
    global env

    env.PR_SHOW_ROOT = os.environ.get("PR_SHOW_ROOT", "")
    source("{root}/shell/show_nav.sh")
