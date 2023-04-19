# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#   https://github.com/Korchy/blender_alpha_quad_279

import bpy


from bpy.props import (
        FloatProperty,
        IntProperty,
        BoolProperty,
        EnumProperty,
        )


#from . import helper
from . import alpha_quad
#from . import gui
from . import alpha_quad_ui

bl_info = {
    "name": "Alpha Quad",
    "description": "Quad retopology tool for selected faces",
    "author": "Kushiro",
    "version": (1, 2, 0),
    "blender": (2, 83, 0),
    "location": "View3D > Edit > Context Menu (right click)",
    "category": "Mesh",
}



def menu_func(self, context):
    self.layout.operator_context = "INVOKE_DEFAULT";
    self.layout.operator(alpha_quad.AlphaQuadOperator.bl_idname)

def register():    
    alpha_quad_ui.register()

    importlib.reload(alpha_quad)
    # importlib.reload(gui)
    
    bpy.utils.register_class(alpha_quad.AlphaQuadOperator)
    # bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(menu_func)
    #bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)    


def unregister():
    #bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)
    # bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func)
    # bpy.utils.unregister_class(alpha_quad.SDModelerOperator)
    alpha_quad_ui.unregister()

    
if __name__ == "__main__":    
    register()

import importlib

def test():    
    #importlib.reload(helper)    
    
    try:
        unregister()
    except :
        pass
    
    try:
        register()
    except :
        pass
    
    print('test loaded')


