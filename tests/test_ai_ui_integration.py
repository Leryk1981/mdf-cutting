"""
Тесты интеграции AI-модуля с пользовательским интерфейсом.

Проверка работы AI-компонентов и их интеграции с основным приложением.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Добавление пути к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mdf_cutting.ui.ai_enhanced.styles import AIStyles
from mdf_cutting.ui.ai_enhanced.toast_notification import ToastNotification
from mdf_cutting.ui.ai_enhanced.feedback_dialog import ImprovedFeedbackDialog
from mdf_cutting.ui.ai_enhanced.ai_control_panel import (
    ImprovedAIControlPanel, 
    AnimatedProgressBar,
    DetailDialog
)
from mdf_cutting.integration.ai_integration_service import AIIntegrationService
from mdf_cutting.integration.feedback_collector import FeedbackCollector


class TestAIStyles(unittest.TestCase):
    """Тесты стилевой системы AI"""
    
    def setUp(self):
        """Настройка тестов"""
        self.root = tk.Tk()
        self.root.withdraw()  # Скрываем окно
    
    def tearDown(self):
        """Очистка после тестов"""
        self.root.destroy()
    
    def test_colors_defined(self):
        """Проверка определения цветов"""
        self.assertIn('primary', AIStyles.COLORS)
        self.assertIn('success', AIStyles.COLORS)
        self.assertIn('danger', AIStyles.COLORS)
        self.assertIn('background', AIStyles.COLORS)
    
    def test_setup_ai_styles(self):
        """Проверка настройки стилей"""
        try:
            AIStyles.setup_ai_styles()
            # Если не возникло исключений, стили настроены корректно
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Ошибка настройки стилей: {e}")


class TestToastNotification(unittest.TestCase):
    """Тесты системы уведомлений"""
    
    def setUp(self):
        """Настройка тестов"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.toast = ToastNotification(self.root)
    
    def tearDown(self):
        """Очистка после тестов"""
        self.root.destroy()
    
    def test_toast_creation(self):
        """Проверка создания уведомления"""
        self.assertIsNotNone(self.toast)
        self.assertEqual(self.toast.master, self.root)
    
    def test_level_colors(self):
        """Проверка цветов по уровням"""
        success_color = self.toast._get_level_color('success')
        error_color = self.toast._get_level_color('error')
        info_color = self.toast._get_level_color('info')
        
        self.assertIsInstance(success_color, str)
        self.assertIsInstance(error_color, str)
        self.assertIsInstance(info_color, str)
        self.assertNotEqual(success_color, error_color)
    
    def test_level_icons(self):
        """Проверка иконок по уровням"""
        success_icon = self.toast._get_level_icon('success')
        error_icon = self.toast._get_level_icon('error')
        info_icon = self.toast._get_level_icon('info')
        
        self.assertIsInstance(success_icon, str)
        self.assertIsInstance(error_icon, str)
        self.assertIsInstance(info_icon, str)
        self.assertNotEqual(success_icon, error_icon)


class TestAnimatedProgressBar(unittest.TestCase):
    """Тесты анимированного прогресс-бара"""
    
    def setUp(self):
        """Настройка тестов"""
        self.root = tk.Tk()
        self.root.withdraw()
        self.progress = AnimatedProgressBar(self.root)
    
    def tearDown(self):
        """Очистка после тестов"""
        self.root.destroy()
    
    def test_progress_creation(self):
        """Проверка создания прогресс-бара"""
        self.assertIsNotNone(self.progress)
        self.assertFalse(self.progress.animation_active)
    
    def test_animation_control(self):
        """Проверка управления анимацией"""
        self.progress.start_animation()
        self.assertTrue(self.progress.animation_active)
        
        self.progress.stop_animation()
        self.assertFalse(self.progress.animation_active)


class TestImprovedAIControlPanel(unittest.TestCase):
    """Тесты улучшенной панели управления AI"""
    
    def setUp(self):
        """Настройка тестов"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Моки для сервисов
        self.ai_service = Mock(spec=AIIntegrationService)
        self.app = Mock()
        
        # Создание панели
        self.panel = ImprovedAIControlPanel(self.root, self.ai_service, self.app)
    
    def tearDown(self):
        """Очистка после тестов"""
        self.root.destroy()
    
    def test_panel_creation(self):
        """Проверка создания панели"""
        self.assertIsNotNone(self.panel)
        self.assertEqual(self.panel.ai_service, self.ai_service)
        self.assertEqual(self.panel.app, self.app)
    
    def test_ui_components(self):
        """Проверка наличия UI компонентов"""
        # Проверяем, что основные компоненты созданы
        self.assertIsNotNone(self.panel.optimize_btn)
        self.assertIsNotNone(self.panel.leftover_btn)
        self.assertIsNotNone(self.panel.feedback_btn)
        self.assertIsNotNone(self.panel.progress_bar)
        self.assertIsNotNone(self.panel.suggestions_tree)
    
    def test_confidence_label_update(self):
        """Проверка обновления метки уверенности"""
        self.panel.confidence_var.set(0.75)
        self.panel.update_confidence_label(0.75)
        self.assertEqual(self.panel.confidence_label.cget('text'), '75%')
    
    def test_ai_mode_change(self):
        """Проверка изменения режима AI"""
        initial_state = self.panel.ai_mode_var.get()
        self.panel.ai_mode_var.set(not initial_state)
        self.panel.on_ai_mode_changed()
        
        # Проверяем, что обработчик вызвался без ошибок
        self.assertTrue(True)
    
    def test_get_available_leftovers(self):
        """Проверка получения остатков"""
        leftovers = self.panel.get_available_leftovers()
        self.assertIsInstance(leftovers, list)
        self.assertGreater(len(leftovers), 0)
        
        # Проверяем структуру данных
        for leftover in leftovers:
            self.assertIn('id', leftover)
            self.assertIn('area', leftover)
            self.assertIn('material_code', leftover)
    
    def test_suggestion_data_parsing(self):
        """Проверка парсинга данных предложений"""
        # Тестовые данные
        test_suggestions = [
            {
                'piece_id': 'test_001',
                'correction_type': 'rotation',
                'confidence': 0.85,
                'expected_improvement': 0.12
            }
        ]
        
        self.panel.current_suggestions = test_suggestions
        self.panel.update_suggestions(test_suggestions)
        
        # Проверяем, что предложение добавлено в таблицу
        children = self.panel.suggestions_tree.get_children()
        self.assertGreater(len(children), 0)


class TestDetailDialog(unittest.TestCase):
    """Тесты диалога деталей"""
    
    def setUp(self):
        """Настройка тестов"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.suggestion_data = {
            'piece_id': 'test_001',
            'correction_type': 'rotation',
            'confidence': 0.85,
            'expected_improvement': 0.12,
            'parameters': {
                'angle': 90,
                'priority': 'high'
            }
        }
        
        self.dialog = DetailDialog(self.root, self.suggestion_data)
    
    def tearDown(self):
        """Очистка после тестов"""
        self.dialog.destroy()
        self.root.destroy()
    
    def test_dialog_creation(self):
        """Проверка создания диалога"""
        self.assertIsNotNone(self.dialog)
        self.assertEqual(self.dialog.suggestion_data, self.suggestion_data)
    
    def test_dialog_title(self):
        """Проверка заголовка диалога"""
        self.assertEqual(self.dialog.title(), "Детали AI-предложения")


