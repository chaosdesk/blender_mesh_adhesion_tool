############################################################################
#
# adhere_object.py
#
# Copyright (C) 2018 chaosdesk
# 
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.#
#
# ##### END GPL LICENSE BLOCK #####
#
############################################################################

import bpy
import bmesh
import mathutils
from mathutils import Vector, Euler
import math


class AdhereProc():
    def __init__(self):
        pass

    def execSingleAdhesion(self, org_obj, adh_obj, offset):
        org_obj.data.update()

        # Check each mesh if one or more face is selected
        ret = self.getSelectPolyErrCheck(org_obj, adh_obj)
        if ret != 0:
            return ret

        # Get each normal vector
        vector_nor_adh = self.averageNormal(adh_obj, False)
        vector_nor_org = self.averageNormal(org_obj, True)
        
        self.applyRotation(adh_obj, vector_nor_adh, vector_nor_org)
        self.applyLocation(adh_obj, self.getGlobalCenterPoint(org_obj))
        self.applyOffset(adh_obj, offset)

        return 0

    def execMultipleAdhesion(self, org_obj, adh_obj, offset, link):
        org_obj.data.update()
        adh_obj.select = True

        # Check each mesh if one or more face is selected
        ret = self.getSelectPolyErrCheck(org_obj, adh_obj)
        if ret != 0:
            return ret

        # Get each normal vector
        vector_nor_adh = self.averageNormal(adh_obj, False)
        vector_nor_org_list = self.multiAverageNormal(org_obj, True)

        # Duplicate mesh
        sel_polynum = self.getSelectPolyNum(org_obj.data)
        adhobj_list = self.getDuplicateObjList(adh_obj, sel_polynum, link)

        org_mesh_center_list = self.getMultiGlobalCenterPoint(org_obj)
        for vector_nor_org in vector_nor_org_list:
            # Get duplicated mesh
            dup_obj = adhobj_list[0]
            adhobj_list.pop(0)

            # Get center position
            org_mesh_center = org_mesh_center_list[0]
            org_mesh_center_list.pop(0)

            self.applyRotation(dup_obj, vector_nor_adh, vector_nor_org)
            self.applyLocation(dup_obj, org_mesh_center)
            self.applyOffset(dup_obj, offset)

        return 0

    def getSelectPolyErrCheck(self, org_obj, adh_obj):
        ret = 0
        if self.getSelectPolyExist(adh_obj.data) == False:
            ret = -2
            return ret

        if self.getSelectPolyExist(org_obj.data) == False:
            ret = -1
            return ret

        return ret

    def applyRotation(self, adh_obj, vector_nor_adh, vector_nor_org):
        vector_inv_adh = vector_nor_adh * -1.0
        quat_rot = vector_inv_adh.rotation_difference(vector_nor_org)
        eul_rot = quat_rot.to_euler()
        adh_obj.rotation_euler = eul_rot

    def applyLocation(self, adh_obj, org_mesh_center):
        adh_mesh_center = self.getGlobalCenterPoint(adh_obj)
        adh_obj_center = adh_obj.location
        move_vector = (adh_obj_center[0] - adh_mesh_center[0],
                       adh_obj_center[1] - adh_mesh_center[1],
                       adh_obj_center[2] - adh_mesh_center[2])

        adh_obj.location = (org_mesh_center[0] + move_vector[0],
                            org_mesh_center[1] + move_vector[1],
                            org_mesh_center[2] + move_vector[2])

    def applyOffset(self, obj, offset):
        if offset[0] != 0.0 or offset[1] != 0.0 or offset[2] != 0.0:
            eul_rot = obj.rotation_euler
            offset_vect = Vector(offset)
            offset_vect.rotate(eul_rot)
            obj.delta_location = (offset_vect.x, offset_vect.y, offset_vect.z)

    def getBMesh(self, mesh):
        if mesh.is_editmode:
            bm = bmesh.from_edit_mesh(mesh)
        else:
            bm = bmesh.new()
            bm.from_mesh(mesh)

        return bm

    def getSelectPolyNum(self, mesh):
        num = 0
        bm = self.getBMesh(mesh)
        for face in bm.faces:
            if face.select == True:
                num += 1
        return num

    def getSelectPolyExist(self, mesh):
        select_obj_exist = False

        bm = self.getBMesh(mesh)
        for face in bm.faces:
            if face.select == True:
                select_obj_exist = True
                break
        
        return select_obj_exist

    def getDuplicateObjList(self, dup_obj, dup_num, link):
        dup_objlist = []
        active_obj = bpy.context.active_object
        select_obj = bpy.context.selected_objects

        # Argument mesh is only selected
        bpy.ops.object.mode_set(mode='OBJECT')
        for obj in select_obj:
            if obj != dup_obj:
                obj.select = False

        # duplicate
        for i in range(0, dup_num):
            bpy.ops.object.duplicate(linked=link)
            new_obj = bpy.context.selected_objects[0]
            dup_objlist.append(new_obj)

        # Restore mesh selection
        dup_objlist[-1].select = False
        for obj in select_obj:
            obj.select = True
        active_obj.select = True
        bpy.context.scene.objects.active = active_obj          
        bpy.ops.object.mode_set(mode='EDIT')

        return dup_objlist

    def getSelectedFaces(self, bm):
        select_face = []
        for face in bm.faces:
            if face.select == True:
                select_face.append(face)

        return select_face

    def averageNormal(self, obj, is_global):
        weight_norx = 0.
        weight_nory = 0.
        weight_norz = 0.
        aver_normal = None
        bm = self.getBMesh(obj.data)
        select_face = self.getSelectedFaces(bm)

        for face in select_face:
            weight_norx += face.normal.x * face.calc_area()
            weight_nory += face.normal.y * face.calc_area()
            weight_norz += face.normal.z * face.calc_area()

        aver_normal = Vector((weight_norx, weight_nory, weight_norz))
        aver_normal.normalize()

        if is_global == True:
            eul_obj_rot = obj.rotation_euler
            aver_normal.rotate(eul_obj_rot)
        
        return aver_normal

    def multiAverageNormal(self, obj, is_global):
        select_face = []
        avr_normal_list = []
        bm = self.getBMesh(obj.data)
        select_face = self.getSelectedFaces(bm)

        eul_obj_rot = obj.rotation_euler
        for face in select_face:
            aver_normal = Vector((face.normal.x, face.normal.y, face.normal.z))
            aver_normal.normalize()
            if is_global == True:
                aver_normal.rotate(eul_obj_rot)
            avr_normal_list.append(aver_normal)

        return avr_normal_list

    def applyObjInfoToVector(self, vect, obj):
        obj_loc = obj.location
        obj_rot = obj.rotation_euler
        obj_scl = obj.scale

        apply_vect = vect
        apply_vect.rotate(obj_rot)
        for i in range(0,3):
            apply_vect[i] *= obj_scl[i]
            apply_vect[i] += obj_loc[i]

        return apply_vect

    def getGlobalCenterPoint(self, obj):
        mesh_point = self.getMeshCenterPoint(obj.data)
        vect_mesh = self.applyObjInfoToVector(Vector(mesh_point), obj)

        return (vect_mesh[0], vect_mesh[1], vect_mesh[2])

    def getMultiGlobalCenterPoint(self, obj):
        multi_center_list = []
        select_face_center = []
        bm = self.getBMesh(obj.data)

        for face in bm.faces:
            if face.select == True:
                select_face_center.append(face.calc_center_median())

        for face_center in select_face_center:
            vect_mesh = self.applyObjInfoToVector(face_center, obj)
            multi_center_list.append((vect_mesh[0], 
                                      vect_mesh[1],
                                      vect_mesh[2]))

        return multi_center_list

    def getMeshCenterPoint(self, mesh):
        average_x = 0.
        average_y = 0.
        average_z = 0.
        select_face = []
        bm = self.getBMesh(mesh)
        
        select_face = self.getSelectedFaces(bm)
        face_num = len(select_face)

        for face in select_face:
            vect = face.calc_center_median()
            average_x += vect.x
            average_y += vect.y
            average_z += vect.z
        
        average_x /= (face_num * 1.0)
        average_y /= (face_num * 1.0)
        average_z /= (face_num * 1.0)

        return (average_x, average_y, average_z)

