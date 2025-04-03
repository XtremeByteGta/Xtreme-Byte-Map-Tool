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
import bmesh
from struct import unpack
from .dff import dff

def parse_ipl(ipl_path):
    objects = []
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
            if in_inst_section and line and '#' not in line: 
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 10:
                    try:
                        obj_id = int(parts[0])
                        obj = {
                            'id': parts[0],
                            'model_name': parts[1],
                            'interior': parts[2],
                            'pos': (float(parts[3]), float(parts[4]), float(parts[5])),
                            'rot': (float(parts[9]), float(parts[6]), float(parts[7]), float(parts[8])),
                            'lod': parts[10] if len(parts) > 10 else ''
                        }
                        objects.append(obj)
                        print(f"Строка {i+1}: Успешно распарсен объект {obj['model_name']} с ID {obj['id']}")
                    except ValueError as e:
                        print(f"Ошибка в строке {i+1}: {line} — {e}. Строка пропущена.")
                else:
                    print(f"Строка {i+1} пропущена: недостаточно данных ({len(parts)} частей): {line}")
            elif in_inst_section and '#' in line:
                print(f"Строка {i+1} пропущена: содержит комментарий: {line}")
    print(f"Всего распарсено {len(objects)} объектов из IPL")
    return objects

def parse_img(img_path, dir_path=None):

    files = {}
    
    if dir_path:
        if not os.path.exists(dir_path):
            print(f"Файл .dir не найден: {dir_path}")
            return files
        with open(dir_path, 'rb') as dir_file:
            dir_data = dir_file.read()
            for i in range(0, len(dir_data), 32):
                offset, size, name = unpack('<II24s', dir_data[i:i+32])
                name = name.decode('ascii').rstrip('\0').lower()
                files[name] = (offset * 2048, size * 2048) 
    else:  # Версия 2
        with open(img_path, 'rb') as img_file:
            header = img_file.read(8)
            if header[:4] != b'VER2':
                print(f"Неподдерживаемая версия IMG или файл поврежден: {img_path}")
                return files
            num_entries = unpack('<I', header[4:8])[0]
            for _ in range(num_entries):
                offset, size, name = unpack('<II24s', img_file.read(32))
                name = name.decode('ascii').rstrip('\0').lower()
                files[name] = (offset * 2048, size * 2048)
    
    return files

def extract_dff_from_img(img_path, model_name, files_dict):
 
    model_name = model_name.lower()
    if model_name not in files_dict and model_name + '.dff' not in files_dict:
        print(f"Модель {model_name} не найдена в IMG-архиве")
        return None
    
    key = model_name if model_name in files_dict else model_name + '.dff'
    offset, size = files_dict[key]
    
    with open(img_path, 'rb') as img_file:
        img_file.seek(offset)
        dff_data = img_file.read(size)
    return dff_data

