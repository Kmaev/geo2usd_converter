import os
import sys
from pathlib import Path
import shutil

def build(source_path:str, build_path:str, install_path:str, targets:list[str]):
    install_path = Path(install_path)
    source_path = Path(source_path)


    to_copy = {
        source_path / "src": install_path / "python",
        source_path / "resources": install_path / "resources"
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

if __name__ == '__main__':
    build(
        source_path=os.environ['REZ_BUILD_SOURCE_PATH'],
        build_path=os.environ['REZ_BUILD_PATH'],
        install_path=os.environ['REZ_BUILD_INSTALL_PATH'],
        targets=sys.argv[1:]
    )

#To build rez package:
# cd /Users/kmaev/Documents/hou_dev/tracepath_pipeline/modules/tracepath
# rez build --install
