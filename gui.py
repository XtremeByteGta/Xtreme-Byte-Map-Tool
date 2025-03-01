# MIT License
#
# Copyright (c) 2025 xtreme byte
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import bpy
import os
from .gta_sa_ipl_importer import parse_ipl, import_dff, place_objects, export_ipl, export_ide, check_errors
from .water import WATER_OT_Import, WATER_OT_Export, WATER_OT_SetParameters, WATER_OT_GetParameters, WATER_OT_CheckFile

class Xtreme_Byte_PT_Panel(bpy.types.Panel):
    bl_label = "Xtreme Byte"
    bl_idname = "XTREME_PT_BYTE"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Xtreme Tools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Секция Настройка объектов
        box = layout.box()
        box.label(text="Настройка объектов", icon='OBJECT_DATA')
        box.prop(scene, "id_start", text="Начальный ID")
        box.operator("gta.set_values", text="Применить настройки")

        # Секция Параметры моделей
        box = layout.box()
        box.label(text="Параметры моделей", icon='MODIFIER')
        col = box.column(align=True)
        col.prop(scene, "txd_name", text="Имя TXD")
        col.prop(scene, "interior", text="Интерьер")
        col.prop(scene, "distance", text="Дистанция")
        col.prop(scene, "flag", text="Флаг")
        col.prop(scene, "lod_start", text="Начало LOD")

        row = box.row()
        row.operator("gta.get_all", text="Применить все")
        row.operator("gta.reset_all", text="Сбросить все")

        # Секция Параметры воды
        box = layout.box()
        box.label(text="Параметры воды", icon='MATFLUID')
        col = box.column(align=True)
        col.label(text="Направление течения:")
        row = col.row(align=True)
        row.prop(scene, "water_speed_x", text="X")
        row.prop(scene, "water_speed_y", text="Y")
        col.prop(scene, "wave_height", text="Высота волн")
        col.prop(scene, "unk_height", text="Неизвестная высота")
        col.prop(scene, "water_type", text="Тип воды")
        row = box.row(align=True)
        row.operator("water.get_parameters", text="Получить")
        row.operator("water.set_parameters", text="Установить")

        # Секция Импорт/Экспорт
        box = layout.box()
        box.label(text="Импорт и Экспорт", icon='FILE')
        box.prop(scene, "ipl_path", text="Путь к IPL")
        box.prop(scene, "dff_folder", text="Папка DFF")
        box.operator("import.ipl", text="Импортировать IPL")

        col = box.column(align=True)
        col.prop(scene, "export_ipl_path", text="Экспорт IPL")
        col.prop(scene, "export_ide_path", text="Экспорт IDE")
        col.prop(scene, "lod_autosearch", text="Автпоиск LOD")

        row = box.row()
        row.operator("export.ipl", text="Экспорт IPL")
        row.operator("export.ide", text="Экспорт IDE")

        # Секция WATER.DAT
        col = box.column(align=True)
        col.prop(scene, "water_path", text="Путь к WATER.DAT")
        col.prop(scene, "water_path_export", text="Экспорт WATER.DAT")
        row = box.row(align=True)
        row.operator("water.import", text="Импорт")
        row.operator("water.export", text="Экспорт")
        box.operator("water.check_file", text="Проверить WATER.DAT")

        box.operator("gta.check_errors", text="Проверить ошибки")

class IMPORT_OT_IPL(bpy.types.Operator):
    bl_idname = "import.ipl"
    bl_label = "Import IPL File"
    def execute(self, context):
        ipl_path = context.scene.ipl_path
        dff_folder = context.scene.dff_folder
        if not os.path.exists(ipl_path) or not os.path.exists(dff_folder):
            self.report({'ERROR'}, "Проверьте пути к файлам")
            return {'CANCELLED'}
        objects = parse_ipl(ipl_path)
        place_objects(objects, dff_folder)
        self.report({'INFO'}, f"Импортировано {len(objects)} объектов")
        return {'FINISHED'}

class GTA_OT_SetValues(bpy.types.Operator):
    bl_idname = "gta.set_values"
    bl_label = "Set Values"
    def execute(self, context):
        id_start = context.scene.id_start
        selected = bpy.context.selected_objects
        for i, obj in enumerate(selected):
            obj['id'] = id_start + i
            obj['txd_name'] = context.scene.txd_name
            obj['interior'] = context.scene.interior
            obj['distance'] = context.scene.distance
            obj['flag'] = context.scene.flag
            obj['lod'] = context.scene.lod_start + i if obj.name.lower().startswith('lod') else -1
        self.report({'INFO'}, f"Установлены настройки для {len(selected)} объектов")
        return {'FINISHED'}

class GTA_OT_GetAll(bpy.types.Operator):
    bl_idname = "gta.get_all"
    bl_label = "Get All"
    def execute(self, context):
        selected = bpy.context.selected_objects
        for obj in selected:
            obj['txd_name'] = context.scene.txd_name
            obj['interior'] = context.scene.interior
            obj['distance'] = context.scene.distance
            obj['flag'] = context.scene.flag
            if obj.name.lower().startswith('lod'):
                obj['lod'] = context.scene.lod_start
        self.report({'INFO'}, f"Применены настройки к {len(selected)} объектам")
        return {'FINISHED'}

class GTA_OT_ResetAll(bpy.types.Operator):
    bl_idname = "gta.reset_all"
    bl_label = "Re Set All Values"
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            obj['txd_name'] = context.scene.txd_name
            obj['interior'] = context.scene.interior
            obj['distance'] = context.scene.distance
            obj['flag'] = context.scene.flag
            if obj.name.lower().startswith('lod'):
                obj['lod'] = context.scene.lod_start
        return {'FINISHED'}

