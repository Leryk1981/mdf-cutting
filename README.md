# MDF Cutting Optimizer

[![CI](https://github.com/Leryk1981/mdf-cutting/workflows/CI/badge.svg)](https://github.com/Leryk1981/mdf-cutting/actions)
[![Codecov](https://codecov.io/gh/Leryk1981/mdf-cutting/branch/main/graph/badge.svg)](https://codecov.io/gh/Leryk1981/mdf-cutting)
[![PyPI](https://img.shields.io/pypi/v/mdf-cutting-optimizer.svg)](https://pypi.org/project/mdf-cutting-optimizer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Система для оптимизации раскроя МДФ с функциями AI-коррекции карт раскроя. Промышленное решение для автоматизации процесса учета остатков и оптимизации раскроя.

## 🚀 Возможности

- **Автоматическая оптимизация раскроя** - алгоритмы упаковки деталей.
- **Генерация DXF файлов** - создание карт раскроя в стандартном формате.
- **Управление остатками** - автоматический учет и оптимизация использования материалов.
- **AI-коррекция карт** - автоматическая корректировка карт раскроя с помощью ИИ.
- **Интерактивный GUI (Tkinter)** - удобный десктопный интерфейс для работы с системой.
- **Веб-интерфейс (FastAPI)** - API и UI для интеграции в веб.
- **Валидация изменений** - проверка корректности AI-корректировок.

## 📋 Требования

- Python 3.9+
- `tkinter` для GUI (обычно входит в стандартную библиотеку Python)
- `fastapi` и `uvicorn` для веб-интерфейса
- `ezdxf` для работы с DXF файлами
- `rectpack` для алгоритмов упаковки

## 🛠️ Установка

```bash
# Клонирование репозитория
git clone https://github.com/Leryk1981/mdf-cutting.git
cd mdf-cutting

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установка зависимостей
pip install -r requirements.txt
```

## 🚀 Запуск приложения

Система поддерживает несколько режимов запуска:

### 1. Графический интерфейс (GUI)

Это основной режим для большинства пользователей. Запустите его командой:

```bash
python main.py
```

### 2. Веб-интерфейс и API

Для запуска веб-сервера используйте `uvicorn`:

```bash
uvicorn web-ui.api.main:app --host 0.0.0.0 --port 8007
```

После запуска веб-интерфейс будет доступен по адресу `http://localhost:8007`.

## 🖼️ Демонстрация

### Графический интерфейс (GUI)

*[Скриншот основного окна GUI]*

### Веб-интерфейс

*[Скриншот веб-интерфейса]*

## 📁 Структура проекта

```
├── src/                    # Основной код
│   └── mdf_cutting/       # Пакет приложения
│       ├── core/          # Алгоритмы упаковки и оптимизации
│       ├── ui/            # Пользовательский интерфейс (десктоп)
│       ├── web-ui/        # Веб-интерфейс и API
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
```

### Проверка качества кода

```bash
# Форматирование
black .
isort .

# Линтинг
flake8 .
mypy src/

# Проверка безопасности
bandit -r src/
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

- **Issues**: [GitHub Issues](https://github.com/Leryk1981/mdf-cutting/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Leryk1981/mdf-cutting/discussions)
- **Email**: dev@mdf-cutting.com

## 🗺️ Roadmap

- [x] Веб-интерфейс
- [ ] Полная реализация AI-модуля
- [ ] Интеграция с CAD системами
- [ ] API для внешних систем
- [ ] Мобильное приложение
- [ ] Облачная версия

## 🙏 Благодарности

- [ezdxf](https://github.com/mozman/ezdxf) - библиотека для работы с DXF
- [rectpack](https://github.com/secnot/rectpack) - алгоритмы упаковки
- [FastAPI](https://fastapi.tiangolo.com/) - веб-фреймворк