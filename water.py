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
import bmesh
import os
import mathutils
from enum import Enum

class WaterType(Enum):
    DEFAULT_INVISIBLE = 0  
    DEFAULT_VISIBLE = 1   
    SHALLOW_INVISIBLE = 2 
    SHALLOW_VISIBLE = 3  

class WaterVertex:
    def __init__(self, position, direction=(0.0, 0.0), wave_height=0.0, unk_height=0.0):
        self.position = position  
        self.direction = direction  
        self.wave_height = wave_height  
        self.unk_height = unk_height 

class Water:
    def __init__(self, vertices, flag=WaterType.DEFAULT_VISIBLE):
        self.vertices = vertices  
        self.flag = flag  

def parse_water_dat(water_path):
    waters = []
    try:
        with open(water_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            print(f"Открыт файл {water_path}, найдено {len(lines)} строк")
            if len(lines) == 0:
                print("Файл пустой!")
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('#') or line == "processed":
                    print(f"Строка {i+1} пропущена: пустая, комментарий или 'processed': {line}")
                    continue
                parts = [p.strip() for p in line.split()]
                print(f"Строка {i+1}: найдено {len(parts)} частей: {parts}")
                if len(parts) >= 22:  
                    try:
                        vertices = []
                
                        v1 = WaterVertex(
                            position=(float(parts[0]), float(parts[1]), float(parts[2])),
                            direction=(float(parts[3]), float(parts[4])),
                            unk_height=float(parts[5]),
                            wave_height=float(parts[6])
                        )
                        vertices.append(v1)
                      
                        v2 = WaterVertex(
                            position=(float(parts[7]), float(parts[8]), float(parts[9])),
                            direction=(float(parts[10]), float(parts[11])),
                            unk_height=float(parts[12]),
                            wave_height=float(parts[13])
                        )
                        vertices.append(v2)
                    
                        v3 = WaterVertex(
                            position=(float(parts[14]), float(parts[15]), float(parts[16])),
                            direction=(float(parts[17]), float(parts[18])),
                            unk_height=float(parts[19]),
                            wave_height=float(parts[20])
                        )
                        vertices.append(v3)
                     
                        if len(parts) == 29:  
                            v4 = WaterVertex(
                                position=(float(parts[21]), float(parts[22]), float(parts[23])),
                                direction=(float(parts[24]), float(parts[25])),
                                unk_height=float(parts[26]),
                                wave_height=float(parts[27])
                            )
                            vertices.append(v4)
                            flag = WaterType(int(parts[28]))
                        else:  
                            flag = WaterType(int(parts[21]))
                        water = Water(vertices=vertices, flag=flag)
                        waters.append(water)
                        print(f"Строка {i+1}: Успешно распарсена водная поверхность с {len(vertices)} вершинами, flag={flag}")
                    except (ValueError, IndexError) as e:
                        print(f"Ошибка в строке {i+1}: {line} — {e}. Строка пропущена.")
                else:
                    print(f"Строка {i+1} пропущена: недостаточно данных ({len(parts)} частей): {line}")
    except Exception as e:
        print(f"Ошибка при открытии файла {water_path}: {e}")
    print(f"Всего распарсено {len(waters)} водных поверхностей из water.dat")
    return waters

def create_water_mesh(water, name_prefix="Water"):
    mesh = bpy.data.meshes.new(f"{name_prefix}_{len(water.vertices)}_{id(water)}")
    obj = bpy.data.objects.new(f"{name_prefix}_{len(water.vertices)}_{id(water)}", mesh)

    bm = bmesh.new()
    bm_verts = []
    for v in water.vertices:
        bm_verts.append(bm.verts.new(v.position))
    if len(water.vertices) == 4:
        bm.faces.new([bm_verts[0], bm_verts[1], bm_verts[3], bm_verts[2]])  
    else: 
        bm.faces.new([bm_verts[0], bm_verts[2], bm_verts[1]]) 
    bm.to_mesh(mesh)
    bm.free()


    for i, v in enumerate(water.vertices):
        obj[f"vertex_{i}_direction"] = v.direction
        obj[f"vertex_{i}_wave_height"] = v.wave_height
        obj[f"vertex_{i}_unk_height"] = v.unk_height
    obj["flag"] = water.flag.value

    is_visible = water.flag in [WaterType.DEFAULT_VISIBLE, WaterType.SHALLOW_VISIBLE]
    obj.hide_viewport = not is_visible
    obj.hide_render = not is_visible


    mat = bpy.data.materials.new(name=f"WaterMat_{id(water)}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.get("Material Output")
    is_shallow = water.flag in [WaterType.SHALLOW_INVISIBLE, WaterType.SHALLOW_VISIBLE]
    principled.inputs["Base Color"].default_value = (0, 0, 1, 0.5) if not is_shallow else (0, 0.5, 1, 0.5)
    principled.inputs["Alpha"].default_value = 0.5
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

  
    mat.blend_method = 'BLEND'  

    mat.use_screen_refraction = True  

    mesh.materials.append(mat)

    return obj

def import_water(water_path):
    waters = parse_water_dat(water_path)
    grouped_objects = {flag: [] for flag in WaterType}
    for water in waters:
        obj = create_water_mesh(water)
        grouped_objects[water.flag].append(obj)
        bpy.context.collection.objects.link(obj)

 
    for flag, objects in grouped_objects.items():
        if objects:
    
            parent = bpy.data.objects.new(f"WaterGroup_{flag.name}", None)
            parent["flag"] = flag.value
            bpy.context.collection.objects.link(parent)
            for obj in objects:
                obj.parent = parent
    return waters

def export_water_dat(water_path, objects):
    with open(water_path, 'w') as file:
        file.write("processed\n")
        for obj in objects:
            if "flag" not in obj:
                print(f"Пропущен объект {obj.name}: нет свойства 'flag'")
                continue
            mesh = obj.data
            if len(mesh.vertices) not in {3, 4}:
                print(f"Пропущен объект {obj.name}: неподходящее количество вершин ({len(mesh.vertices)})")
                continue
            flag = WaterType(obj["flag"])
            verts = [v.co for v in mesh.vertices]
            if len(verts) == 4:
 
                order = [0, 1, 3, 2]
            else:
     
                order = [0, 2, 1]
            line_parts = []
            for i in order:
                v = verts[i]
                direction = obj.get(f"vertex_{i}_direction", (0.0, 0.0))
                unk_height = obj.get(f"vertex_{i}_unk_height", 0.0)
                wave_height = obj.get(f"vertex_{i}_wave_height", 0.0)
                line_parts.extend([
                    f"{v.x:.4f}", f"{v.y:.4f}", f"{v.z:.4f}",
                    f"{direction[0]:.5f}", f"{direction[1]:.5f}",
                    f"{unk_height:.5f}", f"{wave_height:.5f}"
                ])
            line_parts.append(str(flag.value))
            file.write(" ".join(line_parts) + "\n")
    print(f"Экспортировано {len(objects)} водных поверхностей в water.dat: {water_path}")

class WATER_OT_Import(bpy.types.Operator):
    bl_idname = "water.import"
    bl_label = "Import Water"
    def execute(self, context):
        water_path = context.scene.water_path
        if not os.path.exists(water_path):
            self.report({'ERROR'}, "Проверьте путь к water.dat")
            return {'CANCELLED'}
        waters = import_water(water_path)
        self.report({'INFO'}, f"Импортировано {len(waters)} водных поверхностей")
        return {'FINISHED'}

class WATER_OT_Export(bpy.types.Operator):
    bl_idname = "water.export"
    bl_label = "Export Water"
    def execute(self, context):
        water_path = context.scene.water_path_export
        if not water_path:
            self.report({'ERROR'}, "Укажите путь для экспорта water.dat")
            return {'CANCELLED'}
        if not water_path.lower().endswith('.dat'):
            water_path += '.dat'
        objects = []
  
        for obj in bpy.context.selected_objects:
            if "flag" in obj:
                objects.append(obj)
            for child in obj.children:
                if "flag" in child:
                    objects.append(child)
        if not objects:
            self.report({'WARNING'}, "Нет выделенных водных объектов для экспорта")
            return {'CANCELLED'}
        export_water_dat(water_path, objects)
        self.report({'INFO'}, f"Экспортировано {len(objects)} водных поверхностей в water.dat: {water_path}")
        return {'FINISHED'}

class WATER_OT_SetParameters(bpy.types.Operator):
    bl_idname = "water.set_parameters"
    bl_label = "Set Parameters"
    def execute(self, context):
        scene = context.scene
        selected = bpy.context.selected_objects
        updated_objects = 0
        for obj in selected:
            if "flag" not in obj:
                continue
            updated_objects += 1
            num_vertices = len(obj.data.vertices)
    
            for i in range(num_vertices):
                obj[f"vertex_{i}_direction"] = (scene.water_speed_x, scene.water_speed_y)
                obj[f"vertex_{i}_wave_height"] = scene.wave_height
                obj[f"vertex_{i}_unk_height"] = scene.unk_height
        
            obj["flag"] = int(scene.water_type)
      
            flag = WaterType(int(scene.water_type))
            is_visible = flag in [WaterType.DEFAULT_VISIBLE, WaterType.SHALLOW_VISIBLE]
            obj.hide_viewport = not is_visible
            obj.hide_render = not is_visible
 
            if obj.data.materials:
                mat = obj.data.materials[0]
                is_shallow = flag in [WaterType.SHALLOW_INVISIBLE, WaterType.SHALLOW_VISIBLE]
                mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
                    (0, 0, 1, 0.5) if not is_shallow else (0, 0.5, 1, 0.5)
                )
        self.report({'INFO'}, f"Параметры установлены для {updated_objects} водных поверхностей")
        return {'FINISHED'}

class WATER_OT_GetParameters(bpy.types.Operator):
    bl_idname = "water.get_parameters"
    bl_label = "Get Parameters"
    def execute(self, context):
        scene = context.scene
        if bpy.context.selected_objects and "flag" in bpy.context.selected_objects[0]:
            obj = bpy.context.selected_objects[0]

            direction = obj.get("vertex_0_direction", (0.0, 0.0))
            scene.water_speed_x = direction[0]
            scene.water_speed_y = direction[1]
            scene.wave_height = obj.get("vertex_0_wave_height", 0.0)
            scene.unk_height = obj.get("vertex_0_unk_height", 0.0)
            scene.water_type = str(obj.get("flag", 1))
        return {'FINISHED'}

class WATER_OT_CheckFile(bpy.types.Operator):
    bl_idname = "water.check_file"
    bl_label = "Check WATER.DAT"
    def execute(self, context):
        water_path = context.scene.water_path
        if not os.path.exists(water_path):
            self.report({'ERROR'}, "Файл water.dat не найден!")
            return {'CANCELLED'}
        try:
            with open(water_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                valid_lines = 0
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line or line.startswith('#') or line == "processed":
                        continue
                    parts = [p.strip() for p in line.split()]
                    if len(parts) in {22, 29}:
                        try:
                            _ = [float(x) for x in parts[:-1]] 
                            flag = int(parts[-1])
                            if flag in {0, 1, 2, 3}:
                                valid_lines += 1
                        except ValueError:
                            continue
                self.report({'INFO'}, f"Найдено {valid_lines} валидных водных поверхностей в water.dat")
        except Exception as e:
            self.report({'ERROR'}, f"Ошибка при проверке файла: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}