def import_dff(model_name, dff_source):
    print(f"Начало импорта модели: {model_name}")
    dff_loader = dff()
    
    # Загрузка данных DFF
    try:
        if isinstance(dff_source, str): 
            dff_path = os.path.join(dff_source, model_name + '.dff')
            if not os.path.exists(dff_path):
                print(f"Ошибка: Файл {dff_path} не найден")
                return None
            print(f"Загрузка DFF из файла: {dff_path}")
            dff_loader.load_file(dff_path)
        else:  
            if dff_source is None:
                print(f"Ошибка: Данные для модели {model_name} не предоставлены")
                return None
            print(f"Загрузка DFF из памяти для модели: {model_name}")
            dff_loader.load_memory(dff_source)
    except Exception as e:
        print(f"Ошибка при загрузке DFF для {model_name}: {e}")
        return None
    
    if not dff_loader.geometry_list:
        print(f"Ошибка: Не удалось загрузить геометрию для {model_name}")
        return None

    geometry = dff_loader.geometry_list[0]
    print(f"Геометрия загружена: {len(geometry.vertices)} вершин, {len(geometry.triangles)} треугольников")

    # Создание меша и объекта
    mesh = bpy.data.meshes.new(model_name)
    obj = bpy.data.objects.new(model_name, mesh)
    bm = bmesh.new()

    # Добавление вершин
    print(f"Добавление {len(geometry.vertices)} вершин в меш")
    for vert in geometry.vertices:
        bm.verts.new((vert.x, vert.y, vert.z))
    bm.verts.ensure_lookup_table()

    # Создание UV-слоёв
    uv_layers = []
    for i in range(len(geometry.uv_layers)):
        uv_layer = bm.loops.layers.uv.new(f"UVMap_{i}")
        uv_layers.append(uv_layer)
        print(f"Создан UV-слой: UVMap_{i}")

    # Обработка материалов
    material_indices = {}
    if geometry.materials:
        print(f"Обнаружено {len(geometry.materials)} материалов")
        for i, mat in enumerate(geometry.materials):
            mat_name = f"{model_name}_mat_{i}"
            has_texture = mat.textures and len(mat.textures) > 0

            if has_texture:
                tex_name = mat.textures[0].name
                mat_name = tex_name if tex_name else mat_name
                print(f"Материал {i}: {mat_name} с текстурой {tex_name}.png")
            else:
                print(f"Материал {i}: {mat_name} без текстуры, используется только цвет")

            # Создаём материал только если есть текстура или цвет
            if has_texture or mat.color:
                bpy_mat = bpy.data.materials.new(name=mat_name)
                bpy_mat.use_nodes = True
                nodes = bpy_mat.node_tree.nodes
                links = bpy_mat.node_tree.links

                # Создание нод
                principled = nodes.new("ShaderNodeBsdfPrincipled")
                output = nodes.get("Material Output")
                if not output:
                    output = nodes.new("ShaderNodeOutputMaterial")
                    print(f"Создана нода Material Output для материала {mat_name}")
                
                links.new(principled.outputs["BSDF"], output.inputs["Surface"])
                print(f"Связь BSDF -> Surface создана для материала {mat_name}")

                # Добавление текстуры, если есть
                if has_texture:
                    tex_name += ".png"
                    if tex_name not in bpy.data.images:
                        image = bpy.data.images.new(name=tex_name, width=1024, height=1024)
                        image.filepath = "//" + tex_name
                        image.source = 'FILE'
                        print(f"Создана новая текстура: {tex_name}")
                    else:
                        image = bpy.data.images[tex_name]
                        print(f"Использована существующая текстура: {tex_name}")
                    
                    tex_node = nodes.new("ShaderNodeTexImage")
                    tex_node.image = image
                    links.new(tex_node.outputs["Color"], principled.inputs["Base Color"])
                    print(f"Текстура {tex_name} подключена к Base Color")

                # Установка цвета, если есть
                if mat.color:
                    color = (mat.color.r / 255.0, mat.color.g / 255.0, mat.color.b / 255.0, mat.color.a / 255.0)
                    principled.inputs["Base Color"].default_value = color
                    print(f"Установлен цвет материала {mat_name}: {color}")

                mesh.materials.append(bpy_mat)
                material_indices[i] = i
            else:
                print(f"Материал {i} пропущен: нет текстуры и цвета")

    # Использование треугольников
    triangles = geometry.extensions.get('mat_split', geometry.triangles)
    print(f"Источник треугольников: {'Bin Mesh PLG' if triangles is not geometry.triangles else 'Geometry'}, всего {len(triangles)}")

    # Подсчёт использования материалов
    material_usage = {i: 0 for i in range(len(geometry.materials))}
    for tri in triangles:
        if tri.material in material_usage:
            material_usage[tri.material] += 1

    print("Использование материалов:")
    for mat_idx, count in material_usage.items():
        print(f"Материал {mat_idx}: {count} треугольников")

    # Добавление треугольников
    skipped_triangles = 0
    for tri in triangles:
        try:
            face = bm.faces.new((bm.verts[tri.b], bm.verts[tri.a], bm.verts[tri.c]))
            if tri.material in material_indices:
                face.material_index = material_indices[tri.material]
            else:
                face.material_index = 0
                print(f"Треугольник использует несуществующий материал {tri.material}, присвоен материал 0")
            
            # Применение UV-координат
            for uv_layer_idx, uv_layer in enumerate(uv_layers):
                if uv_layer_idx < len(geometry.uv_layers):
                    for i, loop in enumerate(face.loops):
                        vert_idx = [tri.b, tri.a, tri.c][i]
                        uv = geometry.uv_layers[uv_layer_idx][vert_idx]
                        loop[uv_layer].uv = (uv.u, uv.v)
        except ValueError as e:
            skipped_triangles += 1
            print(f"Пропущен треугольник в модели {model_name}: {e}")
            continue

    if skipped_triangles > 0:
        print(f"Пропущено {skipped_triangles} треугольников из-за ошибок")

    # Финализация меша
    bm.to_mesh(mesh)
    bm.free()

    if geometry.uv_layers and len(geometry.uv_layers) > 0:
        mesh.uv_layers[0].name = "UVMap"
        mesh.uv_layers[0].active = True
        print(f"UV-слой активирован: UVMap")

    print(f"Импорт модели {model_name} завершён успешно")
    return obj

