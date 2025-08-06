# MDF Cutting Optimizer

[![CI](https://github.com/your-org/mdf-cutting-optimizer/workflows/CI/badge.svg)](https://github.com/your-org/mdf-cutting-optimizer/actions)
[![Codecov](https://codecov.io/gh/your-org/mdf-cutting-optimizer/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/mdf-cutting-optimizer)
[![PyPI](https://img.shields.io/pypi/v/mdf-cutting-optimizer.svg)](https://pypi.org/project/mdf-cutting-optimizer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Система для оптимизации раскроя МДФ с функциями AI-коррекции карт раскроя. Промышленное решение для автоматизации процесса учета остатков и оптимизации раскроя.

## 🚀 Возможности

- **Автоматическая оптимизация раскроя** - алгоритмы упаковки деталей
- **Генерация DXF файлов** - создание карт раскроя в стандартном формате
- **Управление остатками** - автоматический учет и оптимизация использования материалов
- **AI-коррекция карт** - автоматическая корректировка карт раскроя с помощью ИИ
- **Интерактивный GUI** - удобный интерфейс для работы с системой
- **Валидация изменений** - проверка корректности AI-корректировок

## 📋 Требования

- Python 3.8+
- PyQt6 для GUI
- ezdxf для работы с DXF файлами
- rectpack для алгоритмов упаковки

## 🛠️ Установка

### Из исходного кода

```bash
# Клонирование репозитория
git clone https://github.com/your-org/mdf-cutting-optimizer.git
cd mdf-cutting-optimizer

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt

# Установка в режиме разработки
pip install -e .
```

### Из PyPI

```bash
pip install mdf-cutting-optimizer
```

## 🚀 Быстрый старт

```python
from mdf_cutting.core.optimizer import CuttingOptimizer
from mdf_cutting.ui.desktop_app import CuttingApp

# Создание оптимизатора
optimizer = CuttingOptimizer()

# Запуск GUI приложения
app = CuttingApp()
app.run()
```

## 📁 Структура проекта

```
├── src/                    # Основной код
│   └── mdf_cutting/       # Пакет приложения
│       ├── core/          # Алгоритмы упаковки и оптимизации
│       ├── ui/            # Пользовательский интерфейс
│       ├── data/          # Менеджеры данных
│       ├── ai_module/     # AI-модуль для корректировки
│       └── utils/         # Вспомогательные утилиты
├── tests/                 # Тесты
├── docs/                  # Документация
├── scripts/               # Утилиты
├── configs/               # Конфигурации
└── .github/               # GitHub Actions
```

## 🧪 Разработка

### Установка инструментов разработки

```bash
pip install -r requirements-dev.txt
pre-commit install
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=src/mdf_cutting

# Только unit тесты
pytest -m unit

# Только интеграционные тесты
pytest -m integration
```

### Проверка качества кода

```bash
# Форматирование
black src/ tests/
isort src/ tests/

# Линтинг
flake8 src/ tests/
mypy src/

# Проверка безопасности
bandit -r src/
```

## 📊 Использование

### Базовое использование

```python
import pandas as pd
from mdf_cutting.core.optimizer import CuttingOptimizer

# Загрузка данных
details_df = pd.read_csv('details.csv')
materials_df = pd.read_csv('materials.csv')

# Создание оптимизатора
optimizer = CuttingOptimizer()

# Оптимизация раскроя
results = optimizer.optimize_cutting(details_df, materials_df)

# Генерация DXF файлов
dxf_files = optimizer.generate_dxf_files(results)

# Обновление остатков
updated_materials = optimizer.update_remnants(results)
```

### AI-коррекция карт

```python
from mdf_cutting.ai_module.dxf_parser import DXFParser
from mdf_cutting.ai_module.ml_model import CuttingOptimizer
from mdf_cutting.ai_module.validator import LayoutValidator

# Парсинг DXF файла
parser = DXFParser()
dxf_data = parser.parse_dxf('layout.dxf')

# AI-оптимизация
ai_optimizer = CuttingOptimizer()
corrections = ai_optimizer.predict_corrections(dxf_data)

# Валидация изменений
validator = LayoutValidator()
validation_result = validator.validate_corrections(dxf_data, corrections)
```

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта! Пожалуйста, ознакомьтесь с [CONTRIBUTING.md](CONTRIBUTING.md) для получения подробной информации о процессе разработки.

### Процесс разработки

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Внесите изменения и зафиксируйте их (`git commit -m 'Add amazing feature'`)
4. Отправьте изменения в ваш форк (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для подробностей.

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-org/mdf-cutting-optimizer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/mdf-cutting-optimizer/discussions)
- **Email**: dev@mdf-cutting.com

## 🗺️ Roadmap

- [ ] Полная реализация AI-модуля
- [ ] Интеграция с CAD системами
- [ ] Веб-интерфейс
- [ ] API для внешних систем
- [ ] Мобильное приложение
- [ ] Облачная версия

## 🙏 Благодарности

- [ezdxf](https://github.com/mozman/ezdxf) - библиотека для работы с DXF
- [rectpack](https://github.com/secnot/rectpack) - алгоритмы упаковки
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI фреймворк 