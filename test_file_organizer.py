#!/usr/bin/env python3
"""
Тест для проверки организации файлов по папкам
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Добавляем путь к модулю packer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from packer.file_organizer import create_material_folder_structure, get_organized_file_path


def test_folder_creation():
    """Тестируем создание структуры папок"""
    print("=== Тестирование создания структуры папок ===")
    
    # Создаем временную директорию для тестов
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Временная директория: {temp_dir}")
        
        # Тест 1: Создание папки для стандартного материала (S)
        print("\n--- Тест 1: Материал S, толщина 16 ---")
        main_folder, clean_folder = create_material_folder_structure(16, 'S', temp_dir)
        print(f"Основная папка: {main_folder}")
        print(f"Clean папка: {clean_folder}")
        
        # Проверяем, что папки созданы
        assert os.path.exists(main_folder), "Основная папка не создана"
        assert os.path.exists(clean_folder), "Clean папка не создана"
        
        # Проверяем названия папок
        expected_main = os.path.join(temp_dir, "16mm")
        expected_clean = os.path.join(temp_dir, "16mm", "16mm_clean")
        assert main_folder == expected_main, f"Неправильное название основной папки: {main_folder}"
        assert clean_folder == expected_clean, f"Неправильное название clean папки: {clean_folder}"
        print("✓ Тест 1 пройден")
        
        # Тест 2: Создание папки для материала V, толщина 18
        print("\n--- Тест 2: Материал V, толщина 18 ---")
        main_folder2, clean_folder2 = create_material_folder_structure(18, 'V', temp_dir)
        print(f"Основная папка: {main_folder2}")
        print(f"Clean папка: {clean_folder2}")
        
        # Проверяем, что папки созданы
        assert os.path.exists(main_folder2), "Основная папка не создана"
        assert os.path.exists(clean_folder2), "Clean папка не создана"
        
        # Проверяем названия папок
        expected_main2 = os.path.join(temp_dir, "18mm_V")
        expected_clean2 = os.path.join(temp_dir, "18mm_V", "18mm_V_clean")
        assert main_folder2 == expected_main2, f"Неправильное название основной папки: {main_folder2}"
        assert clean_folder2 == expected_clean2, f"Неправильное название clean папки: {clean_folder2}"
        print("✓ Тест 2 пройден")
        
        # Тест 3: Создание папки для дробной толщины
        print("\n--- Тест 3: Материал S, толщина 15.5 ---")
        main_folder3, clean_folder3 = create_material_folder_structure(15.5, 'S', temp_dir)
        print(f"Основная папка: {main_folder3}")
        print(f"Clean папка: {clean_folder3}")
        
        # Проверяем, что папки созданы
        assert os.path.exists(main_folder3), "Основная папка не создана"
        assert os.path.exists(clean_folder3), "Clean папка не создана"
        
        # Проверяем названия папок для дробной толщины
        expected_main3 = os.path.join(temp_dir, "15.5mm")
        expected_clean3 = os.path.join(temp_dir, "15.5mm", "15.5mm_clean")
        assert main_folder3 == expected_main3, f"Неправильное название основной папки: {main_folder3}"
        assert clean_folder3 == expected_clean3, f"Неправильное название clean папки: {clean_folder3}"
        print("✓ Тест 3 пройден")
        
        print("\n=== Все тесты создания папок пройдены! ===")


def test_file_path_organization():
    """Тестируем получение организованных путей к файлам"""
    print("\n=== Тестирование организации путей файлов ===")
    
    # Создаем временную директорию для тестов
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Временная директория: {temp_dir}")
        
        # Тест 1: Путь к файлу для стандартного материала
        print("\n--- Тест 1: Путь файла для материала S, толщина 16 ---")
        filename = "sheet_16mm_0.dxf"
        file_path = get_organized_file_path(16, 'S', filename, temp_dir)
        print(f"Полный путь: {file_path}")
        
        expected_path = os.path.join(temp_dir, "16mm", filename)
        assert file_path == expected_path, f"Неправильный путь: {file_path}"
        
        # Проверяем, что папка создана
        parent_dir = os.path.dirname(file_path)
        assert os.path.exists(parent_dir), "Родительская папка не создана"
        print("✓ Тест 1 пройден")
        
        # Тест 2: Путь к файлу для материала V
        print("\n--- Тест 2: Путь файла для материала V, толщина 18 ---")
        filename2 = "12_800x600_18mm_V.dxf"
        file_path2 = get_organized_file_path(18, 'V', filename2, temp_dir)
        print(f"Полный путь: {file_path2}")
        
        expected_path2 = os.path.join(temp_dir, "18mm_V", filename2)
        assert file_path2 == expected_path2, f"Неправильный путь: {file_path2}"
        
        # Проверяем, что папка создана
        parent_dir2 = os.path.dirname(file_path2)
        assert os.path.exists(parent_dir2), "Родительская папка не создана"
        
        # Проверяем, что clean папка тоже создана
        clean_dir = os.path.join(parent_dir2, "18mm_V_clean")
        assert os.path.exists(clean_dir), "Clean папка не создана"
        print("✓ Тест 2 пройден")
        
        print("\n=== Все тесты организации путей пройдены! ===")


def test_real_world_scenario():
    """Тестируем реальный сценарий использования"""
    print("\n=== Тестирование реального сценария ===")
    
    # Создаем временную директорию для тестов
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Временная директория: {temp_dir}")
        
        # Имитируем создание нескольких файлов карт раскроя
        test_files = [
            (16, 'S', 'sheet_16mm_0.dxf'),
            (16, 'S', 'sheet_16mm_1.dxf'),
            (18, 'V', '12_800x600_18mm_V.dxf'),
            (18, 'V', '15_1200x800_18mm_V.dxf'),
            (20, 'L', 'sheet_20mm_L_0.dxf'),
        ]
        
        created_files = []
        
        for thickness, material, filename in test_files:
            # Получаем организованный путь
            file_path = get_organized_file_path(thickness, material, filename, temp_dir)
            
            # Создаем пустой файл для проверки
            with open(file_path, 'w') as f:
                f.write(f"Test file: {filename}")
            
            created_files.append(file_path)
            print(f"Создан файл: {file_path}")
        
        # Проверяем структуру созданных папок
        print("\n--- Проверка структуры папок ---")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(temp_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{sub_indent}{file}")
        
        # Проверяем, что все файлы созданы
        for file_path in created_files:
            assert os.path.exists(file_path), f"Файл не создан: {file_path}"
        
        # Проверяем, что clean папки созданы
        expected_clean_dirs = [
            os.path.join(temp_dir, "16mm", "16mm_clean"),
            os.path.join(temp_dir, "18mm_V", "18mm_V_clean"),
            os.path.join(temp_dir, "20mm_L", "20mm_L_clean"),
        ]
        
        for clean_dir in expected_clean_dirs:
            assert os.path.exists(clean_dir), f"Clean папка не создана: {clean_dir}"
            print(f"✓ Clean папка создана: {clean_dir}")
        
        print("\n=== Реальный сценарий выполнен успешно! ===")


if __name__ == "__main__":
    try:
        print("Запуск тестов организации файлов по папкам...")
        
        test_folder_creation()
        test_file_path_organization()
        test_real_world_scenario()
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО! 🎉")
        print("\nОрганизация файлов по папкам работает корректно:")
        print("✓ Папки создаются по шаблону: {толщина}mm_{материал}")
        print("✓ Внутри каждой папки создается пустая папка {название}_clean")
        print("✓ Карты раскроя сохраняются в соответствующие папки")
        print("✓ Карты на листах и остатках с одинаковой толщиной и материалом попадают в одну папку")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
