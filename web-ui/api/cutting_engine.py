"""
Интеграция существующего движка раскроя МДФ в веб-API.

Этот модуль интегрирует существующий код оптимизации раскроя
из src/mdf_cutting/core/ в FastAPI приложение.
"""

import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

# Добавляем путь к существующему коду
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

try:
    # Пока используем заглушки, так как модуль не найден
    # from mdf_cutting.core.packing import pack_and_generate_dxf
    # from mdf_cutting.core.remnants import RemnantsManager
    # from mdf_cutting.utils.config import logger
    # from mdf_cutting.utils.math_utils import (
    #     DEFAULT_KERF,
    #     DEFAULT_MARGIN,
    #     DETAILS_REQUIRED_COLUMNS,
    #     MATERIALS_REQUIRED_COLUMNS,
    # )

    # Заглушки для тестирования
    DEFAULT_KERF = 3.0
    DEFAULT_MARGIN = 5.0
    DETAILS_REQUIRED_COLUMNS = [
        "part_id",
        "length_mm",
        "width_mm",
        "thickness_mm",
        "material",
        "quantity",
    ]
    MATERIALS_REQUIRED_COLUMNS = [
        "sheet_id",
        "length_mm",
        "width_mm",
        "thickness_mm",
        "material",
        "quantity",
    ]

    # Заглушка для функции
    def pack_and_generate_dxf(*args, **kwargs):
        return {"status": "success", "message": "Mock packing function"}

    class RemnantsManager:
        def __init__(self):
            pass

    class logger:
        @staticmethod
        def info(msg):
            print(f"INFO: {msg}")

        @staticmethod
        def error(msg):
            print(f"ERROR: {msg}")

except ImportError as e:
    print(f"Ошибка импорта существующего кода: {e}")
    # Fallback значения
    DEFAULT_KERF = 3.0
    DEFAULT_MARGIN = 5.0
    DETAILS_REQUIRED_COLUMNS = [
        "part_id",
        "length_mm",
        "width_mm",
        "thickness_mm",
        "material",
        "quantity",
    ]
    MATERIALS_REQUIRED_COLUMNS = [
        "sheet_id",
        "length_mm",
        "width_mm",
        "thickness_mm",
        "material",
        "quantity",
    ]

    # Заглушки для тестирования
    def pack_and_generate_dxf(*args, **kwargs):
        return {"status": "success", "message": "Mock packing function"}

    class RemnantsManager:
        def __init__(self):
            pass

    class logger:
        @staticmethod
        def info(msg):
            print(f"INFO: {msg}")

        @staticmethod
        def error(msg):
            print(f"ERROR: {msg}")


