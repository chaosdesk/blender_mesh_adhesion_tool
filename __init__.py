############################################################################
#
# __init__.py
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
from . import adhere_object


bl_info = {
    'name': 'Mesh Adhesion Tool',
    'author': 'chaosdesk',
    'version': (1,0),
    'blender': (2, 7, 9),
    "location": "View3D > Edit Mode > Property Panel > Mesh Adhesion",
    'description': 'Adhere any selected mesh to face of another mesh',
    'warning': '',
    'wiki_url': '',
    'tracker_url': 'http://chaos-junction.tumblr.com/',
    "category": "Mesh"}

translation_dict = {
        "en_US":{
            ("*", "Execute Mesh Adhesion"):
                "Execute Mesh Adhesion",
            ("*", "Mesh To Adhere Not Selected"):
                "Mesh To Adhere Not Selected",
            ("*", "Faces Of Mesh Not Selected"):
                "Faces Of Mesh Not Selected",
            ("*", "Mesh Select"):
                "Mesh Select", 
            ("*", "Mesh Adhesion"):
                "Mesh Adhesion", 
            ("*", "Select Mesh to Adhere:"):
                "Select Mesh to Adhere:", 
            ("*", "The Mesh Is Being Editted"):
                "The Mesh Is Being Editted", 
            ("*", "Adhesion Option:"):
                "Adhesion Option:", 
            ("*", "Type Of Mesh Duplication:"):
                "Type Of Mesh Duplication:", 
            ("*", "Offset Position:"):
                "Offset Position:", 
            ("*", "Execute"):
                "Execute", 
            ("*", "Center Of Selected Faces"):
                "Center Of Selected Faces", 
            ("*", "Every Selected Faces"):
                "Every Selected Faces",
            ("*", "Select To Type Of Adhesion"):
                "Select To Type Of Adhesion",
            ("*", "Copy"):
                "Copy", 
            ("*", "Linked"):
                "Linked" 
                },
        "ja_JP":{
            ("*", "Execute Mesh Adhesion"):
                "オブジェクト接着を実行",
            ("*", "Mesh To Adhere Not Selected"):
                "選択メッシュの面が選択されていません",
            ("*", "Faces Of Mesh Not Selected"):
                "元のメッシュの面が選択されていません",
            ("*", "Mesh Select"):
                "オブジェクト選択", 
            ("*", "Mesh Adhesion"):
                "オブジェクト接着", 
            ("*", "Select Mesh to Adhere:"):
                "接着オブジェクト選択:", 
            ("*", "The Mesh Is Being Editted"):
                "編集中のオブジェクトです", 
            ("*", "Adhesion Option:"):
                "接着オプション:", 
            ("*", "Type Of Mesh Duplication:"):
                "オブジェクトの複製方式:", 
            ("*", "Offset Position:"):
                "オフセット座標:", 
            ("*", "Execute"):
                "実行", 
            ("*", "Center Of Selected Faces"):
                "選択面の中心に接着", 
            ("*", "Every Selected Faces"):
                "各選択面毎に接着",
            ("*", "Select To Type Of Adhesion"):
                "接着方法の選択",
            ("*", "Copy"):
                "コピー", 
            ("*", "Linked"):
                "参照"
                }
        }


def getTransText(str_key):
    return bpy.app.translations.pgettext(str_key)


class MeshSearchProps(bpy.types.PropertyGroup):
    
    mesh_list = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    sel_mesh = bpy.props.StringProperty()

    def update_data(self):
        sel_mesh_exist = False

        self.mesh_list.clear()
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                val = self.mesh_list.add()
                val.name = obj.name
        
        for mesh in self.mesh_list:
            if mesh.name == self.sel_mesh:
                sel_mesh_exist = True
                break

        if sel_mesh_exist == False:
            self.sel_mesh = ""


class AdhereObject(bpy.types.Operator):
    bl_idname  = "object.adhere_object"
    bl_label = getTransText("Execute Mesh Adhesion")
    bl_description = getTransText("Execute Mesh Adhesion")
    bl_options = {'REGISTER','UNDO'}
    ret_val = 0

    def execute(self, context):
        wm = context.window_manager
        scene = context.scene
        mcollection = context.window_manager.mesh_collection
        
        adh_obj = bpy.data.objects[mcollection.sel_mesh] 
        org_obj = bpy.context.active_object
        offset = (scene.offset_x, scene.offset_y, scene.offset_z)

        aobj = adhere_object.AdhereProc()
        if(scene.adhere_option == "SINGLE"):
            AdhereObject.ret_val = aobj.execSingleAdhesion(org_obj, adh_obj, offset)
        else:
            link = False
            if(scene.objcopy_option == "REFERENCE"):
                link = True
            AdhereObject.ret_val = aobj.execMultipleAdhesion(org_obj, adh_obj, offset, link)
        if(AdhereObject.ret_val != 0):
            return wm.invoke_popup(self, width=250, height=100)

        return {'FINISHED'}

    # Popup Message
    def draw(self, context):
        layout = self.layout
        if AdhereObject.ret_val == -2:
            layout.label(getTransText("Mesh To Adhere Not Selected"), icon = 'ERROR')
        elif AdhereObject.ret_val == -1:
            layout.label(getTransText("Faces Of Mesh Not Selected"), icon = 'ERROR')
        else:
            pass


