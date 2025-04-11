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
import sys
import os
import bmesh
import importlib
import subprocess
import numpy as np

# Путь для установки Pillow внутри аддона
addon_dir = os.path.dirname(__file__)
pil_path = os.path.join(addon_dir, "PIL")
if pil_path not in sys.path:
    sys.path.insert(0, pil_path)

def ensure_pillow_installed():
    """Проверяет наличие Pillow и устанавливает его в папку аддона, если отсутствует."""
    try:
        from PIL import Image
        print("Pillow уже доступен")
        return True
    except ImportError:
        print("Pillow не найден, пытаюсь установить в папку аддона...")
        try:
            python_exe = os.path.join(sys.prefix, "bin", "python.exe") if os.name == 'nt' else sys.executable
            subprocess.check_call([python_exe, "-m", "ensurepip"])
            subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
            subprocess.check_call([python_exe, "-m", "pip", "install", "Pillow", "--target", pil_path, "--upgrade"])
            importlib.invalidate_caches()
            from PIL import Image
            print("Pillow успешно установлен в папку аддона")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Ошибка установки Pillow: {e}")
            print("Проверьте интернет-соединение или попробуйте установить вручную.")
            return False
        except Exception as e:
            print(f"Не удалось установить Pillow: {e}")
            return False

if not ensure_pillow_installed():
    print("Внимание: Pillow не установлен, импорт текстур работать не будет!")

from struct import unpack
from .dff import dff
from .txd import txd
from PIL import Image

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
    else:
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

def extract_dff_and_txd_from_img(img_path, model_name, files_dict):
    model_name = model_name.lower()
    dff_key = model_name if model_name in files_dict else model_name + '.dff'
    txd_key = model_name if model_name in files_dict else model_name + '.txd'
    
    dff_data = None
    txd_data = None
    
    if dff_key not in files_dict:
        print(f"Модель {model_name}.dff не найдена в IMG-архиве")
    else:
        offset, size = files_dict[dff_key]
        with open(img_path, 'rb') as img_file:
            img_file.seek(offset)
            dff_data = img_file.read(size)
        print(f"Извлечён {dff_key} из IMG")

    if txd_key not in files_dict:
        print(f"Текстуры {model_name}.txd не найдены в IMG-архиве")
    else:
        offset, size = files_dict[txd_key]
        with open(img_path, 'rb') as img_file:
            img_file.seek(offset)
            txd_data = img_file.read(size)
        print(f"Извлечён {txd_key} из IMG")
    
    return dff_data, txd_data

def extract_textures_from_txd(txd_data, output_dir):
    if not txd_data:
        print("Нет данных TXD для обработки")
        return {}
    
    texture_dict = {}
    txd_loader = txd()
    try:
        txd_loader.load_memory(txd_data)
    except Exception as e:
        print(f"Ошибка загрузки TXD: {e}")
        return {}
    
    try:
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        print(f"Ошибка создания директории {output_dir}: {e}")
        return {}
    
    for texture in txd_loader.native_textures:
        try:
            rgba_data = texture.to_rgba(level=0)
            width = texture.get_width(0)
            height = texture.get_height(0)
            
            if rgba_data and width > 0 and height > 0:
                img = Image.frombytes("RGBA", (width, height), rgba_data)
                texture_path = os.path.join(output_dir, f"{texture.name}.png")
                img.save(texture_path, "PNG")
                texture_dict[texture.name.lower()] = texture_path
                print(f"Сохранена текстура: {texture_path}")
            else:
                print(f"Не удалось декодировать текстуру {texture.name}: нет данных или неверные размеры")
        except Exception as e:
            print(f"Ошибка сохранения текстуры {texture.name}: {e}")
            continue
    
    return texture_dict

