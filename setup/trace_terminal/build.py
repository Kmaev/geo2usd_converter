import os
import sys
import shutil
from pathlib import Path

def build(source_path, build_path, install_path, targets):
    install_path = Path(install_path)
    source_path = Path(source_path)

    to_copy = {
        source_path / "show_nav" : install_path / "shell",
    }

    if "install" in targets:
        for src, dest in to_copy.items():
            if dest.exists():
                print("Deleting", dest)
                shutil.rmtree(dest)

            print("Copying {} to {}".format(src, dest))
            shutil.copytree(src, dest)
    else:
        print("Package does not build, doing nothing...")

if __name__ == "__main__":
    build(
        source_path=os.environ["REZ_BUILD_SOURCE_PATH"],
        build_path=os.environ["REZ_BUILD_PATH"],
        install_path=os.environ["REZ_BUILD_INSTALL_PATH"],
        targets=sys.argv[1:]
    )
