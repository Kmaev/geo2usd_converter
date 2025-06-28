import json
from pathlib import Path

import hou

"""
This module explores one possible approach to recreating a usd file based on imported geometry.
A very low-level method.
"""


def create_temp_hou_stage(file_path):
    """
    Creates a temp usd scene in memory to import a geometry file and export usd file
    """
    asset_name = file_path.name.split(".")[0]
    if not file_path.exists():
        raise FileNotFoundError(f"Could not find geometry file: {file_path}")
    else:
        # create Sop read
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
        print(f"Converted USD: {str(usd_file)}")


def construct_usd_file_path(geo_path: Path, separate_usd_folder: bool = True) -> str:
    """
    Construct the output .usda path from a geometry file path.
    If separate_usd_folder is True, usd files will be put into usd subfolder.
    """
    clean_base = geo_path.name.split(".")[0]
    usd_file_name = clean_base + ".usda"

    if separate_usd_folder:
        usd_dir = geo_path.parent / "usd"
    else:
        usd_dir = geo_path.parent

    usd_path = usd_dir / usd_file_name
    return str(usd_path)


def run_geo_to_usd_conversion(conversion_data: str):
    """
     Runs geometry-to-usd conversion using a list of input geometry files provided in a json file.

    Parameters:
        conversion_data (str): Path to a json file containing a list of geometry file paths (e.g., .bgeo.sc, .obj).
    """
    with open(conversion_data, "r") as r:
        conv_data = json.load(r)
    for file_path in conv_data:
        file_path = Path(file_path)
        create_temp_hou_stage(file_path)
