import bpy

import os
import shutil
from pathlib import Path

# get currntly selected obj : C.object

class GEO_OT_Operator(bpy.types.Operator):
    bl_idname = "view3d.export_geo"
    bl_label = "Simple operator"
    bl_description = "export to collada and use collada converter"

    def execute(self, context):
        
        res_path = "/home/creutzerb/Dev/horde3D/aaa_horde2_sample/Content/scenes/"
        clean_path = bpy.path.abspath(context.scene.my_tool.path) + "/"

        # print(context.scene.my_tool.path)

        if context.scene.my_tool.is_seam:


            obj = bpy.context.object

            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(obj.data)
                vertices = bm.verts

            else:
                vertices = obj.data.vertices

            verts = [obj.matrix_world @ vert.co for vert in vertices] 
            plain_verts = [vert.to_tuple() for vert in verts]

            seamVert = []
            for vert in plain_verts:
                seamVert += "{:.6f}".format(-vert[0]) + "," + "{:.6f}".format(vert[2]) + "," + "{:.6f}".format(-vert[1]) + "\n"
                
            vert_csv = open(clean_path + obj.name + "_seam.csv","w")
            vert_csv.writelines(seamVert)
            vert_csv.close()


        else:

            # clean_path = context.scene.my_tool.path[2:]
            
            temp_path = "/tmp/h3dConv/"

            object_name = bpy.context.view_layer.objects.active.name

            # create a folder
            if Path(temp_path).is_dir():
                shutil.rmtree(temp_path)
            os.mkdir(temp_path)

            

            # export selected object to collada inside /tmp/h3d_tmp/
            bpy.ops.wm.collada_export(
                filepath= temp_path + object_name +".dae", 
                check_existing=False, 
                filter_blender=False, 
                filter_image=False, 
                filter_movie=False, 
                filter_python=False, 
                filter_font=False, 
                filter_sound=False, 
                filter_text=False, 
                filter_btx=False, 
                filter_collada=True, 
                filter_folder=True, 
                filemode=8,
                selected=True,
                include_armatures =True,
                include_animations=True,
                include_all_actions=False,
                apply_modifiers=False,
                include_children=True)

            # use collada convert
            cmd = "/home/creutzerb/Dev/horde3D/Horde3D_2/build/Binaries/Linux/Release/ColladaConv "+ temp_path + object_name +".dae -dest " + temp_path
            if context.scene.my_tool.is_anim:
                cmd += " -type anim"
            if context.scene.my_tool.overwrite_mat:
                cmd += " -overwriteMats"
            os.system(cmd)
    
            # copy geo to path
            if context.scene.my_tool.is_anim:
                shutil.copyfile(temp_path + object_name +".anim", clean_path + object_name +".anim")
            else:
                shutil.copyfile(temp_path + object_name +".geo", clean_path + object_name +".geo")
                shutil.copyfile(temp_path + object_name +".scene.xml", clean_path + object_name + ".scene.xml")

            # delete /tmp/h3d_tmp/
            shutil.rmtree(temp_path)


        return {'FINISHED'}