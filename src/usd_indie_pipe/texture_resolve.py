import pathlib
from dataclasses import dataclass, field

from usd_indie_pipe._utils import flatten_input_data


@dataclass
class TextureResolve:
    geometry_file: str
    tex_folder_path: str = ""
    namespace: str = ""

    tex_conversion: dict[str, str] = field(default_factory=lambda: {
        "base_color": "basecolor",
        "specular": "specular"
    })
    mapping: dict[str, pathlib.Path] = field(default_factory=dict)

    def parse_texture(self):
        # we remove the first few characters just because we use asset name as a namespace, and sometimes it comes with prefixes
        name_space_edit = flatten_input_data(self.namespace)[5:]

        tex_folder_abs_path = pathlib.Path(self.tex_folder_path)
        for file in tex_folder_abs_path.iterdir():
            file_edit = flatten_input_data(str(file.stem))
            for mlx_text, source_tex in self.tex_conversion.items():
                texture_edit = flatten_input_data(source_tex)
                if texture_edit in file_edit and name_space_edit in file_edit:
                    self.mapping[mlx_text] = file
        return self.mapping
