"""
Визуализация результатов корректировок.

Этот модуль содержит:
- Визуализация карт раскроя
- Сравнение до/после корректировок
- Графики метрик качества
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CorrectionVisualizer:
    """Визуализатор результатов корректировок карт раскроя"""
    
    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        """Инициализация визуализатора."""
        self.figsize = figsize
        
        # Цветовая схема
        self.colors = {
            'original': '#1f77b4',
            'corrected': '#ff7f0e',
            'improvement': '#2ca02c',
            'waste': '#d62728',
            'background': '#f7f7f7'
        }
    
    def visualize_cutting_map(self, dxf_data: Dict[str, Any], 
                            corrections: List[Dict[str, Any]] = None,
                            save_path: Optional[str] = None):
        """Визуализация карты раскроя с корректировками."""
        logger.warning("Визуализация недоступна. Установите matplotlib для полной функциональности.")
        return None
    
    def plot_metrics_comparison(self, original_metrics: Dict[str, float],
                              corrected_metrics: Dict[str, float],
                              save_path: Optional[str] = None):
        """Сравнение метрик до и после корректировки."""
        logger.warning("Визуализация недоступна. Установите matplotlib для полной функциональности.")
        return None
    
    def plot_training_history(self, history: List[Dict[str, Any]], 
                            save_path: Optional[str] = None):
        """Визуализация истории обучения."""
        logger.warning("Визуализация недоступна. Установите matplotlib для полной функциональности.")
        return None
    
    def plot_feature_importance(self, feature_names: List[str], 
                              importance_scores: List[float],
                              save_path: Optional[str] = None):
        """Визуализация важности признаков."""
        logger.warning("Визуализация недоступна. Установите matplotlib для полной функциональности.")
        return None
    
    def create_summary_report(self, original_data: Dict[str, Any],
                            corrected_data: Dict[str, Any],
                            metrics: Dict[str, float],
                            save_dir: str) -> str:
        """Создание сводного отчета с визуализациями."""
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Создаем текстовый отчет
        report_path = save_dir / "correction_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("ОТЧЕТ О КОРРЕКТИРОВКЕ КАРТЫ РАСКРОЯ\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("ОБЩАЯ ОЦЕНКА:\n")
            f.write(f"Общий балл: {metrics.get('overall_score', 0):.3f}\n")
            f.write(f"Потенциал улучшения: {metrics.get('improvement_potential', 0):.3f}\n\n")
            
            f.write("МЕТРИКИ КАЧЕСТВА:\n")
            for metric_name, value in metrics.items():
                f.write(f"{metric_name}: {value:.3f}\n")
            
            f.write(f"\nВизуализации недоступны. Установите matplotlib.\n")
        
        logger.info(f"Сводный отчет создан: {report_path}")
        return str(report_path) 