# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Horde3DSceneExporter",
    "author" : "creutzerb",
    "description" : "export blender scene to be used with horde3D",
    "blender" : (2, 83, 0),
    "version" : (0, 0, 1),
    "location" : "View_3D",
    "warning" : "",
    "category" : "Generic"
}

import bpy

from bpy.props import (BoolProperty, StringProperty,
                       PointerProperty,
                       )

from bpy.types import (Panel,
                       Operator,
                       AddonPreferences,
                       PropertyGroup,
                       )

class MyProperties(PropertyGroup):

    path : StringProperty(
        name="",
        description="Path to Directory",
        default="",
        maxlen=1024,
        subtype='DIR_PATH')
    is_anim : BoolProperty()
    overwrite_mat : BoolProperty()
    is_seam : BoolProperty()

from . test_op import Test_OT_Operator
from . export_geo_op import GEO_OT_Operator
from . test_panel import TEST_PT_Panel

classes = (TEST_PT_Panel, Test_OT_Operator, GEO_OT_Operator, MyProperties)

# register, unregister = bpy.utils.register_classes_factory(classes)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool

if __name__ == "__init__":
    register()
