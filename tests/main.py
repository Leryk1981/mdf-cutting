import os
import sys

import pandas as pd

from packer.test_packing import test_maxrects_blsf, test_various_algorithms
from packer.utils import preprocess_dataframes, set_log_level

# Расширенный список кодировок для попыток чтения
EXTENDED_ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "windows-1251",
    "cp1252",
    "latin1",
    "iso-8859-1",
]


def read_csv_with_encoding(file_path):
    """Читает CSV-файл с перебором различных кодировок"""
    for encoding in EXTENDED_ENCODINGS:
        try:
            print(f"Пробуем кодировку {encoding} для {file_path}")
            df = pd.read_csv(
                file_path, sep=";", encoding=encoding, low_memory=False
            )
            print(f"Успешно прочитан файл с кодировкой: {encoding}")
            return df
        except Exception as e:
            print(f"Ошибка чтения с кодировкой {encoding}: {str(e)}")

    # Последняя попытка - чтение с опцией errors='replace'
    try:
        print("Попытка чтения с опцией errors='replace'")
        df = pd.read_csv(
            file_path,
            sep=";",
            encoding="utf-8",
            errors="replace",
            low_memory=False,
        )
        print("Успешно прочитан файл с заменой проблемных символов")
        return df
    except Exception as e:
        print(f"Не удалось прочитать файл: {str(e)}")

    return None


def main():
    # Определение базовой директории
    if getattr(sys, "frozen", False):
        # Работаем из EXE
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        # Работаем из скрипта
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Указываем конкретные пути к файлам
    details_path = os.path.join(base_dir, "packer", "processed_data.csv")
    materials_path = os.path.join(base_dir, "packer", "materials.csv")

    # Проверка существования файлов
    if not os.path.exists(details_path):
        print(f"ОШИБКА: Файл деталей не существует: {details_path}")
        custom_details = input("Введите полный путь к файлу деталей: ")
        if custom_details and os.path.exists(custom_details):
            details_path = custom_details
        else:
            print("Некорректный путь к файлу деталей")
            return

    if not os.path.exists(materials_path):
        print(f"ОШИБКА: Файл материалов не существует: {materials_path}")
        custom_materials = input("Введите полный путь к файлу материалов: ")
        if custom_materials and os.path.exists(custom_materials):
            materials_path = custom_materials
        else:
            print("Некорректный путь к файлу материалов")
            return

    # Директория вывода
    output_dir = os.path.join(base_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Используемые пути:")
    print(f"Файл деталей: {details_path}")
    print(f"Файл материалов: {materials_path}")
    print(f"Директория вывода: {output_dir}")

    # Устанавливаем уровень логирования
    set_log_level("INFO")

    # Чтение CSV файлов с перебором кодировок
    print(f"Чтение файлов: {details_path}, {materials_path}")
    details_df = read_csv_with_encoding(details_path)
    materials_df = read_csv_with_encoding(materials_path)

    if details_df is None or materials_df is None:
        print("Ошибка чтения CSV-файлов!")
        return

    # Предобработка данных
    details_df, materials_df = preprocess_dataframes(details_df, materials_df)

    if details_df is None or materials_df is None:
        print("Ошибка при предобработке данных!")
        return

    # Проверка наличия колонки is_remnant
    if "is_remnant" not in materials_df.columns:
        materials_df["is_remnant"] = False
        print("Добавлена колонка 'is_remnant' со значением False")

    # Запуск тестирования алгоритмов
    print(
        "\n=== Запуск тестирования алгоритма MAXRECTS-BLSF с разными сортировками ==="
    )

    # Включаем режим принудительного поворота больших деталей
    force_rotate_large = True
    rotate_text = (
        "с принудительным поворотом больших деталей"
        if force_rotate_large
        else "без принудительного поворота"
    )

    # Тест с сортировкой "big_first"
    print(
        f"\n>> Тест с сортировкой 'big_first' (сначала большие детали) {rotate_text}:"
    )
    packers1, used_sheets1, layout_count1 = test_maxrects_blsf(
        details_df,
        materials_df,
        output_dir,
        margin=6,
        kerf=4,
        sort_mode="big_first",
        force_rotate_large=force_rotate_large,
    )

    # Тест с сортировкой "medium_first"
    print(
        f"\n>> Тест с сортировкой 'medium_first' (сначала средние детали) {rotate_text}:"
    )
    packers2, used_sheets2, layout_count2 = test_maxrects_blsf(
        details_df,
        materials_df,
        output_dir,
        margin=6,
        kerf=4,
        sort_mode="medium_first",
        force_rotate_large=force_rotate_large,
    )

    # Сравнение результатов
    print("\n=== Сравнение результатов сортировок ===")
    print(
        f"big_first {rotate_text}: {used_sheets1} листов, {layout_count1} карт раскроя"
    )
    print(
        f"medium_first {rotate_text}: {used_sheets2} листов, {layout_count2} карт раскроя"
    )

    # Тест разных алгоритмов упаковки
    run_algorithm_comparison = True
    if run_algorithm_comparison:
        print(
            f"\n=== Запуск сравнительного тестирования различных алгоритмов упаковки {rotate_text} ==="
        )
        results = test_various_algorithms(
            details_df,
            materials_df,
            output_dir,
            margin=6,
            kerf=4,
            force_rotate_large=force_rotate_large,
        )

        # Вывод итоговой таблицы
        print(f"\n=== Итоговые результаты всех тестов {rotate_text} ===")
        print("| Алгоритм | Листов | Карт раскроя |")
        print("|----------|--------|-------------|")
        print(f"| BLSF (big_first) | {used_sheets1} | {layout_count1} |")
        print(f"| BLSF (medium_first) | {used_sheets2} | {layout_count2} |")

        for algo_name, result in results.items():
            if algo_name != "MaxRectsBlsf":  # Избегаем дублирования
                print(
                    f"| {algo_name} | {result['total_sheets']} | {result['layout_count']} |"
                )


if __name__ == "__main__":
    main()
