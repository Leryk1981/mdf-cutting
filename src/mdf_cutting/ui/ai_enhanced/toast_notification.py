"""
Система уведомлений Toast в стиле ui_shablon/js/toast-service.min.js.

Адаптация системы уведомлений из веб-интерфейса для tkinter.
"""

import time
import tkinter as tk

from .styles import AIStyles


class ToastNotification:
    """Система уведомлений в стиле ui_shablon/js/toast-service.min.js"""

    def __init__(self, master):
        self.master = master
        self.colors = AIStyles.COLORS
        self.current_toast = None

    def show(self, message: str, level: str = "info", duration: int = 3000):
        """Показать уведомление"""

        def _show():
            if self.current_toast:
                self.current_toast.destroy()

            # Создание окна поверх всех
            toast = tk.Toplevel(self.master)
            toast.overrideredirect(True)
            toast.attributes("-topmost", True)

            # Позиционирование top-right как в шаблоне
            x = self.master.winfo_x() + self.master.winfo_width() - 320
            y = self.master.winfo_y() + 100
            toast.geometry(f"300x80+{x}+{y}")

            # Стили по уровню уведомления
            bg_color = self._get_level_color(level)
            fg_color = "white"

            # Настройка фрейма
            frame = tk.Frame(toast, bg=bg_color, relief=tk.RAISED, bd=1)
            frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

            # Иконка и текст
            icon = self._get_level_icon(level)

            content_frame = tk.Frame(frame, bg=bg_color)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

            icon_label = tk.Label(
                content_frame,
                text=icon,
                bg=bg_color,
                fg=fg_color,
                font=("Segoe UI", 12),
            )
            icon_label.pack(side=tk.LEFT, padx=(0, 10))

            text_label = tk.Label(
                content_frame,
                text=message,
                bg=bg_color,
                fg=fg_color,
                font=("TkDefaultFont", 9),
                wraplength=250,
                justify=tk.LEFT,
            )
            text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            self.current_toast = toast

            # Анимация появления
            self._fade_in(toast)

            # Автоматическое закрытие
            toast.after(duration, lambda: self._fade_out(toast))

        # Запуск в основном потоке
        self.master.after(0, _show)

    def _get_level_color(self, level: str) -> str:
        """Получение цвета по уровню"""
        colors = {
            "success": self.colors["success"],
            "error": self.colors["danger"],
            "warning": self.colors["warning"],
            "info": self.colors["primary"],
        }
        return colors.get(level, self.colors["primary"])

    def _get_level_icon(self, level: str) -> str:
        """Получение иконки по уровню"""
        icons = {"success": "✓", "error": "✗", "warning": "⚠", "info": "ℹ"}
        return icons.get(level, "ℹ")

    def _fade_in(self, window):
        """Анимация появления"""
        for i in range(0, 11):
            window.attributes("-alpha", i / 10)
            window.update()
            time.sleep(0.02)

    def _fade_out(self, window):
        """Анимация исчезновения"""
        for i in range(10, -1, -1):
            window.attributes("-alpha", i / 10)
            window.update()
            time.sleep(0.02)
        window.destroy()
        if self.current_toast == window:
            self.current_toast = None
