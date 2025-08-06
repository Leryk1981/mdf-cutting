"""
Загрузчик конфигурации для MDF Cutting.

Этот модуль содержит:
- Загрузку YAML конфигураций
- Парсинг форматов таблиц
- Управление правилами оптимизации
- Поддержку переменных окружения
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from . import TableFormat, OptimizationRule, ConfigManager


class ConfigLoader:
    """
    Загрузчик конфигурации с поддержкой стандартных форматов таблиц.
    
    Обеспечивает загрузку конфигураций из YAML файлов с сохранением
    существующих форматов таблиц заказчика.
    """

    def __init__(self, config_dir: Path = None):
        """
        Инициализация загрузчика конфигурации.
        
        Args:
            config_dir: Директория с конфигурационными файлами
        """
        self.config_dir = config_dir or Path(__file__).parent
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._table_formats: Dict[str, TableFormat] = {}
        self._optimization_rules: Dict[str, List[OptimizationRule]] = {}
        self._loaded = False

    def load_all(self) -> None:
        """Загрузить все конфигурации при старте системы."""
        try:
            self._load_yaml_config("base_config")
            self._load_yaml_config("production_tables")
            self._load_yaml_config("optimization_rules")
            self._parse_table_formats()
            self._parse_optimization_rules()
            self._loaded = True
        except Exception as e:
            raise RuntimeError(f"Failed to load configurations: {e}")

    def get_table_format(self, format_id: str) -> Optional[TableFormat]:
        """
        Вернуть формат таблиц с сохранением стандарта заказчика.
        
        Args:
            format_id: ID формата таблицы
            
        Returns:
            TableFormat или None если формат не найден
        """
        if not self._loaded:
            self.load_all()
        return self._table_formats.get(format_id)

    def get_optimization_rules(self, material_type: str) -> List[OptimizationRule]:
        """
        Вернуть правила оптимизации для типа материала.
        
        Args:
            material_type: Тип материала
            
        Returns:
            Список правил оптимизации
        """
        if not self._loaded:
            self.load_all()
        return self._optimization_rules.get(material_type, [])

    def get_config(self, config_name: str) -> Dict[str, Any]:
        """
        Получить конфигурацию по имени.
        
        Args:
            config_name: Имя конфигурации
            
        Returns:
            Словарь с конфигурацией
        """
        if not self._loaded:
            self.load_all()
        return self._configs.get(config_name, {})

    def reload(self) -> None:
        """Перезагрузить все конфигурации."""
        self._configs.clear()
        self._table_formats.clear()
        self._optimization_rules.clear()
        self._loaded = False
        self.load_all()

    def _load_yaml_config(self, name: str) -> None:
        """
        Загрузить YAML конфигурацию.
        
        Args:
            name: Имя конфигурационного файла
        """
        config_path = self.config_dir / f"{name}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._configs[name] = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {name}.yaml: {e}")

    def _parse_table_formats(self) -> None:
        """Распарсить форматы таблиц без изменения структуры."""
        tables_data = self._configs.get("production_tables", {})
        for table_id, table_data in tables_data.items():
            try:
                self._table_formats[table_id] = TableFormat(**table_data)
            except Exception as e:
                raise ValueError(f"Invalid table format {table_id}: {e}")

    def _parse_optimization_rules(self) -> None:
        """Распарсить правила оптимизации."""
        rules_data = self._configs.get("optimization_rules", {})
        for material, rules in rules_data.items():
            try:
                self._optimization_rules[material] = [
                    OptimizationRule(**rule_data) for rule_data in rules
                ]
            except Exception as e:
                raise ValueError(f"Invalid optimization rules for {material}: {e}")

    def list_table_formats(self) -> List[str]:
        """Получить список доступных форматов таблиц."""
        if not self._loaded:
            self.load_all()
        return list(self._table_formats.keys())

    def list_material_types(self) -> List[str]:
        """Получить список типов материалов с правилами оптимизации."""
        if not self._loaded:
            self.load_all()
        return list(self._optimization_rules.keys()) 