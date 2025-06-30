import re
from pathlib import Path


def flatten_input_data(data_str: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]', '', data_str).lower()


def create_assets_dictionary(asset_lib_path: str, lib_name=None, tex_folder_path=None) -> dict:
    geo_tex_mapping = {}
    file_formats = ["fbx", "bgeo.sc", "obj"]
    lib_path = Path(asset_lib_path)
    if lib_name and tex_folder_path is None:
        if lib_name == "Kitbash":
            geo_folder = lib_path / "geo"
            tex_folder = lib_path / "KB3DTextures"
            if geo_folder.is_dir() and tex_folder.is_dir():

                resolution_folder = next(
                    (f for f in tex_folder.iterdir() if f.is_dir() and re.match(r'^\d+k$', f.name)),
                    None
                )
                tex_folder = tex_folder / resolution_folder
                for geo_file in geo_folder.iterdir():
                    if any(geo_file.name.endswith(f".{ext}") for ext in file_formats):
                        geo_tex_mapping[geo_file] = tex_folder
                        print(f"{geo_file} -> {tex_folder}")

        elif lib_name == "Megascans":
            for asset in lib_path.iterdir():
                geo_folder = lib_path / asset
                if geo_folder.is_dir():
                    for geo_file in geo_folder.iterdir():
                        if geo_file.name.endswith(".fbx"):
                            geo_tex_mapping[geo_file] = geo_folder


    elif tex_folder_path and lib_name is None:
        for asset in lib_path.iterdir():
            if asset.is_dir():
                geo_tex_mapping[asset] = tex_folder_path

    elif lib_name is None and tex_folder_path is None:

        for asset in lib_path.iterdir():
            for format in file_formats:
                if asset.name.endswith(format):
                    geo_tex_mapping[asset] = lib_path

    else:
        raise ValueError(f"Not enough data: ")

    return geo_tex_mapping
