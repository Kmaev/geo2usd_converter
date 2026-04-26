"""
Run USD conversion from CLI using hython.

Requires USD and Houdini environment.

Examples:
Kitbash:
/Applications/Houdini/.../hython /path/to/convert_to_usd.py --asset-lib-path /path/to/lib --lib-name Kitbash
Megascans:
/Applications/Houdini/.../hython /path/to/convert_to_usd.py --asset-lib-path /path/to/lib --lib-name Megascans

Custom textures:
/Applications/Houdini/.../hython /path/to/convert_to_usd.py --asset-lib-path /path/to/geo --textures-folder-path /path/to/textures

Default:
/Applications/Houdini/.../hython /path/to/convert_to_usd.py --asset-lib-path /path/to/assets
"""
import argparse
import importlib
import logging
import sys
from pathlib import Path

_THIS = Path(__file__)

SRC_ROOT = _THIS.parent.parent
module_path = str(SRC_ROOT)

if module_path not in sys.path:
    sys.path.append(module_path)

_hou_ip = importlib.import_module('assets_to_usd.hou_stage_builder')


def main(args: list[str] | None = None) -> None:
    """
    Run geometry to USD conversion.

    Args:
        args: Command-line arguments.
    """
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    main()
