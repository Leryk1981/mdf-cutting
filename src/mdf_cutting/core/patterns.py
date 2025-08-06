"""
Модуль для работы с узорами раскроя.

Этот модуль содержит:
- Загрузку узоров из файлов
- Обработку узоров раскроя
- Валидацию узоров
"""

import os
from typing import Dict


def load_patterns(pattern_dir: str = "patterns") -> Dict:
    """
    Загружает узоры раскроя из директории.

    Args:
        pattern_dir: Директория с узорами

    Returns:
        Dict: Загруженные узоры
    """
    patterns = {}

    if not os.path.exists(pattern_dir):
        return patterns

    try:
        for filename in os.listdir(pattern_dir):
            if filename.endswith(".txt") or filename.endswith(".json"):
                # TODO: Реализовать загрузку узоров
                patterns[filename] = {}
    except Exception as e:
        print(f"Ошибка при загрузке узоров: {e}")

    return patterns
