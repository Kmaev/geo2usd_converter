name = "tracepath_indie"
version = "1.0.0"
build_command = "python {root}/build.py {install}"


def commands():
    global env

    env.PYTHONPATH.append("{root}/python")