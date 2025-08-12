"""
Улучшенная панель управления AI-оптимизацией.

Интеграция AI-функциональности с использованием стилей из UI шаблона
для создания профессионального и консистентного интерфейса.
"""

import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Any, Dict, List, Optional

from ...integration.ai_integration_service import AIIntegrationService
from ..desktop_app import DesktopApp
from .styles import AIStyles
from .toast_notification import ToastNotification


class AnimatedProgressBar(ttk.Progressbar):
    """Анимированный прогресс-бар на основе ui_shablon/css/preloader.css"""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, style="AI.Horizontal.TProgressbar", **kwargs)
        self.animation_active = False
        self.animation_speed = 50  # ms
        self.colors = ["#607D8B", "#90A4AE", "#B0BEC5"]  # Из шаблона
        self.color_index = 0

    def start_animation(self):
        """Запуск анимации как в шаблоне"""
        self.animation_active = True
        self._animate()

    def stop_animation(self):
        """Остановка анимации"""
        self.animation_active = False
        self["value"] = 0

    def _animate(self):
        """Анимация прогресс-бара"""
        if not self.animation_active:
            return

        # Изменение цвета как в шаблоне
        self.color_index = (self.color_index + 1) % len(self.colors)

        # Движение ползунка
        value = (self["value"] + 10) % 100
        self["value"] = value

        # Планирование следующего кадра
        self.after(self.animation_speed, self._animate)


