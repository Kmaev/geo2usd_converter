import difflib
import json
import os
from pathlib import Path


def get_dcc_template() -> dict:
    """
    Reads the JSON file containing folder templates for each DCC.
    """
    script_dir = Path(__file__).parent

    file_path = script_dir / "dcc_templates.json"

    with open(file_path) as f:
        templ_file = json.load(f)
    return templ_file


def create_dcc_folder_structure(dcc_name: str, parent_folder: str):
    """
    Creates a folder structure based on the template for the given DCC.
    """
    parent_folder = Path(parent_folder)
    templ_file = get_dcc_template()
    folders = templ_file.get(dcc_name, [])
    for folder in folders:
        folder_path = parent_folder / dcc_name / folder
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)


def dcc_template_check(_dcc: str, templ_file: dict) -> str | None:
    """
    Checks whether the given DCC exists in the template file.
    If not, returns the closest matching suggestion (if any).
    """
    known_dccs = list(templ_file.keys())
    if _dcc in known_dccs:
        return None
    suggestion = difflib.get_close_matches(_dcc, known_dccs, n=1)
    return suggestion[0] if suggestion else None
