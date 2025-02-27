bl_info = {
    "name": "xtreme byte MAP Tool",
    "blender": (2, 80, 0),
    "category": "Import-Export",
    "author": "xtreme byte",
    "version": (1, 1, 0),
    "location": "View3D > N-Panel > GTA SA IPL",
    "description": "Imports GTA SA IPL files with correct coordinates.",
}

from .gta_sa_ipl_importer import register, unregister

if "bpy" in locals():
    import importlib
    importlib.reload(gta_sa_ipl_importer)
