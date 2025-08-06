"""
Улучшенный диалог обратной связи в Material Design стиле.

Адаптация диалога обратной связи с использованием стилей из UI шаблона.
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import List

from .styles import AIStyles


class ImprovedFeedbackDialog(tk.Toplevel):
    """Улучшенный диалог обратной связи в Material Design стиле"""

    def __init__(self, parent, feedback_collector):
        super().__init__(parent)
        self.feedback_collector = feedback_collector

        self.title("💬 Обратная связь о работе AI")
        self.geometry("550x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Центрирование
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (550 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (450 // 2)
        self.geometry(f"+{x}+{y}")

        self.setup_dialog()

    def setup_dialog(self):
        """Настройка диалога"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="Помогите улучшить работу AI",
            font=("TkDefaultFont", 14, "bold"),
            foreground=AIStyles.COLORS["primary"],
        )
        title_label.pack(pady=(0, 15))

        subtitle_label = ttk.Label(
            main_frame,
            text="Ваш отзыв поможет нам сделать систему лучше",
            font=("TkDefaultFont", 9),
            foreground=AIStyles.COLORS["secondary"],
        )
        subtitle_label.pack(pady=(0, 20))

        # Рейтинг с Material Design стилями
        rating_frame = ttk.LabelFrame(
            main_frame, text="Оцените работу AI", padding=15
        )
        rating_frame.pack(fill=tk.X, pady=(0, 15))

        rating_label = ttk.Label(
            rating_frame,
            text="Насколько вы довольны работой AI?",
            font=("TkDefaultFont", 10),
        )
        rating_label.pack(anchor=tk.W, pady=(0, 10))

        stars_frame = ttk.Frame(rating_frame)
        stars_frame.pack()

        self.rating_var = tk.IntVar(value=3)

        # Звёздочки для оценки
        for i in range(1, 6):
            star = ttk.Radiobutton(
                stars_frame,
                text="★" if i <= 3 else "☆",
                variable=self.rating_var,
                value=i,
                width=3,
            )
            star.pack(side=tk.LEFT, padx=2)

        # Принятые/отклоненные предложения
        suggestions_frame = ttk.LabelFrame(
            main_frame, text="Предложения AI", padding=15
        )
        suggestions_frame.pack(fill=tk.X, pady=(0, 15))

        accepted_label = ttk.Label(
            suggestions_frame,
            text="Принятые предложения (ID через запятую):",
            font=("TkDefaultFont", 9),
        )
        accepted_label.pack(anchor=tk.W, pady=(0, 5))

        self.accepted_entry = ttk.Entry(
            suggestions_frame, font=("TkDefaultFont", 9)
        )
        self.accepted_entry.pack(fill=tk.X)

        rejected_label = ttk.Label(
            suggestions_frame,
            text="Отклоненные предложения (ID через запятую):",
            font=("TkDefaultFont", 9),
        )
        rejected_label.pack(anchor=tk.W, pady=(10, 5))

        self.rejected_entry = ttk.Entry(
            suggestions_frame, font=("TkDefaultFont", 9)
        )
        self.rejected_entry.pack(fill=tk.X)

        # Комментарии
        comments_frame = ttk.LabelFrame(
            main_frame, text="Комментарии", padding=15
        )
        comments_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        comments_label = ttk.Label(
            comments_frame,
            text="Дополнительные комментарии и пожелания:",
            font=("TkDefaultFont", 9),
        )
        comments_label.pack(anchor=tk.W, pady=(0, 5))

        self.comments_text = tk.Text(
            comments_frame,
            height=8,
            font=("TkDefaultFont", 9),
            wrap=tk.WORD,
            padx=10,
            pady=10,
        )
        self.comments_text.pack(fill=tk.BOTH, expand=True)

        # Чекбокс для обучения
        self.training_var = tk.BooleanVar(value=True)
        training_check = ttk.Checkbutton(
            main_frame,
            text="Использовать этот отзыв для улучшения AI",
            variable=self.training_var,
        )
        training_check.pack(anchor=tk.W, pady=(10, 0))

        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Отправить",
            command=self.submit_feedback,
            style="AI.Success.TButton",
            width=12,
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            button_frame,
            text="Отмена",
            command=self.destroy,
            style="AI.Primary.TButton",
            width=12,
        ).pack(side=tk.RIGHT)

    def submit_feedback(self):
        """Отправка обратной связи"""
        # Валидация
        if self.rating_var.get() < 1:
            self.bell()
            return

        # Парсинг ID
        accepted_ids = self._parse_ids(self.accepted_entry.get())
        rejected_ids = self._parse_ids(self.rejected_entry.get())

        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "satisfaction_rating": self.rating_var.get(),
            "accepted_corrections": accepted_ids,
            "rejected_corrections": rejected_ids,
            "comments": self.comments_text.get("1.0", tk.END).strip(),
            "include_in_training": self.training_var.get(),
        }

        try:
            result = self.feedback_collector.collect_feedback(feedback_data)

            # Показ успешного отправления
            self.show_success_message()
            self.destroy()

        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось отправить отзыв: {str(e)}"
            )

    def _parse_ids(self, text: str) -> List[str]:
        """Парсинг списка ID"""
        if not text.strip():
            return []
        return [id_str.strip() for id_str in text.split(",") if id_str.strip()]

    def show_success_message(self):
        """Показ сообщения об успехе"""
        success_window = tk.Toplevel(self)
        success_window.title("Отзыв отправлен")
        success_window.geometry("300x150")
        success_window.transient(self)

        success_window.geometry(
            "+%d+%d"
            % (
                self.winfo_x() + (self.winfo_width() // 2) - 150,
                self.winfo_y() + (self.winfo_height() // 2) - 75,
            )
        )

        ttk.Label(
            success_window,
            text="✓ Спасибо за отзыв!",
            font=("TkDefaultFont", 12, "bold"),
            foreground=AIStyles.COLORS["success"],
        ).pack(pady=20)

        ttk.Label(
            success_window,
            text="Ваш отзыв поможет улучшить AI",
            font=("TkDefaultFont", 9),
        ).pack(pady=(0, 20))

        ttk.Button(
            success_window,
            text="Закрыть",
            command=success_window.destroy,
            style="AI.Primary.TButton",
            width=10,
        ).pack()
