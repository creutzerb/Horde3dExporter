import bpy

class TEST_PT_Panel(bpy.types.Panel):
    bl_idname = "TEST_PT_Panel"
    bl_label = "Horde3D exporter"
    bl_category = "Horde3D"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        scn = context.scene

        row = layout.row()
        row.operator('view3d.cursor_center', text="export scene")
        row2 = layout.row()
        row2.label(text="Export folder:")


        row3 = layout.row()
        row3.operator('view3d.export_geo', text="export geo")


        col = layout.column(align=True)
        col.prop(scn.my_tool, "path", text="")

        col.prop(scn.my_tool, "is_anim", text="is_anim")
        col.prop(scn.my_tool, "overwrite_mat", text="overwrite_mat")
        col.prop(scn.my_tool, "is_seam", text="is_SEAM")
