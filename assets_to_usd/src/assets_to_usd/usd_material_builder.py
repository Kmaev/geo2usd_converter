import logging

from assets_to_usd.texture_resolve import TextureResolve
from pxr import Usd, UsdGeom, UsdShade, Kind, Sdf

logger = logging.getLogger(__name__)


def create_and_bind_materials(usd_stage: str, materials: list, tex_folder_path: str) -> Usd.Prim:
    """
    Create materials and bind them to geometry.

    Args:
        usd_stage: USD file path.
        materials: Material names.
        tex_folder_path: Texture folder path.
    """
    stage = Usd.Stage.Open(usd_stage)
    subsets = get_subsets(stage)
    for prim in stage.Traverse():
        if not prim.IsValid() or not prim.IsDefined():
            continue
        if Usd.ModelAPI(prim).GetKind() == Kind.Tokens.component:
            mat_lib_path = prim.GetPath().AppendPath("materials")
            mat_lib = stage.DefinePrim(mat_lib_path, "Scope")
            if subsets:
                for mat in materials:
                    mat_path = mat_lib_path.AppendPath(mat)

                    mat_prim = UsdShade.Material.Define(stage, mat_path)
                    for sub_prim in subsets:
                        gprim = stage.GetPrimAtPath(sub_prim.GetPath().GetParentPath())
                        if gprim.IsA(UsdGeom.Gprim):
                            gprim = UsdGeom.Gprim(gprim)
                            gprim.CreateDisplayColorAttr().Set([(0.8, 0.8, 0.8)])
                            gprim.CreateDisplayOpacityAttr().Set([1.0])

                        tex_name = sub_prim.GetName()

                        if mat == tex_name:
                            UsdShade.MaterialBindingAPI.Apply(sub_prim).Bind(mat_prim)
                            attr = sub_prim.GetAttribute("familyName")
                            attr.Set("materialBind")

                            mapping = solve_texture(usd_stage, tex_name, tex_folder_path)
                            populate_mtlx(stage, mat_prim, mapping)

            else:
                for child in prim.GetChildren():
                    for sub_prim in Usd.PrimRange(child):
                        if sub_prim.IsA(UsdGeom.Mesh):
                            mesh_prim_name = sub_prim.GetName()
                            mat_path = mat_lib_path.AppendPath(sub_prim.GetName())
                            mat_prim = UsdShade.Material.Define(stage, mat_path)
                            UsdShade.MaterialBindingAPI.Apply(sub_prim).Bind(mat_prim)
                            mapping = solve_texture(usd_stage, mesh_prim_name, tex_folder_path)
                            populate_mtlx(stage, mat_prim, mapping)

            stage.GetRootLayer().Save()


def get_subsets(stage: Usd.Stage) -> list:
    """
    Collect geometry subsets from a stage.

    Args:
        stage: USD stage.

    Returns:
        list[Usd.Prim]: Subset prims.
    """
    subsets = []
    for prim in stage.Traverse():
        if not prim.IsValid() or not prim.IsDefined():
            continue
        if prim.GetTypeName() == "GeomSubset":
            subsets.append(prim)
    return subsets


def solve_texture(usd_file: str, namespace: str, tex_folder_path: str) -> dict[str, Path]:
    """
    Resolve textures for a given namespace.

    Args:
        usd_file: USD file path.
        namespace: Geometry namespace.
        tex_folder_path: Texture folder path.

    Returns:
        dict: Texture mapping.
    """
    tex_resolve = TextureResolve(usd_file, namespace, tex_folder_path)
    tex_resolve.geometry_file = usd_file
    tex_resolve.namespace = namespace
    tex_resolve.tex_folder_path = tex_folder_path
    mapping = dict(tex_resolve.parse_texture())
    return mapping


def run_material_assignment(usd_file: str, tex_folder_path: str) -> None:
    """
    Run material assignment for a USD stage.

    Args:
        usd_file: USD file path.
         tex_folder_path: Texture folder path.
    """
    stage = Usd.Stage.Open(usd_file)
    subc = get_subsets(stage)
    mat_lis = [s.GetName() for s in subc]
    create_and_bind_materials(usd_file, mat_lis, tex_folder_path)


def populate_mtlx(stage: Usd.Stage, mat: Usd.Prim, parms_mapping: dict) -> None:
    """
    Populate MaterialX shaders and connect textures.

    Args:
        stage: USD stage.
        mat: Material prim.
        parms_mapping: Texture mapping.
    """
    mat_path = mat.GetPath()

    # Init Mtlx standard surface shader
    surface_shader = UsdShade.Shader.Define(stage, f"{mat_path}/mtlxstandard_surface")
    surface_shader.CreateIdAttr("ND_standard_surface_surfaceshader")
    surface_shader_output = surface_shader.CreateOutput("out", Sdf.ValueTypeNames.Token)

    # Init Preview shader, it will be defaulted to [0.8, 0.8, 0.8] base color
    preview_shader = UsdShade.Shader.Define(stage, f"{mat_path}/mtlxstandard_preview")
    preview_shader.CreateIdAttr("UsdPreviewSurface")
    preview_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        (0.8, 0.8, 0.8))
    preview_output = preview_shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)

    # Mtlx surface shader parms definition
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

    # Init Displacement shader
    displacement_shader = UsdShade.Shader.Define(stage, f"{mat_path}/mtlxdisplacement")
    displacement_shader.CreateIdAttr("ND_displacement_float")
    displacement_shader.CreateInput("scale", Sdf.ValueTypeNames.Float).Set(0.0001)
    displacement_shader_output = displacement_shader.CreateOutput("out", Sdf.ValueTypeNames.Token)

    # If textures available creating textures
    for parm_name, tex_path in parms_mapping.items():
        uv_tex = UsdShade.Shader.Define(stage, f"{mat_path}/mtlx_{parm_name}")
        uv_tex.CreateIdAttr("UsdUVTexture")
        uv_tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(str(tex_path)))
        uv_tex_output = uv_tex.CreateOutput("rgb", Sdf.ValueTypeNames.Color3f)

        # Shader connections
        if parm_name == "displacement":
            displacement_shader.CreateInput(parm_name, Sdf.ValueTypeNames.Float3).ConnectToSource(uv_tex_output)
        else:
            surface_shader.CreateInput(parm_name, Sdf.ValueTypeNames.Float3).ConnectToSource(uv_tex_output)

        logging.info(f"CREATED TEXTURE {parm_name} : {tex_path}")

    # Connection to materila output
    mat.CreateOutput("mtlx:surface", Sdf.ValueTypeNames.Token).ConnectToSource(surface_shader_output)
    mat.CreateOutput("mtlx:displacement", Sdf.ValueTypeNames.Token).ConnectToSource(displacement_shader_output)
    mat.CreateOutput("surface", Sdf.ValueTypeNames.Token).ConnectToSource(preview_output)
    mat.CreateSurfaceOutput().ConnectToSource(surface_shader_output)

    logging.info(f"MATERIAL POPULATED: {mat_path}")