def place_objects(objects, dff_folder=None, img_path=None, dir_path=None):
    files_dict = None
    if img_path:
        if not os.path.exists(img_path):
            print(f"Ошибка: IMG-архив не найден: {img_path}")
            return
        files_dict = parse_img(img_path, dir_path)
        print(f"IMG-архив распарсен, найдено {len(files_dict)} файлов")
    
    for obj_data in objects:
        model_name = obj_data['model_name']
        print(f"Обработка объекта: {model_name}")
        try:
            if img_path and files_dict:
                dff_data = extract_dff_from_img(img_path, model_name, files_dict)
                obj = import_dff(model_name, dff_data)
            else:
                obj = import_dff(model_name, dff_folder)
            
            if obj:
                obj.location = obj_data['pos']
                obj.rotation_mode = 'QUATERNION'
                obj.rotation_quaternion = obj_data['rot']
                obj['id'] = int(obj_data['id'])
                obj['interior'] = int(obj_data['interior'])
                obj['lod'] = int(obj_data['lod']) if obj_data['lod'] else -1
                bpy.context.collection.objects.link(obj)
                print(f"Объект {model_name} успешно размещён")
            else:
                print(f"Пропущен объект {model_name} из-за ошибки импорта")
        except Exception as e:
            print(f"Ошибка при размещении объекта {model_name}: {e}")
            continue

def export_ipl(ipl_path, objects, lod_autosearch=False):
    lod_dict = {}
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
            model_name = obj.name
            pos = (obj.location.x, obj.location.y, obj.location.z)
            rot = obj.rotation_quaternion
            interior = obj.get('interior', 0)
            lod_index = obj.get('lod', -1)
            if lod_autosearch and model_name in lod_dict:
                lod_index = lod_dict[model_name].get('id', -1)
            line = f"{obj['id']}, {model_name}, {interior}, {pos[0]:.6f}, {pos[1]:.6f}, {pos[2]:.6f}, {rot[1]:.6f}, {rot[2]:.6f}, {rot[3]:.6f}, {rot[0]:.6f}, {lod_index}\n"
            file.write(line)
        file.write("end\n")
    print(f"Экспортировано {len(objects)} объектов в IPL: {ipl_path}")

def export_ide(ide_path, objects):
    with open(ide_path, 'w') as file:
        file.write("objs\n")
        for obj in objects:
            if 'id' not in obj:
                continue
            model_name = obj.name
            txd_name = obj.get('txd_name', f"{model_name}_tex")
            distance = obj.get('distance', 300.0)
            flags = obj.get('flag', 0)
            line = f"{obj['id']}, {model_name}, {txd_name}, {distance:.1f}, {flags}\n"
            file.write(line)
        file.write("end\n")
    print(f"Экспортировано {len(objects)} объектов в IDE: {ide_path}")

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
