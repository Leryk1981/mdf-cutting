"""
Загрузчик данных для ML-моделей.

Этот модуль содержит:
- Загрузка и предобработка данных
- Создание DataLoader'ов
- Аугментация данных
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import h5py
import numpy as np
import torch
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from torch.utils.data import DataLoader, Dataset

logger = logging.getLogger(__name__)


class CuttingMapDataset(Dataset):
    """Датасет для карт раскроя"""

    def __init__(self, data_path: str, transform=None, target_transform=None):
        """
        Инициализация датасета.

        Args:
            data_path: Путь к файлу с данными (HDF5 или JSON)
            transform: Трансформации для входных данных
            target_transform: Трансформации для целевых данных
        """
        self.data_path = Path(data_path)
        self.transform = transform
        self.target_transform = target_transform

        # Загружаем данные
        self.data = self._load_data()

        logger.info(f"Загружен датасет: {len(self.data)} образцов")

    def _load_data(self) -> List[Dict[str, Any]]:
        """Загрузка данных из файла"""
        if self.data_path.suffix == ".h5":
            return self._load_hdf5_data()
        elif self.data_path.suffix == ".json":
            return self._load_json_data()
        else:
            raise ValueError(
                f"Неподдерживаемый формат файла: {self.data_path.suffix}"
            )

    def _load_hdf5_data(self) -> List[Dict[str, Any]]:
        """Загрузка данных из HDF5 файла"""
        data = []

        with h5py.File(self.data_path, "r") as f:
            # Получаем список ключей
            keys = list(f.keys())

            for key in keys:
                sample = {}

                # Загружаем признаки
                if "features" in f[key]:
                    features_group = f[key]["features"]
                    for feature_name in features_group.keys():
                        sample[f"features_{feature_name}"] = features_group[
                            feature_name
                        ][:]

                # Загружаем цели
                if "targets" in f[key]:
                    targets_group = f[key]["targets"]
                    for target_name in targets_group.keys():
                        sample[f"targets_{target_name}"] = targets_group[
                            target_name
                        ][:]

                # Загружаем метаданные
                if "metadata" in f[key]:
                    metadata_group = f[key]["metadata"]
                    for meta_name in metadata_group.keys():
                        sample[f"metadata_{meta_name}"] = metadata_group[
                            meta_name
                        ][:]

                data.append(sample)

        return data

    def _load_json_data(self) -> List[Dict[str, Any]]:
        """Загрузка данных из JSON файла"""
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.data[idx]

        # Разделяем на признаки и цели
        features = {}
        targets = {}

        for key, value in sample.items():
            if key.startswith("features_"):
                feature_name = key.replace("features_", "")
                features[feature_name] = torch.FloatTensor(value)
            elif key.startswith("targets_"):
                target_name = key.replace("targets_", "")
                targets[target_name] = torch.FloatTensor(value)

        # Применяем трансформации
        if self.transform:
            features = self.transform(features)

        if self.target_transform:
            targets = self.target_transform(targets)

        return {"features": features, "targets": targets, "index": idx}


class DataPreprocessor:
    """Предобработчик данных для ML"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.scalers = {}
        self.feature_dims = {}

        # Инициализация скейлеров
        self._init_scalers()

    def _init_scalers(self):
        """Инициализация скейлеров для разных типов признаков"""
        scaler_types = self.config.get("scaler_types", {})

        for feature_type, scaler_type in scaler_types.items():
            if scaler_type == "standard":
                self.scalers[feature_type] = StandardScaler()
            elif scaler_type == "minmax":
                self.scalers[feature_type] = MinMaxScaler()
            else:
                self.scalers[feature_type] = StandardScaler()  # По умолчанию

    def fit(self, dataset: CuttingMapDataset):
        """Обучение скейлеров на датасете"""
        logger.info("Обучение скейлеров...")

        # Собираем все данные для обучения скейлеров
        feature_data = {}

        for i in range(len(dataset)):
            sample = dataset[i]
            features = sample["features"]

            for feature_name, feature_tensor in features.items():
                if feature_name not in feature_data:
                    feature_data[feature_name] = []

                feature_data[feature_name].append(feature_tensor.numpy())

        # Обучаем скейлеры
        for feature_name, data_list in feature_data.items():
            if len(data_list) > 0:
                data_array = np.vstack(data_list)

                # Определяем тип скейлера
                feature_type = self._get_feature_type(feature_name)
                if feature_type in self.scalers:
                    self.scalers[feature_type].fit(data_array)

                    # Сохраняем размерность
                    self.feature_dims[feature_name] = data_array.shape[1]

        logger.info(
            f"Скейлеры обучены для {len(self.scalers)} типов признаков"
        )

    def transform(
        self, features: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """Трансформация признаков"""
        transformed_features = {}

        for feature_name, feature_tensor in features.items():
            feature_type = self._get_feature_type(feature_name)

            if feature_type in self.scalers:
                # Преобразуем в numpy, скейлим, обратно в tensor
                feature_np = feature_tensor.numpy()
                if feature_np.ndim == 1:
                    feature_np = feature_np.reshape(1, -1)

                scaled_feature = self.scalers[feature_type].transform(
                    feature_np
                )
                transformed_features[feature_name] = torch.FloatTensor(
                    scaled_feature
                )
            else:
                # Без трансформации
                transformed_features[feature_name] = feature_tensor

        return transformed_features

    def _get_feature_type(self, feature_name: str) -> str:
        """Определение типа признака"""
        if "global" in feature_name:
            return "global"
        elif "local" in feature_name:
            return "local"
        elif "spatial" in feature_name:
            return "spatial"
        elif "topological" in feature_name:
            return "topological"
        elif "optimization" in feature_name:
            return "optimization"
        else:
            return "default"


class MLDataLoader:
    """Основной загрузчик данных для ML"""

    def __init__(self, config_loader):
        self.config_loader = config_loader
        self.config = config_loader.get_config()

        # Инициализация предобработчика
        self.preprocessor = DataPreprocessor(
            self.config.get("data_preprocessing", {})
        )

        # Кэш для датасетов
        self.datasets = {}

    def load_dxf(self, dxf_path: Path) -> Dict[str, Any]:
        """Загрузка DXF файла"""
        from src.mdf_cutting.data_collectors.dxf_parser import DxfParser

        parser = DxfParser()
        return parser.parse_dxf(str(dxf_path))

    def create_dataset(
        self, data_path: str, preprocess: bool = True
    ) -> CuttingMapDataset:
        """Создание датасета"""
        dataset = CuttingMapDataset(data_path)

        if preprocess:
            # Обучение предобработчика
            self.preprocessor.fit(dataset)

            # Создание нового датасета с трансформацией
            dataset = CuttingMapDataset(
                data_path, transform=self.preprocessor.transform
            )

        return dataset

    def create_data_loaders(
        self,
        dataset: CuttingMapDataset,
        batch_size: int = 32,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        random_state: int = 42,
    ) -> Dict[str, DataLoader]:
        """Создание DataLoader'ов для обучения"""

        # Разделение на train/val/test
        total_size = len(dataset)
        train_size = int(train_ratio * total_size)
        val_size = int(val_ratio * total_size)

        # Создание индексов
        indices = list(range(total_size))
        np.random.seed(random_state)
        np.random.shuffle(indices)

        train_indices = indices[:train_size]
        val_indices = indices[train_size : train_size + val_size]
        test_indices = indices[train_size + val_size :]

        # Создание подмножеств
        train_dataset = torch.utils.data.Subset(dataset, train_indices)
        val_dataset = torch.utils.data.Subset(dataset, val_indices)
        test_dataset = torch.utils.data.Subset(dataset, test_indices)

        # Создание DataLoader'ов
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=self.config.get("num_workers", 0),
            pin_memory=self.config.get("pin_memory", False),
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=self.config.get("num_workers", 0),
            pin_memory=self.config.get("pin_memory", False),
        )

        test_loader = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=self.config.get("num_workers", 0),
            pin_memory=self.config.get("pin_memory", False),
        )

        logger.info(
            f"Созданы DataLoader'ы: train={len(train_loader)}, val={len(val_loader)}, test={len(test_loader)}"
        )

        return {"train": train_loader, "val": val_loader, "test": test_loader}

    def prepare_features_for_model(
        self, dxf_data: Dict[str, Any], order_data: Dict[str, Any]
    ) -> Dict[str, torch.Tensor]:
        """Подготовка признаков для модели"""
        from src.mdf_cutting.ai_module.features.geometry import (
            GeometryFeatureExtractor,
        )
        from src.mdf_cutting.ai_module.features.material import (
            MaterialFeatureExtractor,
        )
        from src.mdf_cutting.ai_module.features.optimization import (
            OptimizationFeatureExtractor,
        )

        # Извлечение признаков
        geometry_extractor = GeometryFeatureExtractor()
        optimization_extractor = OptimizationFeatureExtractor()
        material_extractor = MaterialFeatureExtractor()

        # Геометрические признаки
        geometry_features = geometry_extractor.extract_features(dxf_data)

        # Признаки оптимизации
        optimization_features = optimization_extractor.extract_features(
            dxf_data, order_data
        )

        # Признаки материалов
        material_features = material_extractor.extract_features(
            order_data, order_data
        )

        # Объединение признаков
        combined_features = {
            **geometry_features,
            **optimization_features,
            **material_features,
        }

        # Преобразование в тензоры
        tensor_features = {}
        for feature_name, feature_value in combined_features.items():
            if isinstance(feature_value, dict):
                # Рекурсивно обрабатываем вложенные словари
                for sub_name, sub_value in feature_value.items():
                    if isinstance(sub_value, (int, float)):
                        tensor_features[f"{feature_name}_{sub_name}"] = (
                            torch.FloatTensor([sub_value])
                        )
                    elif isinstance(sub_value, list):
                        tensor_features[f"{feature_name}_{sub_name}"] = (
                            torch.FloatTensor(sub_value)
                        )
            elif isinstance(feature_value, (int, float)):
                tensor_features[feature_name] = torch.FloatTensor(
                    [feature_value]
                )
            elif isinstance(feature_value, list):
                tensor_features[feature_name] = torch.FloatTensor(
                    feature_value
                )

        # Группировка по типам признаков
        grouped_features = {
            "global": self._extract_global_features(tensor_features),
            "local": self._extract_local_features(tensor_features),
            "spatial": self._extract_spatial_features(tensor_features),
            "topological": self._extract_topological_features(tensor_features),
            "optimization": self._extract_optimization_features(
                tensor_features
            ),
        }

        return grouped_features

    def _extract_global_features(
        self, features: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """Извлечение глобальных признаков"""
        global_keys = [
            k
            for k in features.keys()
            if "global" in k or "utilization" in k or "waste" in k
        ]
        global_features = [features[k] for k in global_keys if k in features]

        if global_features:
            return torch.cat(global_features, dim=0)
        else:
            return torch.zeros(64)  # Дефолтная размерность

    def _extract_local_features(
        self, features: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """Извлечение локальных признаков"""
        local_keys = [
            k
            for k in features.keys()
            if "local" in k or "piece" in k or "compactness" in k
        ]
        local_features = [features[k] for k in local_keys if k in features]

        if local_features:
            return torch.cat(local_features, dim=0)
        else:
            return torch.zeros(128)  # Дефолтная размерность

    def _extract_spatial_features(
        self, features: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """Извлечение пространственных признаков"""
        spatial_keys = [
            k
            for k in features.keys()
            if "spatial" in k or "quadrant" in k or "distribution" in k
        ]
        spatial_features = [features[k] for k in spatial_keys if k in features]

        if spatial_features:
            return torch.cat(spatial_features, dim=0)
        else:
            return torch.zeros(64)  # Дефолтная размерность

    def _extract_topological_features(
        self, features: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """Извлечение топологических признаков"""
        topo_keys = [
            k
            for k in features.keys()
            if "topological" in k or "graph" in k or "connectivity" in k
        ]
        topo_features = [features[k] for k in topo_keys if k in features]

        if topo_features:
            return torch.cat(topo_features, dim=0)
        else:
            return torch.zeros(32)  # Дефолтная размерность

    def _extract_optimization_features(
        self, features: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """Извлечение признаков оптимизации"""
        optim_keys = [
            k
            for k in features.keys()
            if "optimization" in k or "cutting" in k or "efficiency" in k
        ]
        optim_features = [features[k] for k in optim_keys if k in features]

        if optim_features:
            return torch.cat(optim_features, dim=0)
        else:
            return torch.zeros(32)  # Дефолтная размерность

    def save_preprocessor(self, path: str):
        """Сохранение предобработчика"""
        import pickle

        with open(path, "wb") as f:
            pickle.dump(self.preprocessor, f)

        logger.info(f"Предобработчик сохранен: {path}")

    def load_preprocessor(self, path: str):
        """Загрузка предобработчика"""
        import pickle

        with open(path, "rb") as f:
            self.preprocessor = pickle.load(f)

        logger.info(f"Предобработчик загружен: {path}")

    def get_feature_dims(self) -> Dict[str, int]:
        """Получение размерностей признаков"""
        return self.preprocessor.feature_dims.copy()
