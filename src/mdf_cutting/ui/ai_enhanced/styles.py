"""
Стили для AI-компонентов на основе UI шаблона.

Адаптация цветовой схемы и стилей из ui_shablon/css/app.css
для создания консистентного интерфейса.
"""

import tkinter as tk
from tkinter import ttk


class AIStyles:
    """Стили для AI-компонентов на основе UI шаблона"""

    # Цветовая схема из ui_shablon/css/app.css
    COLORS = {
        "primary": "#607D8B",  # Основной синий (btn-clo)
        "secondary": "#90A4AE",  # Вторичный серый
        "success": "#2e7d32",  # Зеленый (button-success)
        "danger": "#c62828",  # Красный (button-danger)
        "warning": "#8C7601",  # Золотой (gold-cell)
        "background": "#f5f5f5",  # Светло-серый фон
        "text_primary": "#263238",  # Основной текст
        "border": "#CFD8DC",  # Серая граница
    }

    @classmethod
    def setup_ai_styles(cls):
        """Настройка стилей для AI-компонентов"""
        style = ttk.Style()

        # Стили для панелей AI (адаптация из шаблона)
        style.configure("AIPanel.TFrame", background=cls.COLORS["background"])

        style.configure(
            "AIPanel.TLabelframe",
            background=cls.COLORS["background"],
            bordercolor=cls.COLORS["border"],
            relief=tk.RIDGE,
            borderwidth=1,
        )

        style.configure(
            "AIPanel.TLabelframe.Label",
            background=cls.COLORS["primary"],
            foreground="white",
            font=("TkDefaultFont", 10, "bold"),
            padding=(5, 5),
        )

        # Стили кнопок (на основе шаблона)
        style.configure(
            "AI.Primary.TButton",
            background=cls.COLORS["primary"],
            foreground="white",
            font=("TkDefaultFont", 10, "bold"),
            padding=(10, 5),
            borderwidth=0,
        )

        style.map(
            "AI.Primary.TButton",
            background=[
                ("active", cls.COLORS["secondary"]),
                ("pressed", cls.COLORS["text_primary"]),
            ],
        )

        style.configure(
            "AI.Success.TButton",
            background=cls.COLORS["success"],
            foreground="white",
        )

        style.map(
            "AI.Success.TButton",
            background=[("active", "#388E3C"), ("pressed", "#1B5E20")],
        )

        style.configure(
            "AI.Danger.TButton",
            background=cls.COLORS["danger"],
            foreground="white",
        )

        # Стили для таблицы предложений
        style.configure(
            "AI.Treeview",
            background="white",
            foreground=cls.COLORS["text_primary"],
            rowheight=25,
            borderwidth=1,
            relief=tk.SOLID,
        )

        style.configure(
            "AI.Treeview.Heading",
            background=cls.COLORS["primary"],
            foreground="white",
            font=("TkDefaultFont", 9, "bold"),
        )

        style.map(
            "AI.Treeview.Heading",
            background=[("active", cls.COLORS["secondary"])],
        )

        # Стили для прогресс-бара (на основе шаблона)
        style.configure(
            "AI.Horizontal.TProgressbar",
            background=cls.COLORS["primary"],
            troughcolor=cls.COLORS["background"],
            borderwidth=0,
        )

        # Стили для меток статуса
        style.configure(
            "AI.Status.TLabel",
            font=("TkDefaultFont", 9),
            foreground=cls.COLORS["success"],
        )

        # Стили для переключателей
        style.configure(
            "AI.Toggle.TCheckbutton",
            background=cls.COLORS["background"],
            indicatoron=False,
            padding=(20, 0),
            font=("TkDefaultFont", 9),
        )

        # Настраиваемые изображения для переключателей
        cls._create_toggle_images()

    @classmethod
    def _create_toggle_images(cls):
        """Создание изображений для переключателей как в ui_shablon/css/toggle.css"""
        # Создаем изображения для состояния ON/OFF
        toggle_on = tk.PhotoImage(width=40, height=20)
        toggle_off = tk.PhotoImage(width=40, height=20)

        # В реальной реализации здесь была заливка цветами,
        # но для простоты используем готовые стили

        setattr(cls, "_toggle_on_image", toggle_on)
        setattr(cls, "_toggle_off_image", toggle_off)
