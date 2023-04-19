# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#   https://github.com/Korchy/blender_alpha_quad_279

import bpy
import importlib
from . import alpha_quad
from . import alpha_quad_ui

bl_info = {
    "name": "Alpha Quad",
    "description": "Quad retopology tool for selected faces",
    "author": "Kushiro, Nikita Akimov, Paul Kotelevets",
    "version": (1, 0, 0),
    "blender": (2, 79, 0),
    "location": "T-Panel - 1D - Alpha Quad",
    "category": "Mesh",
}


def register():    
    alpha_quad_ui.register()

    importlib.reload(alpha_quad)
    bpy.utils.register_class(alpha_quad.AlphaQuadOperator)


def unregister():
    alpha_quad_ui.unregister()

    
if __name__ == "__main__":    
    register()
