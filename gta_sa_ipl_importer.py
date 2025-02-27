import bpy
import os
import bmesh
from .dff import dff

# Функция для парсинга IPL файла (импорт) с проверкой дубликатов ID и комментариев
def parse_ipl(ipl_path):
    objects = []
    id_set = set()  # Множество для отслеживания ID
    with open(ipl_path, 'r') as file:
        lines = file.readlines()
        in_inst_section = False
        for i, line in enumerate(lines):
            line = line.strip()
            if line.lower() == 'inst':
                in_inst_section = True
                print(f"Начало секции 'inst' на строке {i+1}")
                continue
            elif line.lower() == 'end':
                in_inst_section = False
                print(f"Конец секции 'inst' на строке {i+1}")
                continue
            if in_inst_section and line and '#' not in line:  # Пропускаем строки с комментариями
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 10:
                    try:
                        obj_id = int(parts[0])
                        if obj_id in id_set:
                            print(f"Строка {i+1}: Дубликат ID {obj_id} для {parts[1]}")
                        id_set.add(obj_id)
                        obj = {
                            'id': parts[0],
                            'model_name': parts[1],
                            'interior': parts[2],
                            'pos': (float(parts[3]), float(parts[4]), float(parts[5])),
                            'rot': (float(parts[9]), float(parts[6]), float(parts[7]), float(parts[8])),
                            'lod': parts[10] if len(parts) > 10 else '-1'
                        }
                        objects.append(obj)
                        print(f"Строка {i+1}: Успешно распарсен объект {obj['model_name']} с ID {obj['id']}")
                    except ValueError as e:
                        print(f"Ошибка в строке {i+1}: {line} — {e}")
                else:
                    print(f"Строка {i+1} пропущена: недостаточно данных ({len(parts)} частей): {line}")
            elif in_inst_section and '#' in line:
                print(f"Строка {i+1} пропущена: содержит комментарий: {line}")
    print(f"Всего распарсено {len(objects)} объектов из IPL")
    return objects

# Функция для загрузки DFF модели
def import_dff(model_name, dff_folder):
    dff_path = os.path.join(dff_folder, model_name + '.dff')
    if not os.path.exists(dff_path):
        print(f"Ошибка: Модель {model_name} не найдена по пути {dff_path}")
        return None

    try:
        dff_loader = dff()
        dff_loader.load_file(dff_path)
    except Exception as e:
        print(f"Ошибка загрузки DFF {model_name}: {e}")
        return None

    if not dff_loader.geometry_list:
        print(f"Ошибка: Не удалось загрузить геометрию из {model_name}")
        return None

    geometry = dff_loader.geometry_list[0]
    mesh = bpy.data.meshes.new(model_name)
    obj = bpy.data.objects.new(model_name, mesh)

    bm = bmesh.new()
    for vert in geometry.vertices:
        bm.verts.new((vert.x, vert.y, vert.z))
    bm.verts.ensure_lookup_table()

    for tri in geometry.triangles:
        try:
            bm.faces.new((bm.verts[tri.b], bm.verts[tri.a], bm.verts[tri.c]))
        except ValueError:
            continue

    bm.to_mesh(mesh)
    bm.free()
    print(f"Успешно загружена модель {model_name}")
    return obj

# Функция для размещения объектов в сцене (импорт) — без масштабирования
def place_objects(objects, dff_folder):
    for obj_data in objects:
        model_name = obj_data['model_name']
        obj = import_dff(model_name, dff_folder)
        if obj:
            obj.location = obj_data['pos']  # Оригинальные координаты
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = obj_data['rot']
            obj['id'] = int(obj_data['id'])
            obj['interior'] = int(obj_data['interior'])
            obj['lod'] = int(obj_data['lod']) if obj_data['lod'] != '-1' else -1
            bpy.context.collection.objects.link(obj)
            print(f"Объект {model_name} размещён на {obj.location}")
        else:
            # Вместо создания пустого объекта просто пропускаем и логируем
            print(f"Не удалось загрузить {model_name} из DFF, объект не создан (должен быть на {obj_data['pos']})")

