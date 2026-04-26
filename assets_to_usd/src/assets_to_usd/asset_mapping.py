import re
from pathlib import Path


def flatten_input_data(data_str: str) -> str:
    """
    Normalize a string for matching.

    Args:
        data_str: Input string.

    Returns:
        str: Normalized string.
    """
    return re.sub(r'[^a-zA-Z0-9]', '', data_str).lower()


def create_assets_dictionary(asset_lib_path: str, lib_name: str | None = None, tex_folder_path: str | None = None) \
        -> dict[Path, Path]:
    """
    Build mapping between geometry files and texture folders.

    Args:
        asset_lib_path: Asset library path.
        lib_name: Library type (e.g. Kitbash, Megascans).
        tex_folder_path: Custom texture folder path.

    Returns:
        dict: Geometry to texture mapping.
    """
    geo_tex_mapping = {}
    file_formats = ["fbx", "bgeo.sc", "obj"]
    lib_path = Path(asset_lib_path)

    if not lib_path.is_dir():
        raise ValueError(f"Invalid Asset Library Path: {asset_lib_path}")

    if lib_name and tex_folder_path:
        raise ValueError("Specify either lib_name or tex_folder_path, not both.")

    if lib_name and tex_folder_path is None:
        if lib_name == "Kitbash":
            geo_folder = lib_path / "geo"
            tex_folder = lib_path / "KB3DTextures"

            if geo_folder.is_dir() and tex_folder.is_dir():
                resolution_folder = next(
                    (f for f in tex_folder.iterdir() if f.is_dir() and re.match(r'^\d+k$', f.name)),
                    None
                )
                if resolution_folder is None:
                    raise FileNotFoundError(f"No resolution folder like '2k', '4k' found in {tex_folder}")

                tex_folder = tex_folder / resolution_folder

                for geo_file in geo_folder.iterdir():
                    if geo_file.is_file() and any(geo_file.name.lower().endswith(f".{ext}") for ext in file_formats):
                        geo_tex_mapping[geo_file] = tex_folder
                        print(f"{geo_file} -> {tex_folder}")

        elif lib_name == "Megascans":
            for asset in lib_path.iterdir():
                geo_folder = asset
                if geo_folder.is_dir():
                    for geo_file in geo_folder.iterdir():
                        if geo_file.is_file() and any(
                                geo_file.name.lower().endswith(f".{ext}") for ext in file_formats):
                            geo_tex_mapping[geo_file] = geo_folder
        else:
            raise ValueError(f"Unsupported library name: {lib_name}, currently supported: 'Kitbash', 'Megascans'")

    elif tex_folder_path and lib_name is None:
        tex_folder_path = Path(tex_folder_path)
        if tex_folder_path.is_dir():
            for asset in lib_path.iterdir():
                if asset.is_file() and any(asset.name.lower().endswith(f".{ext}") for ext in file_formats):
                    geo_tex_mapping[asset] = tex_folder_path
        else:
            raise ValueError(f"Texture folder {tex_folder_path} not found")

    elif lib_name is None and tex_folder_path is None:
        for asset in lib_path.iterdir():
            if asset.is_file() and any(asset.name.lower().endswith(f".{ext}") for ext in file_formats):
                geo_tex_mapping[asset] = lib_path

    else:
        raise ValueError("Invalid argument combination")

    if not geo_tex_mapping:
        raise ValueError("No valid geometry-texture mappings found.")

    return geo_tex_mapping
