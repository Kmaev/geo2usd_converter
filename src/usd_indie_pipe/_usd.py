from pxr import Usd, UsdShade, Kind, Sdf

from usd_indie_pipe.texture_resolve import TextureResolve


def create_material_prim(usd_stage: str, materials: list, tex_folder_path: str) -> Usd.Prim:
    stage = Usd.Stage.Open(usd_stage)
    subsets = get_subcomponents(stage)

    for prim in stage.Traverse():
        if not prim.IsValid() or not prim.IsDefined():
            continue
        if Usd.ModelAPI(prim).GetKind() == Kind.Tokens.component:
            for mat in materials:
                mat_lib_path = prim.GetPath().AppendPath("materials")
                mat_lib_ = stage.DefinePrim(mat_lib_path, "Scope")
                mat_path = mat_lib_path.AppendPath(mat)

                mat_prim = UsdShade.Material.Define(stage, mat_path)

                for sub_prim in subsets:

                    tex_name = sub_prim.GetName()

                    if mat == tex_name:
                        UsdShade.MaterialBindingAPI.Apply(sub_prim).Bind(mat_prim)
                        attr = sub_prim.GetAttribute("familyName")
                        attr.Set("materialBind")

                        mapping = solve_texture(usd_stage, tex_name, tex_folder_path)

                        populate_textures(stage, mat_prim, mapping)

            stage.GetRootLayer().Save()


def get_subcomponents(stage: Usd.Stage) -> list:
    subsets = []
    for prim in stage.Traverse():
        if not prim.IsValid() or not prim.IsDefined():
            continue
        if prim.GetTypeName() == "GeomSubset":
            subsets.append(prim)
    return subsets


def solve_texture(usd_file: str, namespace: str, tex_folder_path: str) -> dict:
    tex_resolve = TextureResolve(usd_file, namespace, tex_folder_path)
    tex_resolve.geometry_file = usd_file
    tex_resolve.namespace = namespace
    tex_resolve.tex_folder_path = tex_folder_path
    mapping = dict(tex_resolve.parse_texture())
    return mapping


def run_material_assignment(usd_file: str, tex_folder_path: str) -> None:
    stage = Usd.Stage.Open(usd_file)
    subc = get_subcomponents(stage)
    mat_lis = [s.GetName() for s in subc]
    create_material_prim(usd_file, mat_lis, tex_folder_path)


def populate_textures(stage: Usd.Stage, mat: Usd.Prim, parms_mapping: dict) -> None:
    mat_path = mat.GetPath()
    surface_shader = UsdShade.Shader.Define(stage, f"{mat_path}/mtlxstandard_surface")  # define shader surface
    surface_shader.CreateIdAttr("ND_standard_surface_surfaceshader")

    # default_values:
    surface_shader.CreateInput("base", Sdf.ValueTypeNames.Float).Set(1.0)
    surface_shader.CreateInput("coat", Sdf.ValueTypeNames.Float).Set(0.0)
    surface_shader.CreateInput("coat_roughness", Sdf.ValueTypeNames.Float).Set(0.1)
    surface_shader.CreateInput("emission", Sdf.ValueTypeNames.Float).Set(0.0)
    surface_shader.CreateInput("emission_color", Sdf.ValueTypeNames.Float3).Set((1.0, 1.0, 1.0))
    surface_shader.CreateInput("metalness", Sdf.ValueTypeNames.Float).Set(0.0)
    surface_shader.CreateInput("specular", Sdf.ValueTypeNames.Float).Set(1.0)
    surface_shader.CreateInput("specular_color", Sdf.ValueTypeNames.Float3).Set((1.0, 1.0, 1.0))
    surface_shader.CreateInput("specular_IOR", Sdf.ValueTypeNames.Float).Set(1.5)
    surface_shader.CreateInput("specular_roughness", Sdf.ValueTypeNames.Float).Set(0.2)
    surface_shader.CreateInput("transmission", Sdf.ValueTypeNames.Float).Set(0.0)
    surface_shader.CreateOutput("out", Sdf.ValueTypeNames.Token)
    surface_shader_output = surface_shader.CreateOutput("out", Sdf.ValueTypeNames.Token)

    # add displacement
    displacement_shader = UsdShade.Shader.Define(stage, f"{mat_path}/mtlxdisplacement")
    displacement_shader.CreateIdAttr("ND_displacement_float")
    displacement_shader_output = displacement_shader.CreateOutput("out", Sdf.ValueTypeNames.Token)

    # if textures -> replacing default values with textures
    for parm_name, tex_path in parms_mapping.items():
        uv_tex = UsdShade.Shader.Define(stage, f"{mat_path}/mtlx_{parm_name}")
        uv_tex.CreateIdAttr("ND_UsdUVTexture")
        uv_tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(str(tex_path)))
        uv_tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
        rgb_output = uv_tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
        surface_shader.CreateInput("base_color", Sdf.ValueTypeNames.Float3).ConnectToSource(rgb_output)
        # Material outputs connecting to shader outputs

    mat.CreateOutput("mtlx:surface", Sdf.ValueTypeNames.Token).ConnectToSource(surface_shader_output)
    mat.CreateOutput("mtlx:displacement", Sdf.ValueTypeNames.Token).ConnectToSource(displacement_shader_output)
    mat.CreateSurfaceOutput().ConnectToSource(surface_shader_output)
    return print(f"Material populated: {mat_path}")
