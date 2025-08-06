# Конфигурационная система MDF Cutting

## Обзор

Конфигурационная система MDF Cutting обеспечивает гибкую настройку параметров оптимизации раскроя с сохранением стандартных форматов таблиц заказчика.

## Структура конфигурации

```
src/mdf_cutting/config/
├── __init__.py              # Типы и интерфейсы
├── loader.py                # Загрузчик конфигурации
├── base_config.yaml         # Основные параметры системы
├── production_tables.yaml   # Стандартные форматы таблиц
└── optimization_rules.yaml  # Правила оптимизации
```

## Основные компоненты

### 1. ConfigLoader

Основной класс для загрузки и управления конфигурациями:

```python
from src.mdf_cutting.config.loader import ConfigLoader

# Инициализация
loader = ConfigLoader()
loader.load_all()

# Получение формата таблицы
table_format = loader.get_table_format("standard_table")

# Получение правил оптимизации
rules = loader.get_optimization_rules("mdf_16mm")
```

### 2. TableFormat

Структура для описания форматов таблиц:

```python
from src.mdf_cutting.config import TableFormat, TableColumn

# Пример создания формата
format = TableFormat(
    id="custom_format",
    name="Пользовательский формат",
    delimiter=";",
    columns=[
        TableColumn(name="length", type="float", required=True),
        TableColumn(name="width", type="float", required=True),
        TableColumn(name="quantity", type="int", required=False)
    ]
)
```

### 3. OptimizationRule

Правила оптимизации для конкретных типов материалов:

```python
from src.mdf_cutting.config import OptimizationRule

rule = OptimizationRule(
    name="basic_cutting",
    min_spacing=5.0,
    max_cuts=50,
    material_types=["MDF", "LDPE"],
    priority=1
)
```

## Конфигурационные файлы

### base_config.yaml

Основные параметры системы:

```yaml
optimization:
  max_iterations: 10000
  tolerance: 0.001
  population_size: 50

material:
  default_thickness: 16
  kerf_width: 3.2
  min_strip_width: 10

logging:
  level: INFO
  file_format: "{date}_{process}.log"
```

### production_tables.yaml

Стандартные форматы таблиц заказчика:

```yaml
standard_table:
  id: "standard_table"
  name: "Стандартная таблица раскроя"
  delimiter: ";"
  columns:
    - name: "material_code"
      type: "str"
      required: true
    - name: "length"
      type: "float"
      required: true
    - name: "width"
      type: "float"
      required: true
```

### optimization_rules.yaml

Правила оптимизации для производства:

```yaml
mdf_16mm:
  - name: "basic_cutting"
    min_spacing: 5.0
    max_cuts: 50
    material_types: ["MDF", "LDPE"]
    priority: 1
```

## Переменные окружения

Система поддерживает настройку через переменные окружения:

```bash
# .env файл
DEBUG_MODE=False
TABLE_FORMAT_ID=standard_table
CONFIG_PATH=./src/mdf_cutting/config/
LOG_LEVEL=INFO
MAX_ITERATIONS=10000
```

## Добавление новых форматов таблиц

1. Добавьте новый формат в `production_tables.yaml`:

```yaml
new_format:
  id: "new_format"
  name: "Новый формат"
  delimiter: ","
  columns:
    - name: "custom_field"
      type: "str"
      required: true
```

2. Используйте в коде:

```python
table_format = loader.get_table_format("new_format")
```

## Добавление правил оптимизации

1. Добавьте правило в `optimization_rules.yaml`:

```yaml
new_material:
  - name: "custom_rule"
    min_spacing: 3.0
    max_cuts: 100
    material_types: ["NEW_MATERIAL"]
    priority: 1
```

2. Используйте в коде:

```python
rules = loader.get_optimization_rules("new_material")
```

## Тестирование

Запуск тестов конфигурационной системы:

```bash
# Все тесты
pytest tests/test_config/ -v

# Только валидация
pytest tests/test_config/test_config_validation.py -v

# Только загрузчик
pytest tests/test_config/test_loader.py -v
```

## Валидация конфигурации

Система автоматически валидирует:

- Корректность форматов таблиц
- Валидность правил оптимизации
- Наличие обязательных полей
- Типы данных

## Обратная совместимость

- Существующие форматы таблиц работают без изменений
- Поддержка исторических форматов данных
- Возможность миграции без потери данных

## Лучшие практики

1. **Сохранение стандартов**: Не изменяйте существующие форматы таблиц заказчика
2. **Валидация**: Всегда проверяйте конфигурацию перед использованием
3. **Документация**: Документируйте новые форматы и правила
4. **Тестирование**: Создавайте тесты для новых конфигураций
5. **Версионирование**: Используйте семантическое версионирование для конфигураций 