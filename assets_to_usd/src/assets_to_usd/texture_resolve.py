from dataclasses import dataclass, field
from pathlib import Path

from assets_to_usd.asset_mapping import flatten_input_data


@dataclass
class TextureResolve:
    geometry_file: str
    tex_folder_path: str = None
    namespace: str = ""

    tex_conversion: dict[str, str] = field(default_factory=lambda: {
        "base_color": "basecolor",
        "specular": "specular",
        "emission": "emissive",
        "displacement": "height",
        "specular_roughness": "roughness",
        "opacity": "opacity"
    })
    mapping: dict[str, Path] = field(default_factory=dict)

    def parse_texture(self) -> dict:
        # we remove the first few characters because it comes with prefix
        name_space_clean = flatten_input_data(self.namespace)
        name_space_edit = name_space_clean[5:] if len(name_space_clean) > 5 else name_space_clean

        tex_folder_abs_path = Path(self.tex_folder_path)
        for file in tex_folder_abs_path.iterdir():

            file_edit = flatten_input_data(str(file.stem))
            for mlx_text, source_tex in self.tex_conversion.items():
                texture_edit = flatten_input_data(source_tex)
                if texture_edit in file_edit and name_space_edit in file_edit:
                    self.mapping[mlx_text] = file
        return self.mapping
