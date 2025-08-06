"""
AI-улучшенный пользовательский интерфейс.

Модуль содержит компоненты интерфейса с интеграцией AI-функциональности,
использующие стили из UI шаблона для создания профессионального и консистентного интерфейса.
"""

from .ai_control_panel import ImprovedAIControlPanel
from .feedback_dialog import ImprovedFeedbackDialog
from .styles import AIStyles
from .toast_notification import ToastNotification

__all__ = [
    "AIStyles",
    "ImprovedAIControlPanel",
    "ToastNotification",
    "ImprovedFeedbackDialog",
]
