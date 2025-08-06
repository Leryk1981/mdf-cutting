"""
Система сериализации данных для машинного обучения.

Этот модуль содержит:
- Сериализацию данных в форматы для ML
- Поддержку HDF5 для эффективного хранения
- Преобразование геометрических данных в numpy arrays
- Кодировщики для специальных типов данных
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import h5py


class NumpyEncoder(json.JSONEncoder):
    """Кодировщик для сериализации numpy типов в JSON."""

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class MLDataSerializer:
    """
    Сериализатор данных для машинного обучения.

    Обеспечивает эффективную сериализацию данных в форматы,
    пригодные для обучения ML-моделей.
    """

    def __init__(self, output_dir: Path):
        """
        Инициализация сериализатора.

        Args:
            output_dir: Директория для сохранения данных
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def serialize_training_batch(
        self, data: List[Dict[str, Any]], batch_id: str
    ) -> Path:
        """
        Сериализовать партию данных для обучения.

        Args:
            data: Список образцов данных
            batch_id: Уникальный ID партии

        Returns:
            Path: Путь к сохраненному файлу
        """
        timestamp = datetime.now().isoformat()

        # Создаем структуру данных для обучения
        training_data = {
            "metadata": {
                "batch_id": batch_id,
                "created_at": timestamp,
                "total_samples": len(data),
            },
            "samples": [],
        }

        for sample in data:
            # Преобразуем геометрические данные в numpy arrays
            processed_sample = {
                "input": {
                    "order_info": self._process_order_info(
                        sample.get("order_data", {})
                    ),
                    "dxf_geometry": self._process_dxf_data(
                        sample.get("dxf_data", {})
                    ),
                    "material_properties": self._process_material_data(
                        sample.get("material_data", {})
                    ),
                },
                "target": {
                    "corrections": sample.get("corrections", []),
                    "waste_reduction": sample.get("waste_reduction", 0.0),
                    "final_layout_score": sample.get("layout_score", 0.0),
                },
            }
            training_data["samples"].append(processed_sample)

        # Сохраняем в формате HDF5 для эффективности
        output_path = self.output_dir / f"training_batch_{batch_id}.h5"
        with h5py.File(output_path, "w") as f:
            # Метаданные
            meta_group = f.create_group("metadata")
            meta_group.attrs["batch_id"] = training_data["metadata"][
                "batch_id"
            ]
            meta_group.attrs["created_at"] = training_data["metadata"][
                "created_at"
            ]
            meta_group.attrs["total_samples"] = training_data["metadata"][
                "total_samples"
            ]

            # Обучающие данные
            samples_group = f.create_group("samples")
            for i, sample in enumerate(training_data["samples"]):
                sample_group = samples_group.create_group(f"sample_{i}")

                # Input данные
                input_group = sample_group.create_group("input")
                input_group.create_dataset(
                    "order_info", data=np.array(sample["input"]["order_info"])
                )
                input_group.create_dataset(
                    "dxf_geometry",
                    data=np.array(sample["input"]["dxf_geometry"]),
                )
                input_group.create_dataset(
                    "material_properties",
                    data=np.array(sample["input"]["material_properties"]),
                )

                # Target данные
                target_group = sample_group.create_group("target")
                target_group.create_dataset(
                    "corrections",
                    data=np.array(sample["target"]["corrections"]),
                )
                target_group.create_dataset(
                    "waste_reduction", data=sample["target"]["waste_reduction"]
                )
                target_group.create_dataset(
                    "final_layout_score",
                    data=sample["target"]["final_layout_score"],
                )

        return output_path

    def serialize_real_time_data(self, data: Dict[str, Any]) -> Path:
        """
        Сериализовать данные в реальном времени для предсказания.

        Args:
            data: Данные для предсказания

        Returns:
            Path: Путь к сохраненному файлу
        """
        timestamp = datetime.now().isoformat().replace(":", "-")
        output_path = self.output_dir / f"realtime_{timestamp}.json"

        # Прямая сериализация в JSON для быстроты
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, cls=NumpyEncoder, indent=2)

        return output_path

    def serialize_corrections_dataset(
        self, corrections: List[Dict[str, Any]], dataset_id: str
    ) -> Path:
        """
        Сериализовать набор данных корректировок.

        Args:
            corrections: Список корректировок
            dataset_id: ID набора данных

        Returns:
            Path: Путь к сохраненному файлу
        """
        output_path = (
            self.output_dir / f"corrections_dataset_{dataset_id}.json"
        )

        dataset_data = {
            "dataset_id": dataset_id,
            "created_at": datetime.now().isoformat(),
            "total_corrections": len(corrections),
            "corrections": corrections,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dataset_data, f, cls=NumpyEncoder, indent=2)

        return output_path

    def load_training_batch(self, batch_path: Path) -> Dict[str, Any]:
        """
        Загрузить партию данных для обучения.

        Args:
            batch_path: Путь к файлу партии

        Returns:
            Dict: Загруженные данные
        """
        if not batch_path.exists():
            raise FileNotFoundError(f"Batch file not found: {batch_path}")

        with h5py.File(batch_path, "r") as f:
            # Загружаем метаданные
            metadata = {
                "batch_id": f["metadata"].attrs["batch_id"],
                "created_at": f["metadata"].attrs["created_at"],
                "total_samples": f["metadata"].attrs["total_samples"],
            }

            # Загружаем образцы
            samples = []
            samples_group = f["samples"]

            for sample_name in samples_group.keys():
                sample_group = samples_group[sample_name]

                sample = {
                    "input": {
                        "order_info": sample_group["input"]["order_info"][:],
                        "dxf_geometry": sample_group["input"]["dxf_geometry"][
                            :
                        ],
                        "material_properties": sample_group["input"][
                            "material_properties"
                        ][:],
                    },
                    "target": {
                        "corrections": sample_group["target"]["corrections"][
                            :
                        ],
                        "waste_reduction": sample_group["target"][
                            "waste_reduction"
                        ][()],
                        "final_layout_score": sample_group["target"][
                            "final_layout_score"
                        ][()],
                    },
                }
                samples.append(sample)

        return {"metadata": metadata, "samples": samples}

    def _process_order_info(self, order_data: Dict) -> np.ndarray:
        """
        Преобразовать данные заказа в numpy array.

        Args:
            order_data: Данные заказа

        Returns:
            np.ndarray: Массив признаков заказа
        """
        features = [
            self._hash_string(order_data.get("material_code", "")),
            order_data.get("length", 0.0),
            order_data.get("width", 0.0),
            order_data.get("quantity", 1),
            order_data.get("thickness", 16.0),
        ]
        return np.array(features, dtype=np.float32)

    def _process_dxf_data(self, dxf_data: Dict) -> np.ndarray:
        """
        Преобразовать геометрические данные DXF в numpy array.

        Args:
            dxf_data: Данные DXF

        Returns:
            np.ndarray: Массив геометрических признаков
        """
        features = [
            dxf_data.get("total_area", 0.0),
            dxf_data.get("pieces_count", 0),
            dxf_data.get("waste_percentage", 0.0),
            dxf_data.get("average_piece_area", 0.0),
            dxf_data.get("total_cuts", 0),
            dxf_data.get("material_usage", 0.0),
        ]
        return np.array(features, dtype=np.float32)

    def _process_material_data(self, material_data: Dict) -> np.ndarray:
        """
        Преобразовать данные о материале в numpy array.

        Args:
            material_data: Данные о материале

        Returns:
            np.ndarray: Массив признаков материала
        """
        features = [
            material_data.get("thickness", 16.0),
            material_data.get("density", 750.0),  # Typical MDF density
            material_data.get("quality_factor", 1.0),
            self._hash_string(material_data.get("material_type", "MDF")),
            material_data.get("cost_per_sqm", 0.0),
        ]
        return np.array(features, dtype=np.float32)

    def _hash_string(self, s: str) -> float:
        """
        Преобразовать строку в числовой хеш.

        Args:
            s: Строка для хеширования

        Returns:
            float: Числовой хеш
        """
        if not s:
            return 0.0

        # Простой хеш для строки
        hash_value = 0
        for char in s:
            hash_value = (hash_value * 31 + ord(char)) % 1000000

        return float(hash_value)

    def get_batch_statistics(self, batch_path: Path) -> Dict[str, Any]:
        """
        Получить статистику партии данных.

        Args:
            batch_path: Путь к файлу партии

        Returns:
            Dict: Статистика партии
        """
        try:
            with h5py.File(batch_path, "r") as f:
                total_samples = f["metadata"].attrs["total_samples"]

                # Собираем статистику по образцам
                waste_reductions = []
                layout_scores = []

                for sample_name in f["samples"].keys():
                    sample_group = f["samples"][sample_name]
                    waste_reductions.append(
                        sample_group["target"]["waste_reduction"][()]
                    )
                    layout_scores.append(
                        sample_group["target"]["final_layout_score"][()]
                    )

                return {
                    "total_samples": total_samples,
                    "average_waste_reduction": np.mean(waste_reductions),
                    "average_layout_score": np.mean(layout_scores),
                    "min_waste_reduction": np.min(waste_reductions),
                    "max_waste_reduction": np.max(waste_reductions),
                    "min_layout_score": np.min(layout_scores),
                    "max_layout_score": np.max(layout_scores),
                }
        except Exception as e:
            return {"error": str(e)}
