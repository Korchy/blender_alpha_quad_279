# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#   https://github.com/Korchy/blender_alpha_quad_279

from bpy.types import Panel
from bpy.utils import register_class, unregister_class


class ALPHA_QUAD_PT_panel(Panel):
	bl_idname = 'ALPHA_QUAD_PT_panel'
	bl_label = 'Alpha Quad'
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
	bl_category = '1D'

	def draw(self, context):
		layout = self.layout
		self.layout.operator('mesh.alpha_quad_operator')


def register():
	register_class(ALPHA_QUAD_PT_panel)


def unregister():
	unregister_class(ALPHA_QUAD_PT_panel)
