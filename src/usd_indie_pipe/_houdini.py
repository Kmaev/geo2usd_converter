from pathlib import Path

import hou

import _usd
import _utils


def create_temp_hou_stage(file_path):
    """
    Creates a temp usd scene in memory to import a geometry file and export usd file
    """
    asset_name = file_path.name.split(".")[0]
    if not file_path.exists():
        raise FileNotFoundError(f"Could not find geometry file: {file_path}")
    else:
        # create Sop read
        print(f"ASSET NAME: {asset_name}")
        sop_create = hou.node("/stage").createNode("sopcreate", asset_name)
        sop_create.parm("enable_partitionattribs").set(True)
        sop_create.parm("partitionattribs").set("path")

        sop_create.parm("enable_subsetgroups").set(True)
        sop_create.parm("subsetgroups").set("m*")

        # create file sop
        file_sop = hou.node(sop_create.path() + "/sopnet/create").createNode("file")
        file_sop.parm("file").set(str(file_path))

        # attrib wrangle
        wrangle_code = f's@path = "geom/{asset_name}";'
        attrib_wrangle = file_sop.createOutputNode("attribwrangle")
        attrib_wrangle.parm("class").set(1)
        attrib_wrangle.parm("snippet").set(wrangle_code)

        # create delete sop
        delete = attrib_wrangle.createOutputNode("attribdelete")
        delete.parm("primdel").set("shop_materialpath")

        # create output
        delete.createOutputNode("output")

        usd_rop = sop_create.createOutputNode("usd_rop")

        usd_file = construct_usd_file_path(file_path)
        usd_rop.parm("lopoutput").set(str(usd_file))

        # Execute save usd file
        usd_rop.parm("execute").pressButton()
        print(f"CONVERTED USD: {str(usd_file)}")

        return usd_file


def construct_usd_file_path(geo_path: Path, separate_usd_folder: bool = True) -> str:
    """
    Construct the output .usda path from a geometry file path.
    If separate_usd_folder is True, usd files will be put into usd subfolder.
    """
    clean_base = geo_path.name.split(".")[0]
    usd_file_name = clean_base + ".usd"

    if separate_usd_folder:
        usd_dir = geo_path.parent / "usd"
    else:
        usd_dir = geo_path.parent

    usd_path = usd_dir / usd_file_name
    return str(usd_path)


def run_geo_to_usd_conversion(asset_lib_path: str, lib_name=None, tex_folder_path=None) -> None:
    """
    Runs geometry-to-usd conversion for all assets found in the given asset library path.

    If a library name is provided, the texture folder will be automatically resolved based on
    the expected folder structure of the specified library (currently supports Kitbash and Megascans).

    If no library name is provided, you can optionally specify a texture folder directly.
    If neither is provided, the tool will default to using the same folder as the geometry file.
    """
    conv_data = _utils.create_assets_dictionary(asset_lib_path, lib_name, tex_folder_path)
    for file_path, tex_folder in conv_data.items():
        file_path = Path(file_path)
        usd_file = create_temp_hou_stage(file_path)
        _usd.run_material_assignment(usd_file, str(tex_folder))
