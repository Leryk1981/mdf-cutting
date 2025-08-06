import numpy as np
import pandas as pd
from rectpack import newPacker

from .config import logger


class RemnantsManager:
    """Менеджер остатков материалов"""

    def __init__(self, margin=6, kerf=4):
        self.margin = margin
        self.kerf = kerf
        # Минимальные размеры для пригодного остатка (мм)
        self.min_remnant_width = 60
        self.min_remnant_length = 1000
        # Удаляем словарь для учета созданных идентификаторов

    def format_remnant_id(self, remnant_id):
        """
        Оставляет ID остатка без изменений.

        В предыдущей версии этот метод пытался преобразовать ID в целое число,
        что могло приводить к изменению идентификатора. Теперь метод
        просто возвращает исходный ID, сохраняя его точное значение.

        Args:
            remnant_id: ID остатка

        Returns:
            Исходный ID остатка без изменений
        """
        # Просто возвращаем исходный ID без каких-либо преобразований
        return remnant_id

    def calculate_remnants(self, packer, sheet_length, sheet_width, margin):
        """
        Рассчитывает остатки материала после упаковки деталей, игнорируя остатки меньше 60x1000 мм.

        Args:
            packer: упаковщик с размещенными деталями
            sheet_length: длина листа (мм)
            sheet_width: ширина листа (мм)
            margin: отступ от края (мм)

        Returns:
            list: список остатков в формате [(length, width), ...]
        """
        remnants = []

        if packer is None:
            logger.warning("Упаковщик не определён, остатки не рассчитаны")
            return remnants

        if not isinstance(sheet_length, (int, float)) or not isinstance(
            sheet_width, (int, float)
        ):
            logger.warning(
                f"Некорректные размеры листа: {sheet_length}x{sheet_width}"
            )
            return remnants

        if sheet_length <= 2 * margin or sheet_width <= 2 * margin:
            logger.warning(
                f"Размеры листа слишком малы с учётом отступов: {sheet_length}x{sheet_width}"
            )
            return remnants

        bin_width = sheet_length - 2 * margin
        bin_height = sheet_width - 2 * margin

        for bin_num, bin_rects in enumerate(packer):
            if not bin_rects:
                continue

            # Инициализируем список свободных прямоугольников
            # x, y, width, height
            free_spaces = [(0, 0, bin_width, bin_height)]
            for rect in bin_rects:
                new_spaces = []
                for fx, fy, fw, fh in free_spaces:
                    # Проверяем пересечение с текущей деталью
                    if (
                        rect.x >= fx + fw
                        or rect.y >= fy + fh
                        or rect.x + rect.width <= fx
                        or rect.y + rect.height <= fy
                    ):
                        new_spaces.append((fx, fy, fw, fh))  # Нет пересечения
                    else:
                        # Разделяем свободное пространство
                        if rect.y > fy:  # Сверху
                            new_spaces.append((fx, fy, fw, rect.y - fy))
                        if rect.x + rect.width < fx + fw:  # Справа
                            new_spaces.append(
                                (
                                    rect.x + rect.width,
                                    fy,
                                    fx + fw - (rect.x + rect.width),
                                    fh,
                                )
                            )
                        if rect.y + rect.height < fy + fh:  # Снизу
                            new_spaces.append(
                                (
                                    fx,
                                    rect.y + rect.height,
                                    fw,
                                    fy + fh - (rect.y + rect.height),
                                )
                            )
                        if rect.x > fx:  # Слева
                            new_spaces.append((fx, fy, rect.x - fx, fh))
                free_spaces = new_spaces

            # Фильтруем и добавляем остатки с явным ограничением
            for fx, fy, fw, fh in free_spaces:
                actual_length = fw
                actual_width = fh
                # Строгая фильтрация: минимум 60x1000 мм
                if (
                    actual_length < self.min_remnant_length
                    or actual_width < self.min_remnant_length
                ):
                    logger.debug(
                        f"Лист {bin_num}: игнорируется остаток {actual_length}x{actual_width} (меньше {self.min_remnant_length})"
                    )
                    continue
                if (
                    actual_length < self.min_remnant_width
                    or actual_width < self.min_remnant_width
                ):
                    logger.debug(
                        f"Лист {bin_num}: игнорируется остаток {actual_length}x{actual_width} (меньше {self.min_remnant_width})"
                    )
                    continue
                # Если длина меньше ширины, меняем местами для консистентности
                if actual_length < actual_width:
                    actual_length, actual_width = actual_width, actual_length
                remnants.append((actual_length, actual_width))
                logger.info(
                    f"Лист {bin_num}: добавлен остаток {actual_length}x{actual_width} мм"
                )

        return remnants

    def update_material_table(
        self,
        materials_df,
        packer,
        thickness,
        material,
        used_sheets,
        sheet_length=None,
        sheet_width=None,
    ):
        """
        Обновляет таблицу материалов с учётом остатков и использованных листов.

        Args:
            materials_df: DataFrame с материалами
            packer: упаковщик с размещенными деталями
            thickness: толщина материала
            material: тип материала
            used_sheets: количество использованных листов
            sheet_length: длина листа (если None, берётся из materials_df)
            sheet_width: ширина листа (если None, берётся из materials_df)

        Returns:
            DataFrame: обновленная таблица материалов
        """
        logger.info(
            f"Обновление таблицы для толщина={thickness}, материал={material}"
        )
        updated_materials = materials_df.copy()

        # Добавляем колонку is_remnant, если её нет
        if "is_remnant" not in updated_materials.columns:
            updated_materials["is_remnant"] = False
            logger.info(
                "Добавлена колонка 'is_remnant' со значением False для исходных данных"
            )

        # Добавляем колонку remnant_id, если её нет
        if "remnant_id" not in updated_materials.columns:
            # Только для остатков будут идентификаторы, для целых листов - None
            updated_materials["remnant_id"] = None
            logger.info(
                "Добавлена колонка 'remnant_id' со значением None для исходных данных"
            )

        # НЕ преобразуем remnant_id для сохранения исходных значений
        # Просто выведем для диагностики несколько значений
        mask = ~updated_materials["remnant_id"].isna()
        if mask.any():
            logger.info(f"Примеры текущих значений remnant_id:")
            for idx, val in (
                updated_materials.loc[mask, "remnant_id"].head(5).items()
            ):
                logger.info(
                    f"  Индекс {idx}: {val} (тип: {type(val).__name__})"
                )

        # Определяем стандартные размеры целого листа
        if sheet_length is None or sheet_width is None:
            material_mask = (
                (updated_materials["thickness_mm"] == thickness)
                & (updated_materials["material"] == material)
                & (updated_materials["is_remnant"] == False)
            )
            thickness_rows = updated_materials[material_mask]
            if thickness_rows.empty:
                logger.warning(
                    f"Не найдены целые листы для толщина={thickness}, материал={material}"
                )
                return updated_materials
            try:
                sheet_length = float(thickness_rows["sheet_length_mm"].iloc[0])
                sheet_width = float(thickness_rows["sheet_width_mm"].iloc[0])
                if sheet_length <= 0 or sheet_width <= 0:
                    logger.warning(
                        f"Некорректные размеры листа: {sheet_length}x{sheet_width}"
                    )
                    return updated_materials
            except (ValueError, TypeError):
                logger.error("Ошибка получения размеров листа из таблицы")
                return updated_materials

        # Уменьшаем количество целых листов
        if used_sheets > 0:
            material_mask = (
                (updated_materials["thickness_mm"] == thickness)
                & (updated_materials["material"] == material)
                & (updated_materials["is_remnant"] == False)
            )
            material_rows = updated_materials[material_mask]
            if material_rows.empty:
                logger.warning(
                    f"Не найдены целые листы для уменьшения количества"
                )
            else:
                remaining_sheets = used_sheets
                for idx in material_rows.index:
                    original_qty = updated_materials.loc[idx, "total_quantity"]
                    sheets_to_deduct = min(remaining_sheets, original_qty)
                    updated_materials.loc[idx, "total_quantity"] = max(
                        0, original_qty - sheets_to_deduct
                    )
                    remaining_sheets -= sheets_to_deduct
                    logger.info(
                        f"Лист {idx}: количество уменьшено с {original_qty} до {updated_materials.loc[idx, 'total_quantity']}"
                    )
                    if remaining_sheets <= 0:
                        break
                if remaining_sheets > 0:
                    logger.warning(
                        f"Не удалось распределить все {used_sheets} листов, осталось {remaining_sheets}"
                    )

        # Рассчитываем остатки
        remnants = self.calculate_remnants(
            packer, sheet_length, sheet_width, self.margin
        )
        logger.info(f"Найдено {len(remnants)} остатков")

        # НЕ удаляем старые остатки автоматически - они должны сохраняться
        # Создаем таблицу новых остатков
        if remnants:
            # Собираем новые остатки в список словарей
            remnant_rows = []
            for remnant_length, remnant_width in remnants:
                # Новые остатки будут с NULL в поле remnant_id
                # Пользователь сам определит их ID по факту использования
                remnant_row = {
                    "thickness_mm": thickness,
                    "material": material,
                    "sheet_length_mm": float(remnant_length),
                    "sheet_width_mm": float(remnant_width),
                    "total_quantity": 1,
                    "is_remnant": True,
                    "remnant_id": None,  # NULL для новых остатков
                }
                remnant_rows.append(remnant_row)
                logger.info(
                    f"Добавлен новый остаток: {remnant_length}x{remnant_width}, ID: None (требуется заполнение)"
                )

            # Создаем DataFrame из новых остатков
            if remnant_rows:
                # Используем явный список колонок, чтобы гарантировать наличие remnant_id
                columns = [
                    "thickness_mm",
                    "material",
                    "sheet_length_mm",
                    "sheet_width_mm",
                    "total_quantity",
                    "is_remnant",
                    "remnant_id",
                ]

                remnants_df = pd.DataFrame(remnant_rows, columns=columns)

                # Обеспечиваем корректный тип данных
                numeric_cols = [
                    "sheet_length_mm",
                    "sheet_width_mm",
                    "total_quantity",
                ]
                for col in numeric_cols:
                    remnants_df[col] = pd.to_numeric(
                        remnants_df[col], errors="coerce"
                    ).fillna(0)

                # Добавляем только новые остатки в обновленную таблицу
                # Существующие остатки уже присутствуют в updated_materials
                updated_materials = pd.concat(
                    [updated_materials, remnants_df], ignore_index=True
                )
                logger.info(
                    f"Добавлено {len(remnants_df)} новых остатков в таблицу"
                )

                # Логируем для отладки
                logger.info(
                    f"Колонки в обновленной таблице: {', '.join(updated_materials.columns)}"
                )
                if "remnant_id" in updated_materials.columns:
                    logger.info(
                        "Колонка remnant_id присутствует в итоговой таблице"
                    )
                else:
                    logger.error(
                        "Колонка remnant_id ОТСУТСТВУЕТ в итоговой таблице!"
                    )
            else:
                logger.info("Новых остатков не добавлено")
        else:
            logger.info("Новых остатков не обнаружено")

        return updated_materials

    def save_material_table(self, materials_df, output_path):
        """
        Сохраняет обновленную таблицу материалов.

        Args:
            materials_df: DataFrame с материалами
            output_path: путь для сохранения
        """
        try:
            output_df = materials_df.copy()

            # Гарантируем наличие обязательных колонок перед сохранением
            if "remnant_id" not in output_df.columns:
                output_df["remnant_id"] = None
                logger.warning(
                    "Перед сохранением добавлена отсутствующая колонка 'remnant_id'"
                )

            if "is_remnant" not in output_df.columns:
                output_df["is_remnant"] = False
                logger.warning(
                    "Перед сохранением добавлена отсутствующая колонка 'is_remnant'"
                )

            # ВАЖНО: Сохраняем remnant_id в исходном виде без преобразований
            # Не применяем функцию format_remnant_id к значениям remnant_id
            logger.info(
                "Сохраняем remnant_id в исходном виде без преобразований"
            )

            # Для диагностики выведем несколько значений remnant_id
            mask = ~output_df["remnant_id"].isna()
            if mask.any():
                logger.info(f"Примеры значений remnant_id перед сохранением:")
                for idx, val in (
                    output_df.loc[mask, "remnant_id"].head(5).items()
                ):
                    logger.info(
                        f"  Индекс {idx}: {val} (тип: {type(val).__name__})"
                    )

            # Важно: явно преобразуем типы данных перед сохранением
            # Это предотвратит автоматическое приведение целых чисел к float при сохранении
            numeric_cols = [
                "sheet_length_mm",
                "sheet_width_mm",
                "total_quantity",
                "thickness_mm",
            ]
            for col in numeric_cols:
                if col in output_df.columns:
                    output_df[col] = pd.to_numeric(
                        output_df[col], errors="coerce"
                    )

            # Для совместимости с pandas сохраняем remnant_id как объект, а не числовой тип
            # Это предотвратит добавление .0 к целым числам
            output_df["remnant_id"] = output_df["remnant_id"].astype("object")

            # Выводим окончательный список колонок для отладки
            logger.info(
                f"Колонки в сохраняемой таблице: {', '.join(output_df.columns)}"
            )

            # Сохраняем таблицу с явным указанием всех важных колонок
            # Используем float_format для контроля форматирования чисел
            output_df.to_csv(
                output_path,
                sep=";",
                index=False,
                encoding="utf-8",
                float_format="%.0f",
            )  # Убираем десятичные нули
            logger.info(f"Таблица сохранена в {output_path}")

            # Выводим статистику сохраненной таблицы
            remnants_count = (output_df["is_remnant"] == True).sum()
            logger.info(f"В сохраненной таблице {remnants_count} остатков")
            remnants_with_id = (
                (output_df["is_remnant"] == True)
                & (~output_df["remnant_id"].isna())
            ).sum()
            logger.info(f"Из них {remnants_with_id} имеют идентификаторы")

        except Exception as e:
            logger.error(f"Ошибка сохранения таблицы: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