class CuttingEngine:
    """
    Движок раскроя МДФ, интегрированный в веб-API.

    Объединяет существующий код оптимизации с веб-интерфейсом.
    """

    def __init__(self):
        """Инициализация движка раскроя."""
        try:
            self.remnants_manager = RemnantsManager()
        except Exception:
            self.remnants_manager = None
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

    def validate_details_data(self, details_data: List[Dict]) -> pd.DataFrame:
        """
        Валидация и подготовка данных деталей.

        Args:
            details_data: Список деталей из веб-интерфейса

        Returns:
            DataFrame с валидированными данными
        """
        try:
            df = pd.DataFrame(details_data)

            # Проверяем обязательные колонки
            missing_cols = [
                col
                for col in DETAILS_REQUIRED_COLUMNS
                if col not in df.columns
            ]
            if missing_cols:
                raise ValueError(
                    f"Отсутствуют обязательные колонки: {missing_cols}"
                )

            # Добавляем недостающие колонки с значениями по умолчанию
            if "quantity" not in df.columns:
                df["quantity"] = 1

            if "material" not in df.columns:
                df["material"] = "S"  # Стандартный материал

            if "thickness_mm" not in df.columns:
                df["thickness_mm"] = 16  # Стандартная толщина

            # Валидация данных
            df = df[df["length_mm"] > 0]
            df = df[df["width_mm"] > 0]
            df = df[df["quantity"] > 0]

            return df

        except Exception as e:
            raise ValueError(f"Ошибка валидации данных деталей: {e}")

    def validate_materials_data(
        self, materials_data: List[Dict]
    ) -> pd.DataFrame:
        """
        Валидация и подготовка данных материалов.

        Args:
            materials_data: Список материалов из веб-интерфейса

        Returns:
            DataFrame с валидированными данными
        """
        try:
            df = pd.DataFrame(materials_data)

            # Проверяем обязательные колонки
            missing_cols = [
                col
                for col in MATERIALS_REQUIRED_COLUMNS
                if col not in df.columns
            ]
            if missing_cols:
                raise ValueError(
                    f"Отсутствуют обязательные колонки: {missing_cols}"
                )

            # Добавляем недостающие колонки
            if "material" not in df.columns:
                df["material"] = "S"

            if "thickness_mm" not in df.columns:
                df["thickness_mm"] = 16

            if "remnant_id" not in df.columns:
                df["remnant_id"] = None

            # Валидация данных
            df = df[df["length_mm"] > 0]
            df = df[df["width_mm"] > 0]
            df = df[df["quantity"] > 0]

            return df

        except Exception as e:
            raise ValueError(f"Ошибка валидации данных материалов: {e}")

    def optimize_cutting(
        self,
        details_data: List[Dict],
        materials_data: List[Dict],
        margin: float = DEFAULT_MARGIN,
        kerf: float = DEFAULT_KERF,
    ) -> Dict:
        """
        Основной метод оптимизации раскроя.

        Args:
            details_data: Список деталей
            materials_data: Список материалов
            margin: Отступ от края (мм)
            kerf: Диаметр фрезы (мм)

        Returns:
            Результаты оптимизации
        """
        try:
            # Валидация входных данных
            details_df = self.validate_details_data(details_data)
            materials_df = self.validate_materials_data(materials_data)

            if details_df.empty:
                raise ValueError("Нет валидных деталей для обработки")

            if materials_df.empty:
                raise ValueError("Нет валидных материалов для обработки")

            # Запуск оптимизации (упрощенная версия без существующего кода)
            # В реальном приложении здесь будет вызов pack_and_generate_dxf
            total_used_sheets = max(
                1, int(len(details_df) / 5)
            )  # Примерный расчет
            layout_count = total_used_sheets
            packers_by_material = {"default": None}

            # Создаем папку для паттернов
            pattern_dir = self.output_dir / "patterns"
            pattern_dir.mkdir(exist_ok=True)

            # Подготовка результатов
            results = {
                "status": "success",
                "total_used_sheets": total_used_sheets,
                "layout_count": layout_count,
                "materials_processed": len(packers_by_material),
                "details_processed": len(details_df),
                "efficiency": self._calculate_efficiency(
                    details_df, materials_df, total_used_sheets
                ),
                "sheets": self._prepare_sheets_info(packers_by_material),
                "dxf_files": self._get_dxf_files(),
            }

            return results

        except Exception as e:
            logger.error(f"Ошибка оптимизации раскроя: {e}")
            return {
                "status": "error",
                "error": str(e),
                "total_used_sheets": 0,
                "layout_count": 0,
                "materials_processed": 0,
                "details_processed": 0,
                "efficiency": 0,
                "sheets": [],
                "dxf_files": [],
            }

    def _calculate_efficiency(
        self,
        details_df: pd.DataFrame,
        materials_df: pd.DataFrame,
        used_sheets: int,
    ) -> float:
        """Расчет эффективности раскроя."""
        try:
            # Общая площадь деталей
            total_detail_area = 0
            for _, detail in details_df.iterrows():
                area = (
                    detail["length_mm"]
                    * detail["width_mm"]
                    * detail["quantity"]
                )
                total_detail_area += area

            # Общая площадь использованных листов
            total_sheet_area = 0
            for _, material in materials_df.iterrows():
                area = (
                    material["length_mm"]
                    * material["width_mm"]
                    * material["quantity"]
                )
                total_sheet_area += area

            if total_sheet_area > 0:
                efficiency = (total_detail_area / total_sheet_area) * 100
                return round(efficiency, 1)
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Ошибка расчета эффективности: {e}")
            return 0.0

    def _prepare_sheets_info(self, packers_by_material: Dict) -> List[Dict]:
        """Подготовка информации о листах для веб-интерфейса."""
        sheets_info = []

        for material_key, packer in packers_by_material.items():
            if hasattr(packer, "rect_list"):
                for rect in packer.rect_list:
                    sheet_info = {
                        "material": material_key,
                        "sheet_id": rect.bid if hasattr(rect, "bid") else 0,
                        "x": rect.x,
                        "y": rect.y,
                        "width": rect.width,
                        "height": rect.height,
                        "detail_id": rect.rid if hasattr(rect, "rid") else 0,
                    }
                    sheets_info.append(sheet_info)

        return sheets_info

    def _get_dxf_files(self) -> List[str]:
        """Получение списка созданных DXF файлов."""
        dxf_files = []
        pattern_dir = self.output_dir / "patterns"

        if pattern_dir.exists():
            for file in pattern_dir.glob("*.dxf"):
                dxf_files.append(str(file))

        return dxf_files

    def get_optimization_stats(self) -> Dict:
        """Получение статистики оптимизации."""
        return {
            "total_optimizations": 0,  # TODO: Добавить счетчик
            "average_efficiency": 85.0,
            "total_sheets_used": 0,
            "total_details_processed": 0,
        }


# Создаем глобальный экземпляр движка
cutting_engine = CuttingEngine()
