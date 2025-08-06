"""
Схемы данных для валидации в модуле сбора данных.

Этот модуль содержит:
- Pydantic модели для валидации данных
- Схемы для DXF файлов
- Схемы для табличных данных
- Конфигурацию сбора данных
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator, Field


class DxfEntity(BaseModel):
    """Схема для сущности DXF файла."""

    type: str
    handle: str
    layer: str
    color: int = 7  # По умолчанию белый
    linetype: str = "CONTINUOUS"
    points: Optional[List[List[float]]] = None
    bounding_box: Optional[List[float]] = None
    area: float = 0.0


class DxfMetadata(BaseModel):
    """Схема для метаданных DXF файла."""

    units: int = 4  # 4 = миллиметры
    creation_date: Optional[str] = None
    last_modified: Optional[str] = None
    file_path: str
    file_size: int
    version: str = "R2010"


class DxfStatistics(BaseModel):
    """Схема для статистики DXF файла."""

    total_area: float
    pieces_count: int
    waste_percentage: float
    average_piece_area: float
    total_cuts: int
    material_usage: float


class DxfData(BaseModel):
    """Схема для полных данных DXF файла."""

    metadata: DxfMetadata
    entities: List[DxfEntity]
    statistics: DxfStatistics
    dimensions: Dict[str, float]
    material_info: Dict[str, Any]


class OrderData(BaseModel):
    """Схема для данных заказа."""

    material_code: str
    length: float = Field(gt=0)
    width: float = Field(gt=0)
    quantity: int = Field(gt=0)
    thickness: float = Field(gt=0)
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    @validator("length", "width", "thickness")
    def validate_dimensions(cls, v):
        """Валидация размеров."""
        if v <= 0:
            raise ValueError("Размеры должны быть положительными")
        return v


class CorrectionData(BaseModel):
    """Схема для данных корректировки."""

    dxf_file: str
    timestamp: datetime
    correction_type: str = Field(
        pattern="^(position|rotation|dimension_change|custom)$"
    )
    affected_pieces: List[str] = Field(default_factory=list)
    reason: str = ""
    operator: str = ""
    improvement_score: float = Field(ge=0, le=1)


class MaterialProperties(BaseModel):
    """Схема для свойств материала."""

    thickness: float = Field(gt=0)
    density: float = Field(gt=0)
    quality_factor: float = Field(ge=0, le=1)
    material_type: str
    cost_per_sqm: float = Field(ge=0)


class DataCollectionConfig(BaseModel):
    """Конфигурация сбора данных."""

    raw_data_dir: Path
    processed_data_dir: Path
    ml_training_dir: Path
    logs_dir: Path
    max_file_size_mb: int = 100
    supported_dxf_versions: List[str] = Field(
        default_factory=lambda: ["R2010", "R2007", "R2004"]
    )
    batch_size: int = 100
    compression_enabled: bool = True

    @validator(
        "raw_data_dir", "processed_data_dir", "ml_training_dir", "logs_dir"
    )
    def validate_directories(cls, v):
        """Валидация директорий."""
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v

    @validator("max_file_size_mb")
    def validate_file_size(cls, v):
        """Валидация максимального размера файла."""
        if v <= 0:
            raise ValueError(
                "Максимальный размер файла должен быть положительным"
            )
        return v


class MLTrainingSample(BaseModel):
    """Схема для обучающего образца."""

    sample_id: str
    input: Dict[str, Any]
    target: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("input")
    def validate_input(cls, v):
        """Валидация входных данных."""
        required_keys = ["order_info", "dxf_geometry", "material_properties"]
        for key in required_keys:
            if key not in v:
                raise ValueError(f"Отсутствует обязательное поле: {key}")
        return v

    @validator("target")
    def validate_target(cls, v):
        """Валидация целевых данных."""
        required_keys = [
            "corrections",
            "waste_reduction",
            "final_layout_score",
        ]
        for key in required_keys:
            if key not in v:
                raise ValueError(f"Отсутствует обязательное поле: {key}")
        return v
