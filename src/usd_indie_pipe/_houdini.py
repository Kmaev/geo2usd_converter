import json
from collections import defaultdict
from pathlib import Path

import hou
from pxr import Usd, UsdGeom, Gf, Kind, Sdf

"""
This module explores one possible approach to recreating a usd file based on imported geometry.
A very low-level method.
"""


def export_houdini_geo_to_usd(geo_path: Path) -> Usd.Stage:
    """
    Recreates a usd mesh and subcomponents based on geometry data extracted from geo file.
    Builds a usd hierarchy with a component prim and material subsets.
    """
    if not geo_path.exists():
        print(f"Could not find {geo_path}")
        return None


    else:
        # In this case, the geometry file name is used as the component name to build the hierarchy in usd
        _name = geo_path.name.split(".")[0]
        usd_file = construct_usd_file_path(geo_path)
        print(f"BUILDING: {usd_file}")
        usd_stage = Usd.Stage.CreateNew(usd_file)

        # Component definition
        comp_path = Sdf.Path(f"/{_name}")
        component_prim = usd_stage.DefinePrim(comp_path, "Xform")
        Usd.ModelAPI(component_prim).SetKind(Kind.Tokens.component)

        # Xform group under the component definition
        render_geo_path = comp_path.AppendPath("geom")
        usd_stage.DefinePrim(render_geo_path, "Xform")
        # TODO add "proxy", add "materials"

        # Mesh definition
        mesh_prim_path = render_geo_path.AppendPath(_name)
        mesh = UsdGeom.Mesh.Define(usd_stage, mesh_prim_path)

        # Import all geometry data
        points, face_vertex_counts, face_vertex_indices, mat_faces, normals = get_houdini_geo_data(geo_path)

        # Usd mesh recreation
        usd_points = [Gf.Vec3f(p[0], p[1], p[2]) for p in points]
        mesh.CreatePointsAttr(usd_points)
        mesh.CreateFaceVertexCountsAttr(face_vertex_counts)
        mesh.CreateFaceVertexIndicesAttr(face_vertex_indices)

        if normals:
            usd_normals = [Gf.Vec3f(n[0], n[1], n[2]) for n in normals]
            mesh.CreateNormalsAttr(usd_normals)
            mesh.SetNormalsInterpolation("vertex")

        for mat_name, indices in mat_faces.items():
            subset_path = mesh_prim_path.AppendPath(mat_name)
            subset = UsdGeom.Subset.Define(usd_stage, subset_path)
            subset.CreateElementTypeAttr("face")
            subset.CreateIndicesAttr(indices)
        usd_stage.GetRootLayer().Save()
        print(f"Exported USD file {usd_file}")

        return usd_stage


def get_houdini_geo_data(geo_path: Path) -> tuple[
    list[tuple[float, float, float]],  # points
    list[int],  # face_vertex_counts
    list[int],  # face_vertex_indices
    dict[str, list[int]],  # mat_faces
    list[tuple[float, float, float]]  # normals
]:
    """
    Extracts geometry data, points position, vertex cound and face count, material data based on shopmaterialpath
    normals data
    """
    # Create file node to import geometry and get access to geometry data
    geo_node = hou.node("/obj").createNode("geo", "convert_geo")
    file_node = geo_node.createNode("file")
    file_node.parm("file").set(str(geo_path))
    hou_geo = file_node.geometry()

    points = [point.position() for point in hou_geo.iterPoints()]

    face_vertex_counts = []
    face_vertex_indices = []
    normals = []
    # Get material data to create subsets in mesh primitive based on the materials
    mat_faces = defaultdict(list)

    for face_index, prim in enumerate(hou_geo.iterPrims()):
        verts = prim.vertices()
        face_vertex_counts.append(len(verts))
        face_vertex_indices.extend([v.point().number() for v in verts])

        mat = prim.attribValue("shop_materialpath") or "default"
        mat_name = Path(mat).name
        mat_faces[mat_name].append(face_index)

    if hou_geo.findPointAttrib("N"):
        normals = [point.attribValue("N") for point in hou_geo.iterPoints()]
    return points, face_vertex_counts, face_vertex_indices, mat_faces, normals


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
        export_houdini_geo_to_usd(file_path)


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
