import json
import os
import re
from pathlib import Path

import hou

from usd_indie_pipe import _usd
from usd_indie_pipe import _utils


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


def get_path_structure_templ(template: str) -> str | None:
    """
    Imports the template to solve the usd file output path
    """
    json_path = Path(__file__).parent / "folder_structure.json"
    with open(json_path) as f:
        folder_structure = json.load(f)
    templ = folder_structure[template]
    return templ


def get_latest_version(context: str) -> int | None:
    """
    Solves the latest version of the usd scene and returns the latest version number.
    """
    context_path = Path(context)
    if context_path.exists():
        versioned_dirs = []
        for d in context_path.iterdir():

            match = re.search(r'\d+', d.name)
            if match:
                versioned_dirs.append(int(match.group()))
        latest_version = sorted(versioned_dirs, reverse=True)[0]
        return latest_version
    return None


def get_usd_output_path(node: hou.Node) -> str:
    """
    Solves the usd output file path using environment variables and the selected template.
    """
    pr_root = os.environ.get("PR_ROOT")
    show = os.environ.get("PR_SHOW")
    if not pr_root or not show:
        raise RuntimeError("Missing PR_ROOT or PR_SHOW environment variables.")

    # Gather node parameters
    template = node.parm("templ").evalAsString()
    grp = node.parm("grp").evalAsString()
    item = node.parm("item").evalAsString()
    task = node.parm("task").evalAsString()
    file_format = node.parm("format").evalAsString()
    name = node.parm("name").eval()
    padding = ".$F4" if node.evalParm("trange") else ""

    # Resolve template
    templ_dir, templ_version = get_path_structure_templ(template)

    if template == "usd_task_output":
        base_output = templ_dir.format(
            pr_root=pr_root, pr_show=show, pr_group=grp,
            pr_item=item, pr_task=task, name=name
        )

        # Auto versioning
        if node.parm("autoversion").eval():
            version = get_latest_version(base_output)
            version = version + 1 if version else 1
            node.parm("version").set(version)
        else:
            version = int(node.parm("version").eval())

    elif template == "usd_main_output":
        base_output = templ_dir.format(
            pr_root=pr_root, pr_show=show, pr_group=grp,
            pr_item=item, pr_task=task
        )
        version = get_latest_version(base_output)
        version = version if version else 1

    else:
        raise ValueError(f"Unsupported template type: {template}")

    # Parsing the second part of the output path string (everything that goes after version folder)
    version_str = str(version).zfill(3)
    version_dir = templ_version.format(
        name=name, version=version_str, padding=padding, format=file_format
    )

    return str(os.path.join(base_output, version_dir))
