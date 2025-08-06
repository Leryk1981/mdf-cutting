"""
API для интеграции AI-модуля.

Этот модуль содержит:
- API для получения корректировок
- Интеграция с основной системой
"""

from .correction_api import CorrectionAPI

__all__ = [
    "CorrectionAPI"
] 