class EXPORT_OT_IPL(bpy.types.Operator):
    bl_idname = "export.ipl"
    bl_label = "Export IPL File"
    def execute(self, context):
        export_ipl_path = context.scene.export_ipl_path
        if not export_ipl_path:
            self.report({'ERROR'}, "Укажите путь для экспорта IPL")
            return {'CANCELLED'}
            
        if not export_ipl_path.lower().endswith('.ipl'):
            export_ipl_path += '.ipl'
        objects = bpy.context.selected_objects
        if not objects:
            self.report({'WARNING'}, "Нет выделенных объектов для экспорта")
            return {'CANCELLED'}
        export_ipl(export_ipl_path, objects, context.scene.lod_autosearch)
        self.report({'INFO'}, f"Экспортировано {len(objects)} объектов в IPL: {export_ipl_path}")
        return {'FINISHED'}

class EXPORT_OT_IDE(bpy.types.Operator):
    bl_idname = "export.ide"
    bl_label = "Export IDE File"
    def execute(self, context):
        export_ide_path = context.scene.export_ide_path
        if not export_ide_path:
            self.report({'ERROR'}, "Укажите путь для экспорта IDE")
            return {'CANCELLED'}
   
        if not export_ide_path.lower().endswith('.ide'):
            export_ide_path += '.ide'
        objects = bpy.context.selected_objects
        if not objects:
            self.report({'WARNING'}, "Нет выделенных объектов для экспорта")
            return {'CANCELLED'}
        export_ide(export_ide_path, objects)
        self.report({'INFO'}, f"Экспортировано {len(objects)} объектов в IDE: {export_ide_path}")
        return {'FINISHED'}

class GTA_OT_CheckErrors(bpy.types.Operator):
    bl_idname = "gta.check_errors"
    bl_label = "Check Errors"
    def execute(self, context):
        objects = bpy.context.selected_objects
        errors, warnings = check_errors(objects)
        for error in errors:
            print(error)
        for warning in warnings:
            print(warning)
        self.report({'INFO' if not errors else 'WARNING'}, f"Найдено ошибок: {len(errors)}, предупреждений: {len(warnings)}")
        return {'FINISHED'}

classes = [
    Xtreme_Byte_PT_Panel, IMPORT_OT_IPL, EXPORT_OT_IPL, EXPORT_OT_IDE,
    GTA_OT_SetValues, GTA_OT_GetAll, GTA_OT_ResetAll, GTA_OT_CheckErrors,
    WATER_OT_Import, WATER_OT_Export, WATER_OT_SetParameters, WATER_OT_GetParameters,
    WATER_OT_CheckFile
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ipl_path = bpy.props.StringProperty(name="IPL Path", subtype='FILE_PATH')
    bpy.types.Scene.dff_folder = bpy.props.StringProperty(name="DFF Folder", subtype='DIR_PATH')
    bpy.types.Scene.export_ipl_path = bpy.props.StringProperty(name="Export IPL Path", subtype='FILE_PATH')
    bpy.types.Scene.export_ide_path = bpy.props.StringProperty(name="Export IDE Path", subtype='FILE_PATH')
    bpy.types.Scene.id_start = bpy.props.IntProperty(name="ID Start", default=0)
    bpy.types.Scene.txd_name = bpy.props.StringProperty(name="TXD Name", default="")
    bpy.types.Scene.interior = bpy.props.IntProperty(name="Interior", default=0)
    bpy.types.Scene.distance = bpy.props.FloatProperty(name="Distance", default=300.0)
    bpy.types.Scene.flag = bpy.props.IntProperty(name="Flag", default=0)
    bpy.types.Scene.lod_start = bpy.props.IntProperty(name="LOD Start", default=0)
    bpy.types.Scene.lod_autosearch = bpy.props.BoolProperty(name="LOD AutoSearch", default=False)
    # Свойства для water.dat
    bpy.types.Scene.water_path = bpy.props.StringProperty(name="Water Path", subtype='FILE_PATH')
    bpy.types.Scene.water_path_export = bpy.props.StringProperty(name="Export Water Path", subtype='FILE_PATH')
    bpy.types.Scene.water_speed_x = bpy.props.FloatProperty(name="Water Speed X", default=0.0)
    bpy.types.Scene.water_speed_y = bpy.props.FloatProperty(name="Water Speed Y", default=0.0)
    bpy.types.Scene.wave_height = bpy.props.FloatProperty(name="Wave Height", default=0.0)
    bpy.types.Scene.unk_height = bpy.props.FloatProperty(name="Unk Height", default=0.0)
    bpy.types.Scene.water_type = bpy.props.EnumProperty(
        name="Water Type",
        items=[
            ('0', "Обычная / Невидимая", "Default / Invisible"),
            ('1', "Обычная / Видимая", "Default / Visible"),
            ('2', "Мелководье / Невидимая", "Shallow / Invisible"),
            ('3', "Мелководье / Видимая", "Shallow / Visible")
        ],
        default='1'
    )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.ipl_path
    del bpy.types.Scene.dff_folder
    del bpy.types.Scene.export_ipl_path
    del bpy.types.Scene.export_ide_path
    del bpy.types.Scene.id_start
    del bpy.types.Scene.txd_name
    del bpy.types.Scene.interior
    del bpy.types.Scene.distance
    del bpy.types.Scene.flag
    del bpy.types.Scene.lod_start
    del bpy.types.Scene.lod_autosearch
    del bpy.types.Scene.water_path
    del bpy.types.Scene.water_path_export
    del bpy.types.Scene.water_speed_x
    del bpy.types.Scene.water_speed_y
    del bpy.types.Scene.wave_height
    del bpy.types.Scene.unk_height
    del bpy.types.Scene.water_type