# Функция для экспорта IPL с проверкой дубликатов ID — без масштабирования
def export_ipl(ipl_path, objects, lod_autosearch=False):
    lod_dict = {}
    id_set = set()  # Множество для проверки дубликатов ID
    duplicate_ids = []

    if lod_autosearch:
        for obj in objects:
            if obj.name.lower().startswith('lod'):
                base_name = obj.name[3:]
                lod_dict[base_name] = obj

    with open(ipl_path, 'w') as file:
        file.write("inst\n")
        for i, obj in enumerate(objects):
            if 'id' not in obj:
                continue
            obj_id = obj['id']
            if obj_id in id_set:
                duplicate_ids.append(obj_id)
            else:
                id_set.add(obj_id)
                model_name = obj.name
                pos = (obj.location.x, obj.location.y, obj.location.z)  # Оригинальные координаты
                rot = obj.rotation_quaternion
                interior = obj.get('interior', 0)
                lod_index = obj.get('lod', -1)
                if lod_autosearch and model_name in lod_dict:
                    lod_index = lod_dict[model_name].get('id', -1)
                line = f"{obj_id}, {model_name}, {interior}, {pos[0]:.6f}, {pos[1]:.6f}, {pos[2]:.6f}, {rot[1]:.6f}, {rot[2]:.6f}, {rot[3]:.6f}, {rot[0]:.6f}, {lod_index}\n"
                file.write(line)
        file.write("end\n")
    
    if duplicate_ids:
        raise ValueError(f"Обнаружены дубликаты ID при экспорте IPL: {duplicate_ids}")
    print(f"Экспортировано {len(objects)} объектов в IPL: {ipl_path}")

# Функция для экспорта IDE с проверкой дубликатов ID
def export_ide(ide_path, objects):
    id_set = set()  # Множество для проверки дубликатов ID
    duplicate_ids = []

    with open(ide_path, 'w') as file:
        file.write("objs\n")
        for obj in objects:
            if 'id' not in obj:
                continue
            obj_id = obj['id']
            if obj_id in id_set:
                duplicate_ids.append(obj_id)
            else:
                id_set.add(obj_id)
                model_name = obj.name
                txd_name = obj.get('txd_name', f"{model_name}_tex")
                distance = obj.get('distance', 300.0)
                flags = obj.get('flag', 0)
                line = f"{obj_id}, {model_name}, {txd_name}, {distance:.1f}, {flags}\n"
                file.write(line)
        file.write("end\n")
    
    if duplicate_ids:
        raise ValueError(f"Обнаружены дубликаты ID при экспорте IDE: {duplicate_ids}")
    print(f"Экспортировано {len(objects)} объектов в IDE: {ide_path}")

# Функция проверки ошибок
def check_errors(objects):
    errors = []
    warnings = []
    lod_dict = {obj.name[3:].lower(): obj for obj in objects if obj.name.lower().startswith('lod')}

    for obj in objects:
        model_name = obj.name.lower()
        if len(obj.name) > 24:
            errors.append(f"[ERROR #1] Длина имени модели {obj.name} превышает 24 символа")
        if model_name.startswith('lod') and model_name[3:] not in {o.name.lower() for o in objects}:
            errors.append(f"[ERROR #2] Найден LOD {obj.name} без соответствующей модели")
        if not model_name.startswith('lod') and model_name not in lod_dict:
            warnings.append(f"[WARNING #3] Модель {obj.name} без LOD")
        if model_name.startswith('lod') and model_name[3:] not in {o.name.lower() for o in objects if not o.name.lower().startswith('lod')}:
            warnings.append(f"[WARNING #4] LOD {obj.name} имеет некорректное имя")

    return errors, warnings

