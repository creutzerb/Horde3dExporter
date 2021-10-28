import bpy
import bmesh
import math
from pathlib import Path
import os

# get currntly selected obj : C.object

class Test_OT_Operator(bpy.types.Operator):
    bl_idname = "view3d.cursor_center"
    bl_label = "Simple operator"
    bl_description = "Center 3D cursor"

    def execute(self, context):
        
        res_path = "/home/creutzerb/Dev/horde3D/aaa_horde2_orcNgob/Content/rooms/"
        scene_name = bpy.path.basename(bpy.context.blend_data.filepath)[:-6]

        if not Path(res_path + scene_name).is_dir():
            os.mkdir(res_path + scene_name)
        
        ## contains the info about the various static scenes
        scene_xml = []
        scene_xml += "<!DOCTYPE HordeSceneGraph>\n"
        scene_xml += "<Group name=\"" + scene_name + "\">\n"

        ## contains the lights
        light_xml = []
        light_xml += "<!DOCTYPE HordeSceneGraph>\n"

        nav_xml = []
        nav_xml += "<!DOCTYPE HordeSceneGraph>\n"
        nav_xml += "<Group name=\"" + scene_name + "nav\">\n"

        for col in context.scene.collection.children:
            if col.name.startswith("export:sta"):

                for sub_col in col.children:

                    sub_xml = []
                    sub_xml += "<!DOCTYPE HordeSceneGraph>\n"
                    sub_xml += "<Group name=\"" + scene_name + sub_col.name + "\">\n"

                    static_nodes = "     <Group"
                    static_nodes += " name=\"static\""
                    static_nodes += " tx=\"0.0\" ty=\"0.0\" tz=\"0.0\">\n"
                    sub_xml += static_nodes

                    xmin = 9999.0
                    xmax = -9999.0
                    ymin = 9999.0
                    ymax = -9999.0


                    for obj in sub_col.objects:

                        if obj.name.startswith("aa_b"):
                            # reprensented by 4 vertices in blender
                            if obj.mode == 'EDIT':
                                bm = bmesh.from_edit_mesh(obj.data)
                                vertices = bm.verts

                            else:
                                vertices = obj.data.vertices

                            verts = [obj.matrix_world @ vert.co for vert in vertices] 

                            # coordinates as tuples
                            plain_verts = [vert.to_tuple() for vert in verts]
  
                            # loop over 1 vertices to find extremum
                            for vert in plain_verts:
                                if vert[0] < xmin:
                                    xmin = vert[0]
                                if vert[0] > xmax:
                                    xmax = vert[0]

                                if vert[1] < ymin:
                                    ymin = vert[1]
                                if vert[1] > ymax:
                                    ymax = vert[1]
                                    
                            # not a real object
                            continue

                        # C.object["prop"]
                        output = "        <Reference sceneGraph=\"models/" + obj["prop"] + "/" + obj["prop"] + ".scene.xml\""

                        # not very good aabb - might be enough
                        if obj.location.x < xmin:
                            xmin = obj.location.x
                        if obj.location.x + obj.dimensions.x > xmax:
                            xmax = obj.location.x + obj.dimensions.x

                        if obj.location.y < ymin:
                            ymin = obj.location.y
                        if obj.location.y + obj.dimensions.y > ymax:
                            ymax = obj.location.y + obj.dimensions.y

                        # name
                        output += " name=\"" + obj.name + "\""
                        
                        # spacial location : swap y and z
                        # X-axis is inverted
                        t = obj.location
                        output += " tx=\"" + "{:.5f}".format(-t.x) + "\""
                        output += " ty=\"" + "{:.5f}".format(t.z) + "\""
                        output += " tz=\"" + "{:.5f}".format(t.y) + "\""
                        
                        r = obj.rotation_euler
                        output += " rx=\"" + "{:.5f}".format((-r.x * 180.0 / math.pi)%360.0) + "\""
                        output += " ry=\"" + "{:.5f}".format((r.z * 180.0 / math.pi + 180.0)%360.0)  + "\""
                        output += " rz=\"" + "{:.5f}".format((r.y * 180.0 / math.pi)%360.0)  + "\""
                        
                        s = obj.scale
                        output += " sx=\"" + "{:.5f}".format(s.x) + "\""
                        output += " sy=\"" + "{:.5f}".format(s.z) + "\""
                        output += " sz=\"" + "{:.5f}".format(s.y) + "\""
                        
                        output += "/>\n"

                        sub_xml += output
                
                    sub_xml += "    </Group>\n"

                    sub_xml += "</Group>\n"
                    file_sub_xml = open(res_path + scene_name + "/" + scene_name + "_" + sub_col.name + ".scene.xml","w")
                    file_sub_xml.writelines(sub_xml)
                    file_sub_xml.close()

                    sub_info = []
                    sub_info = "    <Sub"
                    sub_info += " xmin=\"" + "{:.5f}".format(-xmax) + "\""
                    sub_info += " xmax=\"" + "{:.5f}".format(-xmin) + "\""
                    sub_info += " zmin=\"" + "{:.5f}".format(ymin) + "\""
                    sub_info += " zmax=\"" + "{:.5f}".format(ymax) + "\""
                    sub_info += ">\n"

                    for elem in sub_col["prop"]:
                        sub_info += "        <Visu id=\"" + str(elem) + "\"/>\n"

                    sub_info += "    </Sub>\n"

                    scene_xml += sub_info


            elif col.name.startswith("export:nav"):

                ## array of unique vertices
                # 1 vertex = [x,y,z] (floats)
                verts = []

                ## array of triangles
                # 1 triangle = [vertA, vertB, vertC, AB, BC, CA, convexInd] (+temp) [modA, modB, modC]
                # vertA : reference element of verts[]
                # AB : index of other convex shape sharing this side (+ 2 special cases)
                # (-1) means undefined yet => still (-1) on export means nobody shares this side
                # (-2) means it's shared with another triangle of this convex shape
                tri = []

                convexInd = -1

                for obj in col.objects:

                    convexInd += 1

                    triangle_list = []

                    # each object represents a convex mesh
                    data = obj.data

                    # for now get the references to the triangles of this convex shape - non unique
                    sample_start = len(tri)# going to replace the indices of this sample later

                    for face in data.polygons:
                        tri.append([face.vertices[0], face.vertices[1], face.vertices[2], -1, -1, -1, convexInd, True, True, True ])
                        triangle_list.append(len(tri) -1)


                    # VERTICES
                    # all the vertices [x,y,z] of the convex shape
                    for v in range(len(data.vertices)):
                        # convert to horde coordinate system
                        pos = [-data.vertices[v].co[0], data.vertices[v].co[2], data.vertices[v].co[1]]

                        # check is that one already exists
                        found = False
                        found_pos = 0
                        for u in range(len(verts)):
                            if abs(verts[u][0] - pos[0]) < 0.0001 and abs(verts[u][1]-pos[1]) < 0.0001 and abs(verts[u][2]-pos[2]) < 0.0001:
                                found = True
                                found_pos = u
                                break

                        if (not found):
                            found_pos = len(verts)
                            verts.append(pos)
                            

                        # replace index in  recently added triangles
                        for i in range(sample_start, len(tri)):
                            for j in range(3):
                                if tri[i][j+7] and tri[i][j] == v:
                                    tri[i][j] = found_pos
                                    tri[i][j+7] = False
                                    # print("in convex:" + str(convexInd) + "  replace tri:" + str(i) + "  vert:" + str(j) + "  from:" + str(v) + "  to:" + str(found_pos) + " found:" + str(found))

                

                # verts tri and conv have been filled
                # need to update neighbor information
                for triangle in tri:
                    for versus in tri:

                        # if the triangle you check against is further than this one in the conv list
                        if versus[6] >= triangle[6] and triangle != versus:

                            if (triangle[0] == versus[0] and triangle[1] == versus[1]) or (triangle[0] == versus[1] and triangle[1] == versus[0]):
                                triangle[3] = versus[6]
                                versus[3] = triangle[6]
                            elif (triangle[0] == versus[1] and triangle[1] == versus[2]) or (triangle[0] == versus[2] and triangle[1] == versus[1]):
                                triangle[3] = versus[6]
                                versus[4] = triangle[6]
                            elif (triangle[0] == versus[2] and triangle[1] == versus[0]) or (triangle[0] == versus[0] and triangle[1] == versus[2]):
                                triangle[3] = versus[6]
                                versus[5] = triangle[6]
                            
                            if (triangle[1] == versus[0] and triangle[2] == versus[1]) or (triangle[1] == versus[1] and triangle[2] == versus[0]):
                                triangle[4] = versus[6]
                                versus[3] = triangle[6]
                            elif (triangle[1] == versus[1] and triangle[2] == versus[2]) or (triangle[1] == versus[2] and triangle[2] == versus[1]):
                                triangle[4] = versus[6]
                                versus[4] = triangle[6]
                            elif (triangle[1] == versus[2] and triangle[2] == versus[0]) or (triangle[1] == versus[0] and triangle[2] == versus[2]):
                                triangle[4] = versus[6]
                                versus[5] = triangle[6]

                            if (triangle[2] == versus[0] and triangle[0] == versus[1]) or (triangle[2] == versus[1] and triangle[0] == versus[0]):
                                triangle[5] = versus[6]
                                versus[3] = triangle[6]
                            elif (triangle[2] == versus[1] and triangle[0] == versus[2]) or (triangle[2] == versus[2] and triangle[0] == versus[1]):
                                triangle[5] = versus[6]
                                versus[4] = triangle[6]
                            elif (triangle[2] == versus[2] and triangle[0] == versus[0]) or (triangle[2] == versus[0] and triangle[0] == versus[2]):
                                triangle[5] = versus[6]
                                versus[5] = triangle[6]
                
                # triangle with neighbor within same shape were also added
                # we want to differentiate internal sides from sides leading to nothing
                for triangle in tri:
                    if triangle[3] == triangle[6]:
                        triangle[3] = -2
                    if triangle[4] == triangle[6]:
                        triangle[4] = -2
                    if triangle[5] == triangle[6]:
                        triangle[5] = -2

                    
                # export
                unique_str = []
                for i in verts:
                    unique_str += "{:.6f}".format(i[0]) + "," + "{:.6f}".format(i[1]) + "," + "{:.6f}".format(i[2]) + "\n"
                
                vert_csv = open(res_path + scene_name + "/" + scene_name + "_unique.csv","w")
                vert_csv.writelines(unique_str)
                vert_csv.close()
                
                tris_str = []
                for i in tri:
                    tris_str += str(i[0]) + "," + str(i[1]) + "," + str(i[2]) + ","
                    tris_str += str(i[3]) + "," + str(i[4]) + "," + str(i[5]) + "," 
                    tris_str += str(i[6]) +"\n"
                
                vert_csv = open(res_path + scene_name + "/" + scene_name + "_tris.csv","w")
                vert_csv.writelines(tris_str)
                vert_csv.close()


            elif col.name.startswith("export:light"):
                # for obj in col.objects:
                #     print(obj.name)
 
                lights = "<Group"
                lights += " name=\"lights\""
                lights += " tx=\"0.0\" ty=\"0.0\" tz=\"0.0\">\n"
                light_xml += lights

                for obj in col.objects:

                    output = "    <Light"

                    # self.report({'INFO'}, 'content: ' + str(dir(obj.arm_propertylist[0])))

                    # name
                    output += " name=\"" + obj.name + "\""

                    output += " lightingContext=\"LIGHTING\""
                    output += " shadowContext=\"SHADOWMAP\""
                    output += " fov=\"89\""
                    output += " shadowMapBias=\"0.005\""
                    output += " shadowMapCount=\"1\""
                    output += " shadowSplitLambda=\"0\""
                    output += " material=\"materials/light.material.xml\""

                    light_data = obj.data
                    
                    output += " radius=\"" + str(25.0) + "\""
                    output += " colMult=\"" + str(light_data.energy/30000) + "\""
                    output += " col_R=\"" + str(light_data.color[0]) + "\""
                    output += " col_G=\"" + str(light_data.color[1]) + "\""
                    output += " col_B=\"" + str(light_data.color[2]) + "\""

                    # spacial location : swap y and z
                    # X-axis is inverted
                    t = obj.location
                    output += " tx=\"" + "{:.5f}".format(-t.x) + "\""
                    output += " ty=\"" + "{:.5f}".format(t.z) + "\""
                    output += " tz=\"" + "{:.5f}".format(t.y) + "\""
                    
                    r = obj.rotation_euler
                    # output += " rx=\"" + "{:.5f}".format((-r.x * 180.0 / math.pi)%360.0) + "\""
                    # output += " ry=\"" + "{:.5f}".format((r.z * 180.0 / math.pi + 180.0)%360.0)  + "\""
                    # output += " rz=\"" + "{:.5f}".format((r.y * 180.0 / math.pi)%360.0)  + "\""
                    
                    # in horde3D lights are oriented toward x+ 
                    horde3D_rx = r.x + math.pi/2
                    output += " rx=\"" + "{:.5f}".format((-horde3D_rx * 180.0 / math.pi)%360.0) + "\""
                    output += " ry=\"" + "{:.5f}".format((r.z * 180.0 / math.pi)%360.0)  + "\""

                    # don't use the y rotation in blender : doesn't work here
                    #output += " rz=\"" + "{:.5f}".format((r.y * 180.0 / math.pi)%360.0)  + "\""
                    
                    output += "/>\n"

                    light_xml += output
            
                light_xml += "</Group>\n"

            elif col.name.startswith("export:path"):
                # for obj in col.objects:
                #     print(obj.name)
                #     for child in obj.children:
                #         print("     " + child.name)

                for obj in col.objects:

                    area = "    <Area"
                    area += " name=\"" + obj.name + "\""
                    area += ">\n"

                    # t = obj.location
                    # output += " tx=\"" + "{:.5f}".format(-t.x) + "\""
                    # output += " ty=\"" + "{:.5f}".format(t.z) + "\""
                    # output += " tz=\"" + "{:.5f}".format(t.y) + "\""

                    nav_xml += area

                    for child in obj.children:

                        output = "        <Obstacle"

                        # name
                        output += " name=\"" + child.name + "\""

                        # spacial location : swap y and z
                        # X-axis is inverted
                        t = child.location
                        output += " tx=\"" + "{:.5f}".format(-t.x) + "\""
                        output += " tz=\"" + "{:.5f}".format(t.y) + "\""

                        s = child.scale
                        output += " radius=\"" + "{:.5f}".format(s.x) + "\""
                        
                        output += "/>\n"

                        nav_xml += output
                
                    nav_xml += "    </Area>\n"
            
            elif col.name.startswith("export:colli_box"):
                for obj in col.objects:

                    box = "    <Box"
                    box += " name=\"" + obj.name + "\""
                    # box += " area_1=\"" + str(obj.arm_propertylist[0].integer_prop) + "\""
                    box += ">\n"
                    nav_xml += box

                    # reprensented by 8 vertices in blender
                    # reprensented by xmin xmax ymin ymax zmin zmax in custom collision system
                    if obj.mode == 'EDIT':
                        bm = bmesh.from_edit_mesh(obj.data)
                        vertices = bm.verts

                    else:
                        vertices = obj.data.vertices

                    verts = [obj.matrix_world @ vert.co for vert in vertices] 

                    # coordinates as tuples
                    plain_verts = [vert.to_tuple() for vert in verts]

                    # initialize - so that first found can only replace default value
                    xmin = 1000.0
                    xmax = -1000.0
                    ymin = 1000.0
                    ymax = -1000.0
                    zmin = 1000.0
                    zmax = -1000.0

                    # loop over 8 vertices to find extremum
                    for vert in plain_verts:
                        if vert[0] < xmin:
                            xmin = vert[0]
                        if vert[0] > xmax:
                            xmax = vert[0]
                        
                        if vert[1] < ymin:
                            ymin = vert[1]
                        if vert[1] > ymax:
                            ymax = vert[1]
                        
                        if vert[2] < zmin:
                            zmin = vert[2]
                        if vert[2] > zmax:
                            zmax = vert[2]

                    # spacial location : swap y and z
                    # X-axis is inverted
                    output = "        <X"
                    output += " min=\"" + "{:.5f}".format(-xmax) + "\""
                    output += " max=\"" + "{:.5f}".format(-xmin) + "\""
                    output += "/>\n"
                    nav_xml += output

                    output = "        <Y"
                    output += " min=\"" + "{:.5f}".format(zmin) + "\""
                    output += " max=\"" + "{:.5f}".format(zmax) + "\""
                    output += "/>\n"
                    nav_xml += output

                    output = "        <Z"
                    output += " min=\"" + "{:.5f}".format(ymin) + "\""
                    output += " max=\"" + "{:.5f}".format(ymax) + "\""
                    output += "/>\n"
                    nav_xml += output
            
                    nav_xml += "    </Box>\n"
            elif col.name.startswith("export:colli_ramp"):
                for obj in col.objects:

                    # a pathway between 2 areas
                    box = "    <Ramp"
                    box += " name=\"" + obj.name + "\""

                    # reprensented by 4 vertices in blender
                    # reprensented by xmin xmax ymin ymax zmin zmax in custom collision system
                    if obj.mode == 'EDIT':
                        bm = bmesh.from_edit_mesh(obj.data)
                        vertices = bm.verts

                    else:
                        vertices = obj.data.vertices

                    verts = [obj.matrix_world @ vert.co for vert in vertices] 

                    # coordinates as tuples
                    plain_verts = [vert.to_tuple() for vert in verts]

                    # initialize - so that first found can only replace default value
                    xmin = 1000.0
                    xmax = -1000.0
                    ymin = 1000.0
                    ymax = -1000.0
                    zmin = 1000.0
                    zmax = -1000.0

                    # loop over 4 vertices to find extremum
                    for vert in plain_verts:
                        if vert[0] < xmin:
                            xmin = vert[0]
                        if vert[0] > xmax:
                            xmax = vert[0]
                        
                        if vert[1] < ymin:
                            ymin = vert[1]
                        if vert[1] > ymax:
                            ymax = vert[1]
                        
                        if vert[2] < zmin:
                            zmin = vert[2]
                        if vert[2] > zmax:
                            zmax = vert[2]

                    #compare to avg to know orientation
                    xavg = 0.5 * (xmin + xmax) 
                    yavg = 0.5 * (ymin + ymax)
                    zavg = 0.5 * (zmin + zmax)

                    #lower point count
                    low_xmin = 0
                    low_xmax = 0
                    low_ymin = 0
                    low_ymax = 0

                    # loop over 4 vertices to find orientation
                    for vert in plain_verts:
                        if vert[2] < zavg:
                            if vert[0] < xavg:
                                low_xmin += 1
                            else:
                                low_xmax += 1

                            if vert[1] < yavg:
                                low_ymin += 1
                            else:
                                low_ymax += 1
                    
                    if low_xmin == 2:
                        box += " low_side=\"xmax\""
                    elif low_xmax == 2:
                        box += " low_side=\"xmin\""
                    elif low_ymin == 2:
                        box += " low_side=\"zmin\""
                    else:
                        box += " low_side=\"zmax\""

                    box += ">\n"
                    nav_xml += box

                    # spacial location : swap y and z
                    # X-axis is inverted
                    output = "        <X"
                    output += " min=\"" + "{:.5f}".format(-xmax) + "\""
                    output += " max=\"" + "{:.5f}".format(-xmin) + "\""
                    output += "/>\n"
                    nav_xml += output

                    output = "        <Y"
                    output += " min=\"" + "{:.5f}".format(zmin) + "\""
                    output += " max=\"" + "{:.5f}".format(zmax) + "\""
                    output += "/>\n"
                    nav_xml += output

                    output = "        <Z"
                    output += " min=\"" + "{:.5f}".format(ymin) + "\""
                    output += " max=\"" + "{:.5f}".format(ymax) + "\""
                    output += "/>\n"
                    nav_xml += output
            
                    nav_xml += "    </Ramp>\n"
            elif col.name.startswith("export:game"):

                # property "prop" : type of object
                # 0 = exit area
                #       room : what's next room
                #       spawn : index of destination area in room

                for obj in col.objects:

                    if obj["prop"] == 0:

                        # area type 0 : exit area
                        box = "    <AREA"
                        box += " name=\"" + obj.name + "\""
                        box += " type=\"0\""
                        box += " room=\"" + str(obj["room"]) + "\""
                        box += " spawn=\"" + str(obj["spawn"]) + "\""

                        r = obj.rotation_euler
                        # default rotation toward x+
                        box += " ry=\"" + "{:.5f}".format(r.z) + "\""

                        box += ">\n"
                        nav_xml += box

                        # reprensented by 8 vertices in blender
                        # reprensented by xmin xmax ymin ymax zmin zmax in custom collision system
                        if obj.mode == 'EDIT':
                            bm = bmesh.from_edit_mesh(obj.data)
                            vertices = bm.verts

                        else:
                            vertices = obj.data.vertices

                        verts = [obj.matrix_world @ vert.co for vert in vertices] 

                        # coordinates as tuples
                        plain_verts = [vert.to_tuple() for vert in verts]

                        # initialize - so that first found can only replace default value
                        xmin = 1000.0
                        xmax = -1000.0
                        ymin = 1000.0
                        ymax = -1000.0
                        zmin = 1000.0
                        zmax = -1000.0

                        # loop over 8 vertices to find extremum
                        for vert in plain_verts:
                            if vert[0] < xmin:
                                xmin = vert[0]
                            if vert[0] > xmax:
                                xmax = vert[0]
                            
                            if vert[1] < ymin:
                                ymin = vert[1]
                            if vert[1] > ymax:
                                ymax = vert[1]
                            
                            if vert[2] < zmin:
                                zmin = vert[2]
                            if vert[2] > zmax:
                                zmax = vert[2]

                        # spacial location : swap y and z
                        # X-axis is inverted
                        output = "        <X"
                        output += " min=\"" + "{:.5f}".format(-xmax) + "\""
                        output += " max=\"" + "{:.5f}".format(-xmin) + "\""
                        output += "/>\n"
                        nav_xml += output

                        output = "        <Y"
                        output += " min=\"" + "{:.5f}".format(zmin) + "\""
                        output += " max=\"" + "{:.5f}".format(zmax) + "\""
                        output += "/>\n"
                        nav_xml += output

                        output = "        <Z"
                        output += " min=\"" + "{:.5f}".format(ymin) + "\""
                        output += " max=\"" + "{:.5f}".format(ymax) + "\""
                        output += "/>\n"
                        nav_xml += output
                
                        nav_xml += "    </AREA>\n"

                    elif obj["prop"] == 1:
                        # DISABLED ######################################################### DISABLED
                        continue

                        output = "    <Spawn"
                        output += " name=\"" + obj.name + "\""

                        # spacial location : swap y and z
                        # X-axis is inverted
                        t = obj.location
                        output += " tx=\"" + "{:.5f}".format(-t.x) + "\""
                        output += " tz=\"" + "{:.5f}".format(t.y) + "\""

                        r = obj.rotation_euler
                        output += " ry=\"" + "{:.5f}".format((r.z * 180.0 / math.pi + 180.0)%360.0)  + "\""

                        output += "/>\n"
                        nav_xml += output


        scene_xml += "</Group>\n"
        nav_xml += "</Group>\n"

        scene_xml_file = open(res_path + scene_name + "/" + scene_name + ".scene.xml","w")
        scene_xml_file.writelines(scene_xml)
        scene_xml_file.close()

        light_xml_file = open(res_path + scene_name + "/" + scene_name + "light.scene.xml","w")
        light_xml_file.writelines(light_xml)
        light_xml_file.close()

        nav_xml_file = open(res_path + scene_name + "/" + scene_name + ".nav.xml","w")
        nav_xml_file.writelines(nav_xml)
        nav_xml_file.close()

        print("DONE exporting")


        return {'FINISHED'}