class TestImprovedFeedbackDialog(unittest.TestCase):
    """Тесты улучшенного диалога обратной связи"""
    
    def setUp(self):
        """Настройка тестов"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.feedback_collector = Mock(spec=FeedbackCollector)
        self.dialog = ImprovedFeedbackDialog(self.root, self.feedback_collector)
    
    def tearDown(self):
        """Очистка после тестов"""
        self.dialog.destroy()
        self.root.destroy()
    
    def test_dialog_creation(self):
        """Проверка создания диалога"""
        self.assertIsNotNone(self.dialog)
        self.assertEqual(self.dialog.feedback_collector, self.feedback_collector)
    
    def test_rating_variable(self):
        """Проверка переменной рейтинга"""
        self.assertIsNotNone(self.dialog.rating_var)
        self.assertEqual(self.dialog.rating_var.get(), 3)  # Значение по умолчанию
    
    def test_id_parsing(self):
        """Проверка парсинга ID"""
        # Тест пустой строки
        result = self.dialog._parse_ids("")
        self.assertEqual(result, [])
        
        # Тест строки с ID
        result = self.dialog._parse_ids("001, 002, 003")
        self.assertEqual(result, ['001', '002', '003'])
        
        # Тест строки с пробелами
        result = self.dialog._parse_ids(" 001 , 002 ")
        self.assertEqual(result, ['001', '002'])
    
    @patch('tkinter.messagebox.showerror')
    def test_feedback_submission_error(self, mock_showerror):
        """Проверка обработки ошибки при отправке отзыва"""
        # Настраиваем мок для вызова исключения
        self.feedback_collector.collect_feedback.side_effect = Exception("Test error")
        
        # Устанавливаем рейтинг
        self.dialog.rating_var.set(5)
        
        # Вызываем отправку отзыва
        self.dialog.submit_feedback()
        
        # Проверяем, что было показано сообщение об ошибке
        mock_showerror.assert_called_once()


class TestAIIntegration(unittest.TestCase):
    """Интеграционные тесты AI-интерфейса"""
    
    def setUp(self):
        """Настройка тестов"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Создание моков
        self.ai_service = Mock(spec=AIIntegrationService)
        self.app = Mock()
        
        # Настройка моков
        self.ai_service.process_cutting_job.return_value = {
            'status': 'success',
            'ai_confidence': 0.85,
            'ai_enhancements': [
                {
                    'piece_id': 'test_001',
                    'correction_type': 'rotation',
                    'confidence': 0.85,
                    'expected_improvement': 0.12
                }
            ]
        }
        
        self.panel = ImprovedAIControlPanel(self.root, self.ai_service, self.app)
    
    def tearDown(self):
        """Очистка после тестов"""
        self.root.destroy()
    
    def test_optimization_workflow(self):
        """Проверка полного цикла оптимизации"""
        # Настраиваем мок для получения данных заказа
        self.app.get_pieces_data.return_value = [
            {'id': 'piece_001', 'width': 100, 'height': 200}
        ]
        
        # Запускаем оптимизацию
        self.panel.optimize_with_ai()
        
        # Проверяем, что AI сервис был вызван
        self.ai_service.process_cutting_job.assert_called_once()
        
        # Проверяем, что параметры были переданы
        call_args = self.ai_service.process_cutting_job.call_args[0][0]
        self.assertIn('order_id', call_args)
        self.assertIn('pieces', call_args)
    
    def test_leftover_optimization_workflow(self):
        """Проверка оптимизации с остатками"""
        # Настраиваем мок
        self.app.get_pieces_data.return_value = [
            {'id': 'piece_001', 'width': 100, 'height': 200}
        ]
        
        self.ai_service.process_with_leftovers.return_value = {
            'status': 'success',
            'material_savings': 15.5
        }
        
        # Запускаем оптимизацию с остатками
        self.panel.optimize_with_leftovers()
        
        # Проверяем, что сервис был вызван
        self.ai_service.process_with_leftovers.assert_called_once()


if __name__ == '__main__':
    unittest.main() 