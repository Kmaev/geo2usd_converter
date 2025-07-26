"""
Before running the command, make sure USD is installed in your environment.

Run the following command: the Hython executable, followed by the path to the convert_usd.py file,
then add the --asset-lib-path argument, and optionally: --lib-name and --textures-folder-path.

Example usage (Kitbash):
/Applications/Houdini/Houdini20.5.653/Frameworks/Houdini.framework/Versions/Current/Resources/bin/hython \
  /Users/kmaev/Documents/hou_dev/usd_indie_pipe/assets_to_usd/src/assets_to_usd/convert_to_usd.py \
  --asset-lib-path /Users/kmaev/Documents/hou_dev/assets/kb3d_ironforge_test_lib/ \
  --lib-name Kitbash

Example usage (Megascans):
/Applications/Houdini/Houdini20.5.653/Frameworks/Houdini.framework/Versions/Current/Resources/bin/hython \
  /Users/kmaev/Documents/hou_dev/usd_indie_pipe/assets_to_usd/src/assets_to_usd/convert_to_usd.py \
  --asset-lib-path /Users/kmaev/Documents/hou_dev/assets/megascans \
  --lib-name Megascans

Example usage: Match geometry and texture folders independently of the library:
/Applications/Houdini/Houdini20.5.653/Frameworks/Houdini.framework/Versions/Current/Resources/bin/hython \
  /Users/kmaev/Documents/hou_dev/usd_indie_pipe/assets_to_usd/src/assets_to_usd/convert_to_usd.py \
  --asset-lib-path /Users/kmaev/Documents/hou_dev/assets/kb3d_match_by_folders/geo \
  --textures-folder-path /Users/kmaev/Documents/hou_dev/assets/kb3d_match_by_folders/KB3DTextures/4k

Example usage: No texture path or texture library provided
(by default, the tool uses the file's folder as the texture folder):
/Applications/Houdini/Houdini20.5.653/Frameworks/Houdini.framework/Versions/Current/Resources/bin/hython \
  /Users/kmaev/Documents/hou_dev/usd_indie_pipe/assets_to_usd/src/assets_to_usd/convert_to_usd.py \
  --asset-lib-path /Users/kmaev/Documents/hou_dev/assets/megascans/japanese_gravestone_ucmmfjgfa_mid
"""
import argparse
import importlib
import sys
from pathlib import Path

_THIS = Path(__file__)

SRC_ROOT = _THIS.parent.parent
module_path = str(SRC_ROOT)

if module_path not in sys.path:
    sys.path.append(module_path)

    _hou_ip = importlib.import_module('assets_to_usd._houdini')


def main(args: list[str] | None = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-lib-path", required=True, default=None)
    parser.add_argument("--lib-name", required=False, default=None)
    parser.add_argument("--textures-folder-path", required=False, default=None)
    namespace = parser.parse_args(args)

    _hou_ip.run_geo_to_usd_conversion(
        namespace.asset_lib_path,
        namespace.lib_name,
        namespace.textures_folder_path,
    )

if __name__ == "__main__":
    main()


