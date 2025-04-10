import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import threading
import numpy as np

from packer.config import logger, setup_logging
from packer.constants import (
    MATERIALS_REQUIRED_COLUMNS,
    DETAILS_REQUIRED_COLUMNS,
    DEFAULT_MARGIN,
    DEFAULT_KERF,
    SUPPORTED_ENCODINGS
)
from packer.cleanup import CleanupManager
from packer.remnants import RemnantsManager
from packer.packing import pack_and_generate_dxf
from packer.utils import (
    set_log_level,
    read_csv_files,
    validate_dataframes,
    preprocess_dataframes,
    check_critical_values
)


class CuttingAppGUI:
    """Графический интерфейс приложения"""

    def __init__(self, root):
        self.root = root
        self.root.title("Раскрой MDF Накладок")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)

        self.cleanup_manager = CleanupManager()
        self.remnants_manager = RemnantsManager()
        self.cutting_thread = None  # Атрибут для хранения потока

        # Пути по умолчанию
        if getattr(sys, 'frozen', False):
            # Работаем из EXE
            base_dir = getattr(
                sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            # Работаем из скрипта
            base_dir = os.path.dirname(os.path.abspath(__file__))

        # Пути к файлам
        self.details_path = os.path.join(base_dir, "processed_data.csv")
        self.materials_path = os.path.join(base_dir, "materials.csv")
        self.pattern_dir = os.path.join(base_dir, "patterns")
        self.output_dir = os.path.dirname(base_dir) if getattr(
            sys, 'frozen', False) else base_dir

        # Создаем интерфейс
        self.create_input_frame()
        self.create_options_frame()
        self.create_log_frame()
        self.create_action_frame()

        # Проверяем наличие файлов
        self.check_files()
        self.setup_log_redirect()

        # Добавим метод проверки возможности активации кнопки
        self.check_run_button_state()

    def setup_log_redirect(self):
        """Перенаправляет вывод в текстовый виджет"""
        class TextRedirector:
            def __init__(self, widget):
                self.widget = widget

            def write(self, text):
                self.widget.insert(tk.END, text)
                self.widget.see(tk.END)

            def flush(self):
                pass

        sys.stdout = TextRedirector(self.log_text)
        sys.stderr = TextRedirector(self.log_text)

    def create_input_frame(self):
        """Создает фрейм для ввода путей к файлам"""
        frame = ttk.LabelFrame(self.root, text="Входные файлы")
        frame.pack(fill="x", expand=False, padx=10, pady=5)

        # Файл деталей
        ttk.Label(frame, text="Файл деталей (processed_data.csv):").grid(
            row=0, column=0, sticky="w", padx=5, pady=2)
        self.details_entry = ttk.Entry(frame, width=50)
        self.details_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.details_entry.insert(0, self.details_path)
        ttk.Button(frame, text="Обзор", command=self.select_details_file).grid(
            row=0, column=2, padx=5, pady=2)

        # Файл материалов
        ttk.Label(frame, text="Файл материалов (materials.csv):").grid(
            row=1, column=0, sticky="w", padx=5, pady=2)
        self.materials_entry = ttk.Entry(frame, width=50)
        self.materials_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.materials_entry.insert(0, self.materials_path)
        ttk.Button(frame, text="Обзор", command=self.select_materials_file).grid(
            row=1, column=2, padx=5, pady=2)

        # Директория узоров
        ttk.Label(frame, text="Папка с узорами:").grid(
            row=2, column=0, sticky="w", padx=5, pady=2)
        self.pattern_dir_entry = ttk.Entry(frame, width=50)
        self.pattern_dir_entry.grid(
            row=2, column=1, padx=5, pady=2, sticky="ew")
        self.pattern_dir_entry.insert(0, self.pattern_dir)
        ttk.Button(frame, text="Обзор", command=self.select_pattern_dir).grid(
            row=2, column=2, padx=5, pady=2)

        # Директория вывода
        ttk.Label(frame, text="Папка для выходных файлов:").grid(
            row=3, column=0, sticky="w", padx=5, pady=2)
        self.output_dir_entry = ttk.Entry(frame, width=50)
        self.output_dir_entry.grid(
            row=3, column=1, padx=5, pady=2, sticky="ew")
        self.output_dir_entry.insert(0, self.output_dir)
        ttk.Button(frame, text="Обзор", command=self.select_output_dir).grid(
            row=3, column=2, padx=5, pady=2)

        frame.columnconfigure(1, weight=1)

    def create_options_frame(self):
        """Создает фрейм для настроек"""
        frame = ttk.LabelFrame(self.root, text="Настройки")
        frame.pack(fill="x", expand=False, padx=10, pady=5)

        # Настройка отступа
        ttk.Label(frame, text="Отступ (мм):").grid(
            row=0, column=0, sticky="w", padx=5, pady=2)
        self.margin_var = tk.DoubleVar(value=DEFAULT_MARGIN)
        ttk.Entry(frame, textvariable=self.margin_var, width=10).grid(
            row=0, column=1, padx=5, pady=2)

        # Настройка реза
        ttk.Label(frame, text="Рез (мм):").grid(
            row=1, column=0, sticky="w", padx=5, pady=2)
        self.kerf_var = tk.DoubleVar(value=DEFAULT_KERF)
        ttk.Entry(frame, textvariable=self.kerf_var, width=10).grid(
            row=1, column=1, padx=5, pady=2)

        # Настройка сохранения временных файлов
        self.keep_files_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Сохранять временные файлы", variable=self.keep_files_var).grid(
            row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)

    def create_log_frame(self):
        """Создает фрейм для логов"""
        frame = ttk.LabelFrame(self.root, text="Логи")
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Текстовое поле для логов
        self.log_text = tk.Text(frame, height=10, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Прокрутка для логов
        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

    def create_action_frame(self):
        """Создает фрейм для кнопок действий"""
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", expand=False, padx=10, pady=5)

        # Кнопка запуска
        self.run_button = ttk.Button(
            frame, text="Запустить раскрой", command=self.run_cutting, state="disabled")
        self.run_button.pack(side="left", padx=5)

        # Кнопка очистки
        ttk.Button(frame, text="Очистить", command=self.clear_all).pack(
            side="left", padx=5)

        # Кнопка очистки логов
        ttk.Button(frame, text="Очистить логи", command=self.clear_logs).pack(
            side="left", padx=5)

        # Уровень логирования
        ttk.Label(frame, text="Уровень логирования:").pack(side="left", padx=5)
        self.log_level_combo = ttk.Combobox(
            frame, values=["INFO", "DEBUG", "WARNING", "ERROR"], state="readonly")
        self.log_level_combo.set("INFO")
        self.log_level_combo.pack(side="left", padx=5)
        self.log_level_combo.bind(
            "<<ComboboxSelected>>", self.change_log_level)

        # Статус
        self.status_label = ttk.Label(frame, text="Инициализация...")
        self.status_label.pack(side="right", padx=5)

    def select_details_file(self):
        """Выбор файла деталей"""
        filename = filedialog.askopenfilename(
            title="Выберите файл деталей",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.details_entry.delete(0, tk.END)
            self.details_entry.insert(0, filename)
            self.check_run_button_state()  # Проверяем состояние после выбора

    def select_materials_file(self):
        """Выбор файла материалов"""
        filename = filedialog.askopenfilename(
            title="Выберите файл материалов",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.materials_entry.delete(0, tk.END)
            self.materials_entry.insert(0, filename)
            self.check_run_button_state()  # Проверяем состояние после выбора

    def select_pattern_dir(self):
        """Выбор директории с шаблонами"""
        dirname = filedialog.askdirectory(
            title="Выберите директорию с шаблонами")
        if dirname:
            self.pattern_dir_entry.delete(0, tk.END)
            self.pattern_dir_entry.insert(0, dirname)
            self.check_run_button_state()  # Проверяем состояние после выбора

    def select_output_dir(self):
        """Выбор директории для результатов"""
        dirname = filedialog.askdirectory(
            title="Выберите директорию для результатов")
        if dirname:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, dirname)
            self.check_run_button_state()  # Проверяем состояние после выбора

    def check_run_button_state(self):
        """Проверяет возможность активации кнопки раскроя"""
        try:
            details_path = self.details_entry.get()
            materials_path = self.materials_entry.get()
            pattern_dir = self.pattern_dir_entry.get()
            output_dir = self.output_dir_entry.get()

            # Проверяем наличие всех необходимых файлов и директорий
            if (os.path.isfile(details_path) and
                os.path.isfile(materials_path) and
                os.path.isdir(pattern_dir) and
                    os.path.isdir(output_dir)):
                self.run_button.config(state="normal")
            else:
                self.run_button.config(state="disabled")
        except Exception as e:
            logger.error(f"Ошибка при проверке состояния кнопки: {e}")
            self.run_button.config(state="disabled")

    def check_files(self):
        """Проверяет наличие необходимых файлов"""
        self.details_path = self.details_entry.get()
        self.materials_path = self.materials_entry.get()
        self.pattern_dir = self.pattern_dir_entry.get()

        files_ok = True

        # Проверка файла деталей
        if not os.path.exists(self.details_path):
            logger.warning(f"Файл деталей не найден: {self.details_path}")
            files_ok = False

        # Проверка файла материалов
        if not os.path.exists(self.materials_path):
            logger.warning(f"Файл материалов не найден: {self.materials_path}")
            files_ok = False

        # Проверка директории узоров
        if not os.path.exists(self.pattern_dir):
            logger.warning(
                f"Папка с узорами не найдена: {self.pattern_dir}, будет создана")
            try:
                os.makedirs(self.pattern_dir)
                logger.info(f"Создана директория: {self.pattern_dir}")
            except Exception as e:
                logger.error(f"Не удалось создать директорию: {str(e)}")

        # Проверка директории вывода
        self.output_dir = self.output_dir_entry.get()
        if not os.path.exists(self.output_dir):
            logger.warning(
                f"Папка для выходных файлов не найдена: {self.output_dir}, будет создана")
            try:
                os.makedirs(self.output_dir)
                logger.info(
                    f"Создана директория для выходных файлов: {self.output_dir}")
            except Exception as e:
                logger.error(f"Не удалось создать директорию: {str(e)}")
                files_ok = False

        # Обновление статуса
        if files_ok:
            self.status_label.config(text="Файлы проверены, готов к запуску")
            self.run_button.config(state="normal")
        else:
            self.status_label.config(text="Ошибка проверки файлов")
            self.run_button.config(state="disabled")

        return files_ok

    def change_log_level(self, event=None):
        """Изменяет уровень логирования"""
        level = self.log_level_combo.get()
        set_log_level(level)
        logger.info(f"Уровень логирования изменён на: {level}")

    def clear_logs(self):
        """Очищает логи"""
        self.log_text.delete(1.0, tk.END)
        self.cleanup_manager.cleanup_logs()
        logger.info("Логи очищены")

    def clear_all(self):
        """Очищает все временные файлы и логи"""
        self.log_text.delete(1.0, tk.END)
        self.cleanup_manager.cleanup_all(keep_output=False)
        logger.info("Все временные файлы и логи очищены")
        self.check_files()

    def run_cutting(self):
        """Запускает процесс раскроя в отдельном потоке"""
        self.run_button.config(state="disabled")
        self.status_label.config(text="Выполняется раскрой...")
        self.cutting_thread = threading.Thread(
            target=self._cutting_thread, daemon=True)
        self.cutting_thread.start()

    def _cutting_thread(self):
        """Поток для выполнения раскроя"""
        try:
            logger.info("Начинается процесс раскроя")

            # Получаем параметры из интерфейса
            details_path = self.details_entry.get()
            materials_path = self.materials_entry.get()
            pattern_dir = self.pattern_dir_entry.get()
            output_dir = self.output_dir_entry.get()
            margin = self.margin_var.get()
            kerf = self.kerf_var.get()

            # Создаем менеджер остатков
            remnants_manager = RemnantsManager(
                margin=int(margin), kerf=int(kerf))

            # Читаем CSV файлы
            details_df, materials_df = read_csv_files(
                details_path, materials_path, SUPPORTED_ENCODINGS)

            if details_df is None or materials_df is None:
                logger.error("Не удалось прочитать CSV-файлы!")
                self.root.after(0, lambda: messagebox.showerror(
                    "Ошибка", "Не удалось прочитать CSV-файлы!"))
                self.root.after(0, self.finish_cutting_task)
                return

            # Проверяем наличие необходимых колонок
            is_valid, missing_cols_details, missing_cols_materials = validate_dataframes(
                details_df, materials_df, DETAILS_REQUIRED_COLUMNS, MATERIALS_REQUIRED_COLUMNS)

            if not is_valid:
                error_message = "Отсутствуют обязательные колонки:\n"
                if missing_cols_details:
                    error_message += f"В файле деталей: {', '.join(missing_cols_details)}\n"
                if missing_cols_materials:
                    error_message += f"В файле материалов: {', '.join(missing_cols_materials)}"
                logger.error(error_message)
                self.root.after(0, lambda: messagebox.showerror(
                    "Ошибка", error_message))
                self.root.after(0, self.finish_cutting_task)
                return

            # Предобработка данных
            details_df, materials_df = preprocess_dataframes(
                details_df, materials_df)

            if details_df is None or materials_df is None:
                self.root.after(0, lambda: messagebox.showerror(
                    "Ошибка", "Ошибка при предобработке данных!"))
                self.root.after(0, self.finish_cutting_task)
                return

            # Проверка критических значений
            if not check_critical_values(details_df, materials_df):
                self.root.after(0, lambda: messagebox.showerror(
                    "Ошибка", "Обнаружены некорректные значения в данных!"))
                self.root.after(0, self.finish_cutting_task)
                return

            # Переходим в директорию вывода
            current_dir = os.getcwd()
            os.chdir(output_dir)

            # Запускаем раскрой
            logger.info("Начинается процесс раскроя")
            packers_by_material, total_used_sheets = pack_and_generate_dxf(
                details_df, materials_df, pattern_dir, int(margin), int(kerf))

            # Обновляем таблицу материалов с учетом использованных листов и остатков
            updated_materials_df = materials_df.copy()

            # Проходимся по всем упаковщикам
            for material_key, packer in packers_by_material.items():
                try:
                    # Обрабатываем разные типы ключей (строка или число)
                    if isinstance(material_key, (float, int, np.float64, np.int64)):
                        # Если ключ - число, то толщина = ключ, материал = 'S' по умолчанию
                        thickness = float(material_key)
                        material = 'S'
                        logger.info(
                            f"Обработка числового ключа: {material_key} -> толщина={thickness}, материал={material}")
                    else:
                        # Если ключ - строка, разбиваем его на толщину и материал
                        key_parts = material_key.split('_', 1)
                        if len(key_parts) != 2:
                            logger.warning(
                                f"Некорректный ключ материала: {material_key}")
                            # Пробуем преобразовать в число
                            thickness = float(material_key)
                            material = 'S'
                        else:
                            thickness = float(key_parts[0])
                            material = key_parts[1]

                    if thickness <= 0:
                        logger.warning(
                            f"Пропуск материала с неположительной толщиной: {thickness}")
                        continue

                    logger.info(
                        f"Обработка остатков для комбинации: толщина={thickness}, материал={material}")

                    # Находим подходящие листы материала для этой комбинации
                    material_mask = (materials_df['thickness_mm'] == thickness) & (
                        materials_df['material'] == material)
                    material_sheets = materials_df[material_mask]

                    if material_sheets.empty:
                        logger.warning(
                            f"Не найдены материалы с комбинацией: толщина={thickness}, материал={material}")
                        continue

                    # Получаем размеры листа для этой комбинации
                    sheet_length = float(
                        material_sheets['sheet_length_mm'].iloc[0])
                    sheet_width = float(
                        material_sheets['sheet_width_mm'].iloc[0])

                    # Проверяем корректность размеров листа
                    if sheet_length <= 0 or sheet_width <= 0:
                        logger.warning(
                            f"Некорректные размеры листа с комбинацией: толщина={thickness}, материал={material}: {sheet_length}x{sheet_width}")
                        continue

                    # Рассчитываем количество использованных листов этой комбинации
                    used_sheets = 0
                    for bin_idx, bin_rects in enumerate(packer):
                        if bin_rects:  # Если в контейнере есть прямоугольники
                            used_sheets += 1

                    # Обновляем таблицу для этой комбинации
                    logger.info(
                        f"Обновление таблицы для комбинации: толщина={thickness}, материал={material}. Использовано листов: {used_sheets}")
                    updated_materials_df = remnants_manager.update_material_table(
                        updated_materials_df, packer, thickness, material, used_sheets,
                        sheet_length, sheet_width)

                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке остатков для ключа {material_key}: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())

            # Сохраняем обновленную таблицу материалов
            remnants_manager.save_material_table(
                updated_materials_df, os.path.join(output_dir, "updated_materials.csv"))

            # Возвращаемся в исходную директорию
            os.chdir(current_dir)

            # Показываем результаты
            generated_files = [f for f in os.listdir(output_dir) if f.startswith(
                "final_layout_") and f.endswith(".dxf")]
            logger.info(f"Создано карт раскроя: {len(generated_files)}")

            # Подсчитываем количество добавленных остатков
            remnants_count = sum(1 for _, row in updated_materials_df.iterrows()
                                 if row.get('is_remnant', False))

            self.root.after(0, lambda: messagebox.showinfo("Готово",
                                                           f"Создано карт раскроя: {len(generated_files)}\n"
                                                           f"Добавлено остатков: {remnants_count}\n"
                                                           f"Обновлённый файл материалов: {os.path.join(output_dir, 'updated_materials.csv')}\n\n"
                                                           f"Файлы сохранены в: {output_dir}"))

            # Очищаем временные файлы если нужно
            if not self.keep_files_var.get():
                self.cleanup_manager.cleanup_all(keep_output=True)

        except Exception as e:
            logger.error(f"Ошибка при выполнении раскроя: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.root.after(0, lambda: messagebox.showerror(
                "Ошибка", f"Ошибка при выполнении раскроя: {str(e)}"))

        finally:
            self.root.after(0, self.finish_cutting_task)

    def finish_cutting_task(self):
        """Завершает задачу раскроя"""
        self.run_button.config(state="normal")
        self.status_label.config(
            text="Готово" if self.check_files() else "Ошибка проверки файлов")