class SelectObject(bpy.types.Operator):
    bl_idname  = "object.select_object"
    bl_label = getTransText("Mesh Select")
    bl_description = getTransText("Mesh Select")
    
    def invoke(self, context, event):
        scene = context.scene
        if scene.running is False:
            scene.running = True
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        return {'CANCELED'}
        
    def modal(self, context, event):
        scene = context.scene
        mcollection = context.window_manager.mesh_collection
        cursor_set = None

        # Finish this function when selecting tool isn't running
        if scene.running is False:
            return {'PASS_THROUGH'}
        else:
            cursor_set = context.window_manager.windows[0]
            cursor_set.cursor_modal_set("EYEDROPPER")
        
        # Each process
        if event.type == 'MOUSEMOVE':
            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE':
            if event.value == 'RELEASE':

                # Select object
                loc = event.mouse_region_x, event.mouse_region_y
                ret = bpy.ops.view3d.select(object=True,location=loc)
                if ret == {'PASS_THROUGH'}:
                    cursor_set.cursor_modal_restore()
                    scene.running = False
                    return {'CANCELLED'}
                
                new_selected_obj = bpy.context.selected_objects[0]
                if new_selected_obj.type != 'MESH':
                    cursor_set.cursor_modal_restore()
                    scene.running = False
                    return {'CANCELLED'}
                
                mcollection.sel_mesh = new_selected_obj.name

                cursor_set.cursor_modal_restore()
                scene.running = False
                return {'FINISHED'}

        elif event.type == 'RIGHTMOUSE':
            if event.value == 'PRESS':
                cursor_set.cursor_modal_restore()
                scene.running = False
                return {'CANCELLED'}

        return {'RUNNING_MODAL'}


class VIEW3D_DisplayMenu(bpy.types.Panel):
    bl_label = getTransText("Mesh Adhesion")
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = getTransText("Mesh Adhesion")

    @classmethod
    def poll(cls, context):
        # Display menu only when the mode is edit one
        if bpy.context.mode == 'EDIT_MESH':
            return True
        return False

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='PLUGIN')
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        mcollection = context.window_manager.mesh_collection
        mcollection.update_data()

        col = layout.column(align=True)
        col.label(text=getTransText("Select Mesh to Adhere:"))
        row = col.row(align=True)
        row.prop_search(mcollection, property='sel_mesh',
                        search_data = mcollection, 
                        search_property="mesh_list", 
                        text="",
                        icon='MESH_DATA')
        row.operator(SelectObject.bl_idname, text="",icon='EYEDROPPER')

        if mcollection.sel_mesh != "":
            if bpy.data.objects[mcollection.sel_mesh] == bpy.context.active_object:
                layout.label(getTransText("The Mesh Is Being Editted"),icon = 'ERROR')

        col = layout.column(align=True)
        col.label(text=getTransText("Adhesion Option:"))
        col.prop(scene, 'adhere_option', text="", expand=False)

        if(scene.adhere_option == "MULTIPLE"):
            col = layout.column(align=True)
            col.label(text=getTransText("Type Of Mesh Duplication:"))
            row = col.row(align=True)
            row.prop(scene, 'objcopy_option', expand=True)

        col = layout.column(align=True)
        col.label(text=getTransText("Offset Position:"))
        col.prop(scene, "offset_x")
        col.prop(scene, "offset_y")
        col.prop(scene, "offset_z")

        layout.separator()
        layout.operator(AdhereObject.bl_idname,text=getTransText("Execute"))


def init_props():
    scene = bpy.types.Scene
    scene.running = bpy.props.BoolProperty(
        default=False
    )

    scene.offset_x = bpy.props.FloatProperty(name="X")
    scene.offset_y = bpy.props.FloatProperty(name="Y")
    scene.offset_z = bpy.props.FloatProperty(name="Z")

    adhere_option_tuple = (("SINGLE", getTransText("Center Of Selected Faces"), ""),
                           ("MULTIPLE", getTransText("Every Selected Faces"), ""))
    scene.adhere_option = bpy.props.EnumProperty(
            name = getTransText("Adhesion Option:"),
            description = getTransText("Select To Type Of Adhesion"),
            items = adhere_option_tuple
    )

    obj_copy_option_tuple = (("COPY", getTransText("Copy"), ""),
                             ("REFERENCE", getTransText("Linked"), ""))
    scene.objcopy_option = bpy.props.EnumProperty(
            name = getTransText("Type Of Mesh Duplication:"),
            description = getTransText("Select To Type Of Adhesion"),
            items = obj_copy_option_tuple
    )

    bpy.types.WindowManager.mesh_collection = bpy.props.PointerProperty(
            type = MeshSearchProps
    )

def clear_props():
    scene = bpy.types.Scene
    del scene.running
    del scene.offset_x
    del scene.offset_y
    del scene.offset_z
    del scene.adhere_option
    del scene.objcopy_option

def register():
    bpy.app.translations.register(__name__, translation_dict)
    bpy.utils.register_module(__name__)
    init_props()

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.app.translations.unregister(__name__)
    clear_props()

if __name__ == "__main__":
    register()