# Панель на N-панели
class GTA_SA_IPL_PT_Panel(bpy.types.Panel):
    bl_label = "GTA SA IPL Importer"
    bl_idname = "GTA_PT_SA_IPL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GTA SA IPL"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Part 1: ID Setup
        box = layout.box()
        box.label(text="Part 1: ID Setup")
        box.prop(scene, "id_start", text="ID Start")
        box.operator("gta.set_values", text="Set Values")
        
        # Part 2: Parameters
        box = layout.box()
        box.label(text="Part 2: Parameters")
        
        row = box.row()
        row.prop(scene, "txd_name", text="TXD Name")
        row.operator("gta.get_txd", text="GET")
        row.operator("gta.set_txd", text="SET")
        
        row = box.row()
        row.prop(scene, "interior", text="Interior")
        row.operator("gta.get_interior", text="GET")
        row.operator("gta.set_interior", text="SET")
        
        row = box.row()
        row.prop(scene, "distance", text="Distance")
        row.operator("gta.get_distance", text="GET")
        row.operator("gta.set_distance", text="SET")
        
        row = box.row()
        row.prop(scene, "flag", text="Flag")
        row.operator("gta.get_flag", text="GET")
        row.operator("gta.set_flag", text="SET")
        
        row = box.row()
        row.prop(scene, "lod_start", text="LOD Start")
        row.operator("gta.get_lod_start", text="GET")
        row.operator("gta.set_lod_start", text="SET")
        
        row = box.row()
        row.operator("gta.get_all", text="GET ALL")
        row.operator("gta.reset_all", text="Re Set All Values")
        
        # Part 3: Export & Check
        box = layout.box()
        box.label(text="Part 3: Export & Check")
        box.prop(scene, "ipl_path", text="IPL File")
        box.prop(scene, "dff_folder", text="DFF Folder")
        box.operator("import.ipl", text="Import IPL")
        box.prop(scene, "export_ipl_path", text="Export IPL File")
        box.prop(scene, "export_ide_path", text="Export IDE File")
        box.prop(scene, "lod_autosearch", text="LOD AutoSearch")
        row = box.row()
        row.operator("export.ipl", text="Export IPL")
        row.operator("export.ide", text="Export IDE")
        box.operator("gta.check_errors", text="Check Errors")

# Оператор импорта
class IMPORT_OT_IPL(bpy.types.Operator):
    bl_idname = "import.ipl"
    bl_label = "Import IPL File"
    def execute(self, context):
        ipl_path = context.scene.ipl_path
        dff_folder = context.scene.dff_folder
        if not os.path.exists(ipl_path):
            self.report({'ERROR'}, f"IPL файл не найден: {ipl_path}")
            return {'CANCELLED'}
        if not os.path.exists(dff_folder):
            self.report({'ERROR'}, f"Папка DFF не найдена: {dff_folder}")
            return {'CANCELLED'}
        objects = parse_ipl(ipl_path)
        place_objects(objects, dff_folder)
        self.report({'INFO'}, f"Импортировано {len(objects)} объектов")
        return {'FINISHED'}

# Оператор установки ID (Set Values)
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
        self.report({'INFO'}, f"Установлены ID для {len(selected)} объектов")
        return {'FINISHED'}

# Операторы GET/SET для каждого поля
class GTA_OT_GetTXD(bpy.types.Operator):
    bl_idname = "gta.get_txd"
    bl_label = "Get TXD"
    def execute(self, context):
        if bpy.context.selected_objects:
            obj = bpy.context.selected_objects[0]
            context.scene.txd_name = obj.get('txd_name', '')
        return {'FINISHED'}

class GTA_OT_SetTXD(bpy.types.Operator):
    bl_idname = "gta.set_txd"
    bl_label = "Set TXD"
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            obj['txd_name'] = context.scene.txd_name
        return {'FINISHED'}

class GTA_OT_GetInterior(bpy.types.Operator):
    bl_idname = "gta.get_interior"
    bl_label = "Get Interior"
    def execute(self, context):
        if bpy.context.selected_objects:
            obj = bpy.context.selected_objects[0]
            context.scene.interior = obj.get('interior', 0)
        return {'FINISHED'}

