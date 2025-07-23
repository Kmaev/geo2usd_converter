import json
import os
import re
from pathlib import Path

import hou


# Generic functions for Load and Write USD HDAs in houdini
def get_env() -> dict:
    """
    Gets environment variables for path resolution.
    """
    env_data = {
        "pr_root": os.getenv("PR_ROOT"),
        "pr_show": os.getenv("PR_SHOW")
    }
    return env_data


def get_node_env_data(node: hou.Node) -> dict:
    """
    Retrieve environment variables from HDA parameters.
    """
    node_data = {
        "pr_group": node.parm("grp").evalAsString(),
        "pr_item": node.parm("item").evalAsString(),
        "pr_task": node.parm("task").evalAsString()
    }
    return node_data


def get_path_structure_templ(template: str) -> str | list | None:
    """
    Load a path template from the folder_structure.json file.
    """
    json_path = Path(__file__).parent / "folder_structure.json"

    try:
        with open(json_path) as f:
            folder_structure = json.load(f)
        return folder_structure[template]
    except KeyError:
        hou.ui.displayMessage(
            f"Template key '{template}' not found in {json_path.name}",
            severity=hou.severityType.Error
        )
        return None


def get_manifest_context(node: hou.Node, templ) -> str:
    """
    Resolve the full context path for the USD shot manifest using template and environment values.
    This function is also used in houdini HDA
    """
    env_vars = get_env()
    node_vars = get_node_env_data(node)
    all_node_data = {**env_vars, **node_vars}

    templ_folder, _ = get_path_structure_templ(templ)
    context = templ_folder.format(**all_node_data)

    return context


def find_matching_files(base_path: str, version: int) -> str | None:
    """
    Find a version folder and a file inside a version folder that contains the version string in its name.
    Shot manifest context is sources from the template, but the actual file is sources by listing folders.
    """
    node_version = str(version).zfill(3)
    base = Path(base_path)
    results = []
    for subfolder in base.iterdir():
        if subfolder.is_dir() and node_version in subfolder.name:
            for file in subfolder.iterdir():

                if node_version in file.name:
                    results.append(file)
    return results[0] if results else None


def get_latest_version_number(context: str) -> int | None:
    """
    Gets the highest version number from versioned subfolders in a given context.
    """
    context_path = Path(context)
    if not context_path.exists():
        return None

    versioned_dirs = []
    for d in context_path.iterdir():
        match = re.search(r'\d+', d.name)
        if match:
            versioned_dirs.append(int(match.group()))
    if versioned_dirs:
        version = sorted(versioned_dirs, reverse=True)[0]
        return version
    else:
        return None


# Load USD Stage HDA

def set_latest_version(node: hou.Node, context: str):
    """
    Set the node's version parameter to the latest version found in the context folder (Run from HDA on node creation).
    """
    version = get_latest_version_number(str(context))
    node.parm("version").set(version)


def load_shot_manifest(node: hou.Node) -> str:
    """
    Load the path to the main shot manifest file based on the version selected in the HDA.
    Used in HDA parameter
    """
    context = get_manifest_context(node, "usd_shot_manifest_output")
    node_version = node.parm("version").evalAsString()
    file = find_matching_files(str(context), node_version)

    if not file or not Path(file).exists():
        raise RuntimeError(f"No matching file found for version '{node_version}' in: {context}")
    return str(file)


# Write USD HDA:

def get_usd_output_path(node: hou.Node, template) -> str:
    """
    Solves the usd output file path using environment variables and the selected template.
    """
    env_vars = get_env()
    node_vars = get_node_env_data(node)

    node_vars["name"] = node.parm("name").eval()
    node_vars["version"] = str(node.parm("version").eval()).zfill(3)
    node_vars["file_format"] = node.parm("format").evalAsString()
    node_vars["padding"] = ".$F4" if node.evalParm("trange") else ""
    all_node_data = {**env_vars, **node_vars}

    templ = get_path_structure_templ(template)
    if not templ:
        raise RuntimeError(f"Template '{template}' not found.")
    output_path = templ.format(**all_node_data)
    return output_path


def get_first_frame_cache(node: hou.Node) -> float:
    """
    Gets first frame cache for a given node.
    """
    first_frame = node.parm("f1").eval()
    cache_parm = node.parm("lopoutput").evalAtFrame(first_frame)
    return cache_parm


