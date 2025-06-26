import os
import re
import pathlib
import _utils
from dataclasses import dataclass, field


@dataclass
class TextureResolve:
    geometry_file: str
    tex_folder_relative_path: str = "./"
    tex_conversion: dict[str, str] = field(default_factory=lambda: {
        "base_color": "basecolor",
        "specular": "specular",
        "normal": "normal"
    })
    mapping: dict[str, pathlib.Path] = field(default_factory=dict)
    name_space: str = ""



    def get_folder_abs_path(self)->pathlib.Path:
        return pathlib.Path(os.path.dirname(self.geometry_file))

    def parse_texture(self):
        name_space_edit = _utils.flatten_input_data(self.name_space)
        folder_path = self.get_folder_abs_path()
        tex_abs_path = pathlib.Path(os.path.normpath(os.path.join(str(folder_path), self.tex_folder_relative_path)))

        for file in tex_abs_path.iterdir():
            file_edit = _utils.flatten_input_data(str(file))
            for mlx_text, source_tex in self.tex_conversion.items():
                texture_edit = _utils.flatten_input_data(source_tex)
                if texture_edit in file_edit and name_space_edit in file_edit:
                    self.mapping[mlx_text] = file
        return self.mapping