class ImprovedAIControlPanel(ttk.Frame):
    """Улучшенная панель управления AI-оптимизацией"""

    def __init__(
        self,
        parent: tk.Widget,
        ai_service: AIIntegrationService,
        app: DesktopApp,
    ):
        super().__init__(parent)
        self.ai_service = ai_service
        self.app = app
        self.current_job_id = None
        self.current_suggestions = []
        self.processing_thread = None
        self.message_queue = queue.Queue()

        # Настройка стилей
        AIStyles.setup_ai_styles()

        # Инициализация уведомлений
        self.toast_notification = ToastNotification(self)

        self.setup_ui()
        self.setup_message_processing()

    def setup_ui(self):
        """Настройка улучшенного интерфейса"""
        # Основной контейнер с фоном из шаблона
        main_frame = ttk.Frame(self, style="AIPanel.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Заголовок в стиле шаблона
        title_frame = ttk.Frame(main_frame, style="AIPanel.TFrame")
        title_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = ttk.Label(
            title_frame,
            text="🤖 AI Оптимизация раскроя",
            font=("TkDefaultFont", 14, "bold"),
            foreground=AIStyles.COLORS["primary"],
        )
        title_label.pack(side=tk.LEFT, padx=(0, 10))

        # Индикатор статуса
        self.status_indicator = ttk.Label(
            title_frame,
            text="● AI готов",
            style="AI.Status.TLabel",
            foreground=AIStyles.COLORS["success"],
        )
        self.status_indicator.pack(side=tk.RIGHT)

        # Секция параметров AI с Material Design стилями
        params_frame = ttk.LabelFrame(
            main_frame,
            text="Параметры AI",
            style="AIPanel.TLabelframe",
            padding=15,
        )
        params_frame.pack(fill=tk.X, pady=(0, 15))

        # Улучшенный AI режим с toggle стилем
        ai_mode_frame = ttk.Frame(params_frame, style="AIPanel.TFrame")
        ai_mode_frame.pack(fill=tk.X, pady=(0, 10))

        self.ai_mode_var = tk.BooleanVar(value=True)
        self.ai_mode_toggle = ttk.Checkbutton(
            ai_mode_frame,
            text="Включить AI-ассистенцию",
            variable=self.ai_mode_var,
            command=self.on_ai_mode_changed,
            style="AI.Toggle.TCheckbutton",
        )
        self.ai_mode_toggle.pack(anchor=tk.W)

        # Улучшенный слайдер уверенности
        confidence_frame = ttk.Frame(params_frame, style="AIPanel.TFrame")
        confidence_frame.pack(fill=tk.X, pady=(5, 10))

        confidence_label = ttk.Label(
            confidence_frame,
            text="Порог уверенности:",
            font=("TkDefaultFont", 9),
        )
        confidence_label.pack(anchor=tk.W, pady=(0, 2))

        slider_container = ttk.Frame(confidence_frame, style="AIPanel.TFrame")
        slider_container.pack(fill=tk.X)

        self.confidence_var = tk.DoubleVar(value=0.7)
        self.confidence_scale = ttk.Scale(
            slider_container,
            from_=0.5,
            to=0.95,
            variable=self.confidence_var,
            orient=tk.HORIZONTAL,
            length=250,
            command=self.update_confidence_label,
        )
        self.confidence_scale.pack(side=tk.LEFT, padx=(0, 10))

        self.confidence_label = ttk.Label(
            slider_container,
            text="70%",
            font=("TkDefaultFont", 9, "bold"),
            foreground=AIStyles.COLORS["primary"],
        )
        self.confidence_label.pack(side=tk.LEFT)

        # Автоматическое применение
        self.auto_apply_var = tk.BooleanVar(value=False)
        auto_apply_check = ttk.Checkbutton(
            params_frame,
            text="Применять предложения автоматически",
            variable=self.auto_apply_var,
            style="AI.Toggle.TCheckbutton",
        )
        auto_apply_check.pack(anchor=tk.W, pady=(5, 0))

        # Секция действий с Material Design кнопками
        actions_frame = ttk.LabelFrame(
            main_frame,
            text="Действия",
            style="AIPanel.TLabelframe",
            padding=15,
        )
        actions_frame.pack(fill=tk.X, pady=(0, 15))

        button_frame = ttk.Frame(actions_frame, style="AIPanel.TFrame")
        button_frame.pack()

        # Кнопки в стиле шаблона
        self.optimize_btn = ttk.Button(
            button_frame,
            text="🚀 AI Оптимизировать",
            command=self.optimize_with_ai,
            style="AI.Primary.TButton",
            width=18,
        )
        self.optimize_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.leftover_btn = ttk.Button(
            button_frame,
            text="♻️ Использовать остатки",
            command=self.optimize_with_leftovers,
            style="AI.Success.TButton",
            width=18,
        )
        self.leftover_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.feedback_btn = ttk.Button(
            button_frame,
            text="💬 Обратная связь",
            command=self.open_feedback_dialog,
            style="AI.Primary.TButton",
            width=18,
        )
        self.feedback_btn.pack(side=tk.LEFT)

        # Секция статуса с улучшенным прогрессом
        status_frame = ttk.LabelFrame(
            main_frame,
            text="Статус AI",
            style="AIPanel.TLabelframe",
            padding=15,
        )
        status_frame.pack(fill=tk.X, pady=(0, 15))

        self.status_label = ttk.Label(
            status_frame,
            text="AI готов к работе",
            font=("TkDefaultFont", 9),
            foreground=AIStyles.COLORS["text_primary"],
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 8))

        # Анимированный прогресс-бар
        self.progress_bar = AnimatedProgressBar(
            status_frame, mode="indeterminate", length=400
        )
        self.progress_bar.pack(fill=tk.X)

        # Улучшенный лог с красивым скроллом
        log_frame = ttk.LabelFrame(
            main_frame,
            text="Лог операций",
            style="AIPanel.TLabelframe",
            padding=15,
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Контейнер для лога с пользовательским скроллом
        log_container = ttk.Frame(log_frame, style="AIPanel.TFrame")
        log_container.pack(fill=tk.BOTH, expand=True)

        # Текстовое поле для лога
        log_scroll = ttk.Scrollbar(log_container, width=10)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_container,
            height=8,
            width=60,
            yscrollcommand=log_scroll.set,
            wrap=tk.WORD,
            font=("TkDefaultFont", 8),
            background="white",
            relief=tk.SOLID,
            borderwidth=1,
            padx=10,
            pady=10,
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)

        # Настройка тегов для цветного вывода
        self.log_text.tag_config(
            "info", foreground=AIStyles.COLORS["text_primary"]
        )
        self.log_text.tag_config(
            "success", foreground=AIStyles.COLORS["success"]
        )
        self.log_text.tag_config(
            "warning", foreground=AIStyles.COLORS["warning"]
        )
        self.log_text.tag_config("error", foreground=AIStyles.COLORS["danger"])

        # Секция предложений с улучшенной таблицей
        suggestions_frame = ttk.LabelFrame(
            main_frame,
            text="Предложения AI",
            style="AIPanel.TLabelframe",
            padding=15,
        )
        suggestions_frame.pack(fill=tk.BOTH, expand=True)

        # Улучшенная таблица предложений
        columns = ("ID", "Тип", "Уверенность", "Потенциал")
        self.suggestions_tree = ttk.Treeview(
            suggestions_frame,
            columns=columns,
            show="headings",
            height=7,
            style="AI.Treeview",
        )

        # Настройка колонок
        for col in columns:
            self.suggestions_tree.heading(col, text=col)
            self.suggestions_tree.column(
                col,
                width=100,
                minwidth=80,
                stretch=tk.NO if col == "ID" else tk.YES,
            )

        # Скролл для таблицы
        suggestions_scroll = ttk.Scrollbar(
            suggestions_frame,
            orient=tk.VERTICAL,
            command=self.suggestions_tree.yview,
        )
        suggestions_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.suggestions_tree.configure(yscrollcommand=suggestions_scroll.set)

        # Настройка тегов для строк
        self.suggestions_tree.tag_configure(
            "high_confidence", background=AIStyles.COLORS["success"] + "20"
        )
        self.suggestions_tree.tag_configure(
            "medium_confidence", background=AIStyles.COLORS["warning"] + "30"
        )
        self.suggestions_tree.tag_configure(
            "low_confidence", background=AIStyles.COLORS["danger"] + "20"
        )

        # Контекстное меню
        self.setup_suggestion_menu()

        # Статус бар внизу
        self.setup_status_bar(main_frame)

    def setup_status_bar(self, parent: ttk.Widget):
        """Настройка статус бара как в шаблоне"""
        status_bar = ttk.Label(
            parent,
            text="AI готов к работе",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2),
            font=("TkDefaultFont", 8),
            foreground=AIStyles.COLORS["secondary"],
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        self.status_bar_label = status_bar

    def setup_message_processing(self):
        """Настройка обработки сообщений из фоновых потоков"""
        self.after(100, self.process_messages)

    def process_messages(self):
        """Обработка сообщений из очереди"""
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()

                if message["type"] == "log":
                    self.log_message(
                        message["text"], message.get("tag", "info")
                    )
                elif message["type"] == "status":
                    self.status_label.config(text=message["text"])
                elif message["type"] == "status_bar":
                    self.status_bar_label.config(text=message["text"])
                elif message["type"] == "toast":
                    self.toast_notification.show(
                        message["text"], message.get("level", "info")
                    )
                elif message["type"] == "update_suggestions":
                    self.update_suggestions(message["suggestions"])

        except queue.Empty:
            pass

        self.after(100, self.process_messages)

    def update_confidence_label(self, value):
        """Обновление метки порога уверенности"""
        confidence = int(float(value) * 100)
        self.confidence_label.config(text=f"{confidence}%")

    def log_message(self, message: str, tag: str = "info"):
        """Добавление цветного сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_entry, tag)
        self.log_text.see(tk.END)

        # Прокрутка вниз
        self.log_text.yview_moveto(1)

    def send_message(self, msg_type: str, text: str, **kwargs):
        """Отправка сообщения в очередь для обработки в основном потоке"""
        message = {"type": msg_type, "text": text, **kwargs}
        self.message_queue.put(message)

    def optimize_with_ai(self):
        """Запуск оптимизации с AI с улучшенной обработкой"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.toast_notification.show(
                "AI уже обрабатывает запрос", "warning"
            )
            return

        # Получение данных заказа
        order_data = self.get_current_order_data()
        if not order_data:
            self.toast_notification.show("Нет данных для оптимизации", "error")
            return

        # Обновление UI
        self.set_processing_state(True)
        self.send_message("status_bar", "AI обрабатывает запрос...")
        self.send_message("log", "Запуск AI-оптимизации", "info")

        # Запуск обработки в отдельном потоке
        self.processing_thread = threading.Thread(
            target=self._perform_optimization, args=(order_data,), daemon=True
        )
        self.processing_thread.start()

    def _perform_optimization(self, order_data: Dict[str, Any]):
        """Выполнение оптимизации в фоновом потоке"""
        try:
            # Обновление параметров AI
            self.ai_service.ai_assistance_mode = self.ai_mode_var.get()
            self.ai_service.auto_apply_corrections = self.auto_apply_var.get()
            self.ai_service.confidence_threshold = self.confidence_var.get()

            # Выполнение оптимизации
            result = self.ai_service.process_cutting_job(order_data)

            # Отправка результатов в основной поток
            self.send_message("log", "Оптимизация завершена", "success")
            self.send_message(
                "status_bar",
                f"Готово. Уверенность: {result.get('ai_confidence', 0):.2f}",
            )

            if result.get("status") == "success":
                self.send_message(
                    "update_suggestions",
                    suggestions=result.get("ai_enhancements", []),
                )
                self.after(
                    0,
                    lambda: self.app.update_dxf_display(
                        result.get("final_dxf")
                    ),
                )

                # Уведомление об успехе
                suggestions_count = len(result.get("ai_enhancements", []))
                self.send_message(
                    "toast",
                    f"Найдено {suggestions_count} предложений для улучшения",
                    "success",
                )
            else:
                self.send_message(
                    "log", f"Ошибка: {result.get('error', 'Unknown')}", "error"
                )
                self.send_message(
                    "toast",
                    f"Ошибка оптимизации: {result.get('error')}",
                    "error",
                )

            self.after(0, self.on_optimization_completed, result)

        except Exception as e:
            error_msg = str(e)
            self.send_message("log", f"Ошибка: {error_msg}", "error")
            self.send_message(
                "toast", f"Критическая ошибка: {error_msg}", "error"
            )
            self.after(0, self.on_optimization_failed, error_msg)

    def on_optimization_completed(self, result: Dict[str, Any]):
        """Обработка завершения оптимизации"""
        self.set_processing_state(False)
        self.status_indicator.config(
            text="● AI готов", foreground=AIStyles.COLORS["success"]
        )

    def on_optimization_failed(self, error_msg: str):
        """Обработка ошибки оптимизации"""
        self.set_processing_state(False)
        self.status_indicator.config(
            text="● Ошибка AI", foreground=AIStyles.COLORS["danger"]
        )
        self.status_label.config(text=f"Ошибка: {error_msg}")
        self.status_bar_label.config(text="AI ошибка при обработке")

    def set_processing_state(self, processing: bool):
        """Установка состояния обработки с анимацией"""
        if processing:
            self.optimize_btn.config(state=tk.DISABLED)
            self.leftover_btn.config(state=tk.DISABLED)
            self.status_label.config(text="AI обрабатывает данные...")
            self.status_indicator.config(
                text="● AI работает", foreground=AIStyles.COLORS["warning"]
            )
            self.progress_bar.start_animation()
        else:
            self.optimize_btn.config(state=tk.NORMAL)
            self.leftover_btn.config(state=tk.NORMAL)
            self.progress_bar.stop_animation()

    def optimize_with_leftovers(self):
        """Оптимизация с использованием остатков"""
        available_leftovers = self.get_available_leftovers()

        if not available_leftovers:
            self.toast_notification.show("Нет доступных остатков", "info")
            return

        order_data = self.get_current_order_data()
        if not order_data:
            return

        self.set_processing_state(True)
        self.send_message("status_bar", "Оптимизация с остатками...")
        self.send_message(
            "log", f"Использование {len(available_leftovers)} остатков", "info"
        )

        self.processing_thread = threading.Thread(
            target=self._perform_leftover_optimization,
            args=(order_data, available_leftovers),
            daemon=True,
        )
        self.processing_thread.start()

    def _perform_leftover_optimization(
        self, order_data: Dict, leftovers: List[Dict]
    ):
        """Оптимизация с остатками в фоне"""
        try:
            result = self.ai_service.process_with_leftovers(
                order_data, leftovers
            )

            savings = result.get("material_savings", 0)
            self.send_message(
                "log", f"Экономия материала: {savings:.1f}%", "success"
            )
            self.send_message(
                "status_bar", f"Готово. Экономия: {savings:.1f}%"
            )
            self.send_message(
                "toast", f"Сэкономлено {savings:.1f}% материала!", "success"
            )

            self.after(0, self.on_leftover_optimization_completed, result)

        except Exception as e:
            error_msg = str(e)
            self.send_message(
                "log", f"Ошибка оптимизации с остатками: {error_msg}", "error"
            )
            self.after(0, self.on_optimization_failed, error_msg)

    def on_leftover_optimization_completed(self, result: Dict[str, Any]):
        """Завершение оптимизации с остатками"""
        self.set_processing_state(False)
        self.status_indicator.config(
            text="● AI готов", foreground=AIStyles.COLORS["success"]
        )
        self.app.update_dxf_display(result.get("final_dxf"))

    def apply_selected_suggestion(self):
        """Применение выбранного предложения"""
        selected_items = self.suggestions_tree.selection()
        if not selected_items:
            self.toast_notification.show(
                "Выберите предложение для применения", "warning"
            )
            return

        item_id = selected_items[0]
        suggestion = self.getSuggestionData(item_id)

        if suggestion:
            self.send_message(
                "log",
                f'Применение предложения: {suggestion.get("correction_type")}',
                "info",
            )

            # Применение предложения
            if hasattr(self.app, "apply_correction"):
                self.app.apply_correction(suggestion)
                self.send_message(
                    "toast", "Предложение применено успешно!", "success"
                )

                # Удаление из списка
                self.suggestions_tree.delete(item_id)
            else:
                self.toast_notification.show(
                    "Метод apply_correction не найден", "error"
                )

    def show_suggestion_details(self):
        """Показ деталей предложения"""
        selected_items = self.suggestions_tree.selection()
        if not selected_items:
            return

        suggestion = self.getSuggestionData(selected_items[0])
        if suggestion:
            DetailDialog(self, suggestion)

    def reject_suggestion(self):
        """Отклонение предложения"""
        selected_items = self.suggestions_tree.selection()
        if selected_items:
            self.suggestions_tree.delete(selected_items[0])
            self.send_message(
                "log", "Предложение отклонено пользователем", "warning"
            )
            self.toast_notification.show("Предложение отклонено", "info")

    def update_suggestions(self, suggestions: List[Dict[str, Any]]):
        """Обновление таблицы предложений с цветовым выделением"""
        # Очистка таблицы
        for item in self.suggestions_tree.get_children():
            self.suggestions_tree.delete(item)

        self.current_suggestions = suggestions

        for i, suggestion in enumerate(suggestions):
            confidence = suggestion.get("confidence", 0)
            values = (
                suggestion.get("piece_id", "N/A"),
                suggestion.get("correction_type", "N/A"),
                f"{confidence:.2f}",
                f"{suggestion.get('expected_improvement', 0):.3f}",
            )

            item_id = self.suggestions_tree.insert("", tk.END, values=values)

            # Цветовое выделение по уровню уверенности
            if confidence >= 0.8:
                self.suggestions_tree.item(item_id, tags=("high_confidence",))
            elif confidence >= 0.6:
                self.suggestions_tree.item(
                    item_id, tags=("medium_confidence",)
                )
            else:
                self.suggestions_tree.item(item_id, tags=("low_confidence",))

    def getSuggestionData(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Получение данных предложения"""
        try:
            index = int(item_id.split("_")[1])
            return (
                self.current_suggestions[index]
                if index < len(self.current_suggestions)
                else None
            )
        except (IndexError, ValueError):
            return None

    def get_current_order_data(self) -> Optional[Dict[str, Any]]:
        """Получение данных текущего заказа"""
        try:
            pieces_data = (
                self.app.get_pieces_data()
                if hasattr(self.app, "get_pieces_data")
                else []
            )

            if not pieces_data:
                return None

            return {
                "order_id": f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "material_code": getattr(
                    self.app, "get_material_code", lambda: "MDF16"
                )(),
                "thickness": getattr(
                    self.app, "get_material_thickness", lambda: 16.0
                )(),
                "pieces": pieces_data,
            }
        except Exception as e:
            self.send_message(
                "log", f"Ошибка получения данных заказа: {str(e)}", "error"
            )
            return None

    def get_available_leftovers(self) -> List[Dict[str, Any]]:
        """Получение доступных остатков"""
        # Симуляция - в реальности запрос к БД
        return [
            {
                "id": "leftover_001",
                "area": 50000,
                "material_code": "MDF16",
                "geometry": {"width": 200, "height": 250},
            },
            {
                "id": "leftover_002",
                "area": 75000,
                "material_code": "MDF16",
                "geometry": {"width": 300, "height": 250},
            },
        ]

    def setup_suggestion_menu(self):
        """Настройка контекстного меню"""
        self.suggestion_menu = tk.Menu(self, tearoff=0)
        self.suggestion_menu.add_command(
            label="✓ Применить", command=self.apply_selected_suggestion
        )
        self.suggestion_menu.add_command(
            label="📋 Подробнее", command=self.show_suggestion_details
        )
        self.suggestion_menu.add_separator()
        self.suggestion_menu.add_command(
            label="✗ Отклонить", command=self.reject_suggestion
        )

        self.suggestions_tree.bind("<Button-3>", self.show_suggestion_menu)
        self.suggestions_tree.bind(
            "<Double-1>", lambda e: self.apply_selected_suggestion()
        )

    def show_suggestion_menu(self, event):
        """Показ контекстного меню"""
        if self.suggestions_tree.identify_region(event.x, event.y) == "cell":
            self.suggestion_menu.post(event.x_root, event.y_root)

    def on_ai_mode_changed(self):
        """Обработка изменения режима AI"""
        mode = "включена" if self.ai_mode_var.get() else "выключена"
        self.send_message("log", f"AI-ассистенция {mode}", "info")

        status_text = (
            "● AI готов" if self.ai_mode_var.get() else "● AI выключен"
        )
        status_color = (
            AIStyles.COLORS["success"]
            if self.ai_mode_var.get()
            else AIStyles.COLORS["danger"]
        )
        self.status_indicator.config(text=status_text, foreground=status_color)

    def open_feedback_dialog(self):
        """Открытие диалога обратной связи"""
        from .feedback_dialog import ImprovedFeedbackDialog

        ImprovedFeedbackDialog(self, self.ai_service.feedback_collector)


class DetailDialog(tk.Toplevel):
    """Диалог деталей предложения"""

    def __init__(self, parent, suggestion_data):
        super().__init__(parent)
        self.suggestion_data = suggestion_data

        self.title("Детали AI-предложения")
        self.geometry("450x350")
        self.resizable(False, False)

        self.setup_dialog()

    def setup_dialog(self):
        """Настройка диалога в стиле шаблона"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            main_frame,
            text="📋 Детали предложения",
            font=("TkDefaultFont", 12, "bold"),
            foreground=AIStyles.COLORS["primary"],
        )
        title_label.pack(pady=(0, 15))

        # Информация о предложении
        info_frame = ttk.LabelFrame(main_frame, text="Информация", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        details = [
            (
                "Тип корректировки:",
                self.suggestion_data.get("correction_type", "N/A"),
            ),
            ("ID детали:", self.suggestion_data.get("piece_id", "N/A")),
            (
                "Уверенность AI:",
                f"{self.suggestion_data.get('confidence', 0):.2f}",
            ),
            (
                "Потенциал улучшения:",
                f"{self.suggestion_data.get('expected_improvement', 0):.3f}",
            ),
        ]

        for label, value in details:
            row_frame = ttk.Frame(info_frame)
            row_frame.pack(fill=tk.X, pady=2)

            ttk.Label(
                row_frame, text=label, font=("TkDefaultFont", 9, "bold")
            ).pack(side=tk.LEFT)
            ttk.Label(row_frame, text=str(value)).pack(side=tk.RIGHT)

        # Параметры
        params_frame = ttk.LabelFrame(main_frame, text="Параметры", padding=10)
        params_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        params_text = tk.Text(params_frame, wrap=tk.WORD, height=8)
        params_text.pack(fill=tk.BOTH, expand=True)

        # Форматирование параметров
        params_content = "\n".join(
            [
                f"  {key}: {value}"
                for key, value in self.suggestion_data.get(
                    "parameters", {}
                ).items()
            ]
        )
        params_text.insert(tk.END, params_content)
        params_text.config(state=tk.DISABLED)

        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Закрыть",
            command=self.destroy,
            style="AI.Primary.TButton",
        ).pack(side=tk.RIGHT)