class GTA_OT_SetInterior(bpy.types.Operator):
    bl_idname = "gta.set_interior"
    bl_label = "Set Interior"
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            obj['interior'] = context.scene.interior
        return {'FINISHED'}

class GTA_OT_GetDistance(bpy.types.Operator):
    bl_idname = "gta.get_distance"
    bl_label = "Get Distance"
    def execute(self, context):
        if bpy.context.selected_objects:
            obj = bpy.context.selected_objects[0]
            context.scene.distance = obj.get('distance', 300.0)
        return {'FINISHED'}

class GTA_OT_SetDistance(bpy.types.Operator):
    bl_idname = "gta.set_distance"
    bl_label = "Set Distance"
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            obj['distance'] = context.scene.distance
        return {'FINISHED'}

class GTA_OT_GetFlag(bpy.types.Operator):
    bl_idname = "gta.get_flag"
    bl_label = "Get Flag"
    def execute(self, context):
        if bpy.context.selected_objects:
            obj = bpy.context.selected_objects[0]
            context.scene.flag = obj.get('flag', 0)
        return {'FINISHED'}

class GTA_OT_SetFlag(bpy.types.Operator):
    bl_idname = "gta.set_flag"
    bl_label = "Set Flag"
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            obj['flag'] = context.scene.flag
        return {'FINISHED'}

class GTA_OT_GetLODStart(bpy.types.Operator):
    bl_idname = "gta.get_lod_start"
    bl_label = "Get LOD Start"
    def execute(self, context):
        if bpy.context.selected_objects:
            obj = bpy.context.selected_objects[0]
            context.scene.lod_start = obj.get('lod', 0)
        return {'FINISHED'}

class GTA_OT_SetLODStart(bpy.types.Operator):
    bl_idname = "gta.set_lod_start"
    bl_label = "Set LOD Start"
    def execute(self, context):
        for obj in bpy.context.selected_objects:
            if obj.name.lower().startswith('lod'):
                obj['lod'] = context.scene.lod_start
        return {'FINISHED'}

# Оператор GET ALL
class GTA_OT_GetAll(bpy.types.Operator):
    bl_idname = "gta.get_all"
    bl_label = "Get All"
    def execute(self, context):
        if bpy.context.selected_objects:
            obj = bpy.context.selected_objects[0]
            context.scene.txd_name = obj.get('txd_name', '')
            context.scene.interior = obj.get('interior', 0)
            context.scene.distance = obj.get('distance', 300.0)
            context.scene.flag = obj.get('flag', 0)
            context.scene.lod_start = obj.get('lod', 0)
        return {'FINISHED'}

# Оператор Re Set All Values
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

# Оператор экспорта IPL с добавлением расширения .ipl
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
        objects = bpy.context.scene.objects
        try:
            export_ipl(export_ipl_path, objects, context.scene.lod_autosearch)
            self.report({'INFO'}, f"Экспортировано {len(objects)} объектов в IPL: {export_ipl_path}")
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}

# Оператор экспорта IDE с добавлением расширения .ide
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
        objects = bpy.context.scene.objects
        try:
            export_ide(export_ide_path, objects)
            self.report({'INFO'}, f"Экспортировано {len(objects)} объектов в IDE: {export_ide_path}")
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        return {'FINISHED'}

# Оператор проверки ошибок
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

# Регистрация классов и свойств
classes = [
    GTA_SA_IPL_PT_Panel, IMPORT_OT_IPL, EXPORT_OT_IPL, EXPORT_OT_IDE,
    GTA_OT_SetValues, GTA_OT_GetTXD, GTA_OT_SetTXD, GTA_OT_GetInterior,
    GTA_OT_SetInterior, GTA_OT_GetDistance, GTA_OT_SetDistance, GTA_OT_GetFlag,
    GTA_OT_SetFlag, GTA_OT_GetLODStart, GTA_OT_SetLODStart, GTA_OT_GetAll,
    GTA_OT_ResetAll, GTA_OT_CheckErrors
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

if __name__ == "__main__":
    register()
