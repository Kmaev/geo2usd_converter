import os
import shutil
from pathlib import Path

from pxr import Usd, UsdGeom, UsdShade, Kind, Sdf, UsdUtils

from usd_indie_pipe.asset_resolve import LayerReplacer
from usd_indie_pipe.texture_resolve import TextureResolve


def create_and_bind_materials(usd_stage: str, materials: list, tex_folder_path: str) -> Usd.Prim:
    """
     Creates a material library and assigns materials to geometry.

    If primitive has subsets for each material name in materials, this function defines a MaterialX, populates it
    with shader parameters and texture connections, and binds it to the corresponding geometry.

    If subsets are not present, binding is done per-mesh
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
    Traverses the USD stage and collects all subsets prims.
    """
    subsets = []
    for prim in stage.Traverse():
        if not prim.IsValid() or not prim.IsDefined():
            continue
        if prim.GetTypeName() == "GeomSubset":
            subsets.append(prim)
    return subsets


def solve_texture(usd_file: str, namespace: str, tex_folder_path: str) -> dict:
    """
    Resolves texture file paths using the TextureResolve class.
    """
    tex_resolve = TextureResolve(usd_file, namespace, tex_folder_path)
    tex_resolve.geometry_file = usd_file
    tex_resolve.namespace = namespace
    tex_resolve.tex_folder_path = tex_folder_path
    mapping = dict(tex_resolve.parse_texture())
    return mapping


def run_material_assignment(usd_file: str, tex_folder_path: str) -> None:
    """
    Runs material creation and assignment for a USD stage.
    This function gathers all geometry subsets, determines material names,
    and calls the material creation and binding pipeline.
    """
    stage = Usd.Stage.Open(usd_file)
    subc = get_subsets(stage)
    mat_lis = [s.GetName() for s in subc]
    create_and_bind_materials(usd_file, mat_lis, tex_folder_path)


def populate_mtlx(stage: Usd.Stage, mat: Usd.Prim, parms_mapping: dict) -> None:
    """
    Populates a materialX surface and displacement shader with default parameters and textures.
    For each texture entry in the parameter mapping, a UsdUVTexture is created and
    connected to the corresponding input on either the surface or displacement shader.
    """

    mat_path = mat.GetPath()

    # Init Mtlx standart surface shader
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

        print(f"CREATED TEXTURE {parm_name} : {tex_path}")

    # Connection to materila output
    mat.CreateOutput("mtlx:surface", Sdf.ValueTypeNames.Token).ConnectToSource(surface_shader_output)
    mat.CreateOutput("mtlx:displacement", Sdf.ValueTypeNames.Token).ConnectToSource(displacement_shader_output)
    mat.CreateOutput("surface", Sdf.ValueTypeNames.Token).ConnectToSource(preview_output)
    mat.CreateSurfaceOutput().ConnectToSource(surface_shader_output)

    print(f"MATERIAL POPULATED: {mat_path}")


# __________________________________________________
# ASSET RESOLVE
"""
All asset resolve paths are in active development; the workflow and asset handling are still being defined.
"""


def get_version(path: str):
    """
    Temp version handling.
    """
    usd_file_path = Path(path)
    version = usd_file_path.parent.name.strip("v")
    return version


def version_up(stage_path: str):
    """
    Increase the version of usd stage
    """
    version = get_version(stage_path)
    new_version = str(int(version) + 1).zfill(len(version))
    return new_version


def create_versioned_up_file_copy(stage_path: str):
    """
    Creates a versioned-up copy of the usd stage. This version of the file will be adjusted based on the latest
    updates to its dependencies
    """
    old_version = get_version(stage_path)
    new_version = version_up(old_version)
    new_stage_path = Path(stage_path.replace(old_version, new_version))
    orig_stage_path = Path(stage_path)
    new_version_dir = new_stage_path.parent

    if not new_version_dir.exists():
        os.makedirs(new_version_dir)

    shutil.copy(orig_stage_path, new_stage_path)
    return str(new_stage_path)


def parse_shot_manifest(stage_path: str, old_path: str, new_path: str):
    """
    Handles adjustments to the dependencies in the USD stage.
    """
    new_stage_path = create_versioned_up_file_copy(stage_path)
    stage = Usd.Stage.Open(new_stage_path)
    root_layer = stage.GetRootLayer()
    layers = root_layer.subLayerPaths

    if old_path in layers:
        UsdUtils.ModifyAssetPaths(
            root_layer,
            LayerReplacer(
                old_path=old_path,
                new_path=new_path,
            ),
        )
        stage.Save()


# __________________________________________________
# USD STAGE LOADING AND PUBLISING


def get_layer_composition(stage_path: str):
    """
    Returns all dependencies of the usd stage.
    """
    stage = Usd.Stage.Open(stage_path)
    usd_layer = stage.GetRootLayer()
    all_layers, _, _ = UsdUtils.ComputeAllDependencies(usd_layer.identifier)
    layers = []
    for layer in all_layers:
        layers.append(layer.identifier)
    return layers
