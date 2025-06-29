import argparse
import importlib
import sys
from pathlib import Path

_THIS = Path(__file__)

TEMPLATE_PATH = _THIS.parent.joinpath("convert_to_usd.json")
DEFAULT_TEXTURES_FOLDER_PATH = _THIS.parent.joinpath("textures")

SRC_ROOT = _THIS.parent.parent
module_path = str(SRC_ROOT)

if module_path not in sys.path:
    sys.path.append(module_path)

    _hou_ip = importlib.import_module('usd_indie_pipe._houdini')


def main(args: list[str] | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-path", required=True)
    parser.add_argument("--textures-folder-path", default=DEFAULT_TEXTURES_FOLDER_PATH,required=True)
    namespace = parser.parse_args(args)

    _hou_ip.run_geo_to_usd_conversion(
        namespace.template_path,
        namespace.textures_folder_path,
    )


if __name__ == "__main__":
    main()

"""
Run the following command: Hython executable, path to the convert_usd.py file + --template_path + json file template
/Applications/Houdini/Houdini20.5.613/Frameworks/Houdini.framework/Versions/Current/Resources/bin/hython \
  /Users/kmaev/Documents/hou_dev/usd_indie_pipe/src/usd_indie_pipe/convert_to_usd.py \
  --template-path /Users/kmaev/Documents/hou_dev/usd_indie_pipe/src/usd_indie_pipe/convert_to_usd.json \
   --textures-folder-path /Users/kmaev/Documents/hou_dev/cat_hou/assets/kb3d_ironforge/KB3DTextures/4k"""