def apply_autoversion(node: hou.Node):
    """
    This function called from HDA to version up the file
    """
    version = 1
    if node.parm("autoversion").eval() == 1:
        context = Path(node.parm("lopoutput").evalAsString()).parent.parent
        if context.exists():
            latest_version = get_latest_version_number(str(context))
            if latest_version:
                version = latest_version
    node.parm("version").set(version)


def version_up_shot_manifest(node: hou.Node) -> str | None:
    """
    Versions up main shot manifest path. Creates an output path, using re extracts the version number.
    This function called from Write USD HDA
    """
    new_output_path = ""
    context = Path(get_manifest_context(node, "usd_shot_manifest_output"))
    if context.exists():
        latest_version = get_latest_version_number(str(context))
        if latest_version:
            output_path = find_matching_files(str(context), latest_version)
            if output_path:
                path = Path(output_path)
                parent_folder = path.parent
                file_name = path.name

                match = re.search(r"(\d+)$", parent_folder.name)

                if match:
                    version = match.group(1)
                    version_up = int(version) + (
                        1 if hou.frame() == node.parm("f1").eval() or node.parm("trange").eval() == 0 else 0)

                    new_version = str(version_up).zfill(len(version))
                    new_folder_name = parent_folder.name.replace(version, new_version)
                    new_folder = parent_folder.parent / new_folder_name
                    new_file_name = file_name.replace(version, new_version)
                    new_output_path = new_folder / new_file_name

    if not new_output_path:
        node_vars = {}
        node_vars["version"] = "001"
        node_vars["file_format"] = node.parm("format").evalAsString()

        _, templ_file = get_path_structure_templ("usd_shot_manifest_output")
        new_file_path = Path(templ_file.format(**node_vars))
        new_output_path = context / new_file_path

    return str(new_output_path)


# Publishing

def get_data_folder() -> Path:
    """
    Helper function to get the data folder.
    """
    env_vars = get_env()
    return Path(env_vars["pr_root"]) / env_vars["pr_show"] / "show_data"


def get_publish_key(node: hou.Node) -> str:
    """
    Helper function to get the publish key, publish key consist of group and item what in classic vfx pipeline would be
    sequence and shot.
    """
    node_data = get_node_env_data(node)
    return f"{node_data['pr_group']}_{node_data['pr_item']}"


def write_publish_comment(node: hou.Node) -> None:
    """
    Writes a publish comment to the published data file.
    """
    comment = node.parm("comment").eval()
    file = node.parm("shot_manifest_output").eval()

    data_folder = get_data_folder()
    key = get_publish_key(node)

    published_data = get_published_data(data_folder)
    published_data.setdefault(key, {})
    published_data[key][file] = comment

    write_published_data(data_folder, published_data)
    node.parm("comment").set("")
    hou.ui.displayMessage(f"Shot manifest: \n{file} \npublished successfully!", severity=hou.severityType.Message)


def get_published_data_path(data_folder: Path) -> Path:
    """
    Helper function to get the path to the json file with all the published data. (Published data is show-based)
    """
    return data_folder / "published_data.json"


def get_published_data(data_folder: Path) -> dict:
    """
    Loads the published assets data from a JSON file.

    If the JSON file does not exist, it creates an empty one and returns an empty dictionary.
    """
    data_folder.mkdir(parents=True, exist_ok=True)
    published_data_path = get_published_data_path(data_folder)

    if not published_data_path.exists():
        published_data_path.write_text('{}')

    return json.loads(published_data_path.read_text())


def write_published_data(data_folder: Path, published_data: dict) -> None:
    """
    Writes the published assets data to a JSON file.
    """
    published_data_path = get_published_data_path(data_folder)
    published_data_path.write_text(json.dumps(published_data, indent=4))


def read_publish_comment(node: hou.Node) -> str | None:
    """
    Reads the published comment from the published data file. Called from HDA parameter
    """
    file_path = node.parm("shot_manifest_read").evalAsString()
    data_folder = get_data_folder()
    key = get_publish_key(node)
    published_data = get_published_data(data_folder)

    file_to_comment = published_data.get(key, {})
    for f, comment in file_to_comment.items():
        if f == file_path:
            return comment

    return None