def filter_triangles(vertices, triangles):
    """Фильтрует дегенеративные треугольники."""
    filtered = []
    for tri in triangles:
        if tri.b >= len(vertices) or tri.a >= len(vertices) or tri.c >= len(vertices):
            print(f"Пропущен треугольник: неверные индексы b={tri.b}, a={tri.a}, c={tri.c}")
            continue
        v0 = np.array([vertices[tri.a].x, vertices[tri.a].y, vertices[tri.a].z])
        v1 = np.array([vertices[tri.b].x, vertices[tri.b].y, vertices[tri.b].z])
        v2 = np.array([vertices[tri.c].x, vertices[tri.c].y, vertices[tri.c].z])
        if np.allclose(v0, v1) or np.allclose(v1, v2) or np.allclose(v0, v2):
            print(f"Пропущен треугольник: дегенеративный (b={tri.b}, a={tri.a}, c={tri.c})")
            continue
        filtered.append(tri)
    print(f"Отфильтровано треугольников: {len(triangles)} -> {len(filtered)}")
    return filtered

def import_dff(model_name, dff_source, texture_dict=None):
    if texture_dict is None:
        texture_dict = {}
    
    print(f"Начало импорта модели: {model_name}")
    dff_loader = dff()
    
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

    triangles = geometry.extensions.get('mat_split', geometry.triangles)
    triangles = filter_triangles(geometry.vertices, triangles)
    print(f"Источник треугольников: {'Bin Mesh PLG' if triangles is not geometry.triangles else 'Geometry'}, всего {len(triangles)}")

    mesh = bpy.data.meshes.new(model_name)
    obj = bpy.data.objects.new(model_name, mesh)
    bm = bmesh.new()

    print(f"Добавление {len(geometry.vertices)} вершин в меш")
    for vert in geometry.vertices:
        bm.verts.new((vert.x, vert.y, vert.z))
    bm.verts.ensure_lookup_table()

    uv_layers = []
    for i in range(len(geometry.uv_layers)):
        uv_layer = bm.loops.layers.uv.new(f"UVMap_{i}")
        uv_layers.append(uv_layer)
        print(f"Создан UV-слой: UVMap_{i}")

    material_indices = {}
    if geometry.materials:
        print(f"Обнаружено {len(geometry.materials)} материалов")
        for i, mat in enumerate(geometry.materials):
            mat_name = f"{model_name}_mat_{i}"
            has_texture = mat.textures and len(mat.textures) > 0

            if has_texture:
                tex_name = mat.textures[0].name.lower()
                mat_name = tex_name if tex_name else mat_name
                print(f"Материал {i}: {mat_name} с текстурой {tex_name}")
            else:
                print(f"Материал {i}: {mat_name} без текстуры")

            bpy_mat = bpy.data.materials.new(name=mat_name)
            bpy_mat.use_nodes = True
            nodes = bpy_mat.node_tree.nodes
            links = bpy_mat.node_tree.links

            principled = nodes.new("ShaderNodeBsdfPrincipled")
            output = nodes.get("Material Output") or nodes.new("ShaderNodeOutputMaterial")
            links.new(principled.outputs["BSDF"], output.inputs["Surface"])

            # Создаём узел Image Texture в любом случае, если есть текстура
            if has_texture:
                tex_node = nodes.new("ShaderNodeTexImage")
                # Если текстура импортируется (есть в texture_dict), загружаем её
                if tex_name in texture_dict:
                    texture_path = texture_dict[tex_name]
                    try:
                        if os.path.exists(texture_path):
                            tex_node.image = bpy.data.images.load(texture_path, check_existing=True)
                            print(f"Текстура {tex_name} загружена из {texture_path}")
                        else:
                            print(f"Текстура {tex_name} не найдена по пути {texture_path}")
                    except Exception as e:
                        print(f"Ошибка загрузки текстуры {tex_name}: {e}")
                # Если текстуры не импортируются, задаём только имя файла
                else:
                    tex_node.image = bpy.data.images.new(name=f"{tex_name}.png", width=1, height=1)
                    tex_node.image.source = 'FILE'
                    tex_node.image.filepath = f"{tex_name}.png"  # Только имя файла
                    print(f"Задана текстура {tex_name}.png для поиска в папке с .blend")
                links.new(tex_node.outputs["Color"], principled.inputs["Base Color"])
            # Если текстуры нет, используем цвет, если он есть
            elif mat.color:
                color = (mat.color.r / 255.0, mat.color.g / 255.0, mat.color.b / 255.0, mat.color.a / 255.0)
                principled.inputs["Base Color"].default_value = color
                print(f"Установлен цвет материала {mat_name}: {color}")

            mesh.materials.append(bpy_mat)
            material_indices[i] = i

    material_usage = {i: 0 for i in range(len(geometry.materials))}
    for tri in triangles:
        if tri.material in material_usage:
            material_usage[tri.material] += 1

    print("Использование материалов:")
    for mat_idx, count in material_usage.items():
        print(f"Материал {mat_idx}: {count} треугольников")

    skipped_triangles = 0
    for tri in triangles:
        try:
            face = bm.faces.new((bm.verts[tri.a], bm.verts[tri.b], bm.verts[tri.c]))
            if tri.material in material_indices:
                face.material_index = material_indices[tri.material]
            else:
                face.material_index = 0
            
            for uv_layer_idx, uv_layer in enumerate(uv_layers):
                if uv_layer_idx < len(geometry.uv_layers):
                    for i, loop in enumerate(face.loops):
                        vert_idx = [tri.a, tri.b, tri.c][i]
                        uv = geometry.uv_layers[uv_layer_idx][vert_idx]
                        loop[uv_layer].uv = (uv.u, 1.0 - uv.v)
        except ValueError as e:
            skipped_triangles += 1
            print(f"Пропущен треугольник в модели {model_name}: {e}")
            continue

    if skipped_triangles > 0:
        print(f"Пропущено {skipped_triangles} треугольников из-за ошибок")

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
    
    # Определяем папку для текстур только если импорт текстур включён
    import_textures = bpy.context.scene.get('import_textures', False)  # По умолчанию False
    texture_output_dir = None
    if import_textures:
        if bpy.data.filepath:
            texture_output_dir = os.path.join(os.path.dirname(bpy.data.filepath), "textures")
            print(f"Текстуры будут сохранены в: {texture_output_dir}")
        else:
            import tempfile
            texture_output_dir = os.path.join(tempfile.gettempdir(), "gta_textures")
            print(f"Файл .blend не сохранён, текстуры будут сохранены во временную папку: {texture_output_dir}")
        
        try:
            os.makedirs(texture_output_dir, exist_ok=True)
        except PermissionError as e:
            print(f"Ошибка создания папки {texture_output_dir}: {e}")
            print("Попробуйте запустить Blender от имени администратора или сохранить .blend в другой директории")
            return
    
    for obj_data in objects:
        model_name = obj_data['model_name']
        print(f"Обработка объекта: {model_name}")
        try:
            if img_path and files_dict:
                dff_data, txd_data = extract_dff_and_txd_from_img(img_path, model_name, files_dict)
                # Извлекаем текстуры только если import_textures включён
                texture_dict = {}
                if import_textures and txd_data:
                    texture_dict = extract_textures_from_txd(txd_data, texture_output_dir)
                    # Если .blend сохранён, преобразуем пути текстур в относительные
                    if bpy.data.filepath:
                        rel_texture_dict = {}
                        for tex_name, tex_path in texture_dict.items():
                            rel_path = bpy.path.relpath(tex_path)
                            rel_texture_dict[tex_name] = rel_path
                            print(f"Преобразован путь текстуры {tex_name}: {tex_path} -> {rel_path}")
                        texture_dict = rel_texture_dict
                obj = import_dff(model_name, dff_data, texture_dict)
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
            warnings.append(f"[WARNING #4] LOD Rt {obj.name} имеет некорректное имя")

    return errors, warnings
