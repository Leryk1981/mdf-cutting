"""
Сервис интеграции AI-модуля с основной системой раскроя.

Обеспечивает:
- Интеграцию AI-предложений с традиционным оптимизатором
- Работу с остатками материала
- Сбор и анализ обратной связи
- Логирование всех операций
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ..ai_module.api.correction_api import CorrectionAPI
from ..config.loader import ConfigLoader
from ..core.optimizer import CuttingOptimizer
from ..core.packing import PackingAlgorithm
from ..utils.logger import setup_logger


class AIIntegrationService:
    """Основной сервис интеграции AI с системой раскроя."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """Инициализация сервиса интеграции."""
        self.config_loader = config_loader or ConfigLoader()
        self.config_loader.load_all()

        # Инициализация компонентов
        self.ai_api = CorrectionAPI()
        self.optimizer = CuttingOptimizer()
        self.packing_algorithm = PackingAlgorithm()
        self.logger = setup_logger("ai_integration")

        # Конфигурация
        self.config = self.config_loader._configs.get("optimization_rules", {})
        self.ai_enabled = self.config.get("ai_enabled", True)
        self.leftovers_enabled = self.config.get("leftovers_enabled", True)
        self.feedback_enabled = self.config.get("feedback_enabled", True)

        # Статистика
        self.processing_stats = {
            "total_jobs": 0,
            "ai_assisted_jobs": 0,
            "leftovers_used": 0,
            "average_processing_time": 0.0,
        }

        self.logger.info("AIIntegrationService initialized successfully")

    def process_cutting_job(
        self, order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Обработка задания на раскрой с интеграцией AI."""
        start_time = datetime.now()

        try:
            # Логирование начала обработки
            self.logger.log_processing_step(
                "job_started",
                {
                    "order_id": order_data.get("order_id", "unknown"),
                    "pieces_count": len(order_data.get("pieces", [])),
                    "material_code": order_data.get(
                        "material_code", "unknown"
                    ),
                },
            )

            # 1. Базовая оптимизация
            base_result = self._perform_base_optimization(order_data)

            # 2. Анализ остатков (если включено)
            leftovers_analysis = None
            if self.leftovers_enabled:
                available_leftovers = self._get_available_leftovers(order_data)
                leftovers_analysis = self._analyze_leftovers(
                    available_leftovers, order_data
                )

            # 3. AI-улучшения (если включено)
            ai_enhancement = None
            if self.ai_enabled:
                ai_enhancement = self._apply_ai_enhancements(
                    base_result, order_data, leftovers_analysis
                )

            # 4. Оптимизация с остатками (если применимо)
            final_result = base_result
            if (
                leftovers_analysis
                and leftovers_analysis.get("use_leftovers", False)
                and ai_enhancement
                and ai_enhancement.get("enhancement_applied", False)
            ):
                final_result = self._optimize_with_leftovers(
                    order_data, available_leftovers
                )

            # 5. Применение AI-корректировок
            final_corrections = []
            if ai_enhancement and ai_enhancement.get("corrections"):
                for correction in ai_enhancement["corrections"]:
                    result = self._apply_correction(correction, final_result)
                    if result["status"] == "success":
                        final_corrections.append(correction)
                        Path(result["corrected_file"])

            # 6. Формирование итогового результата
            processing_time = (datetime.now() - start_time).total_seconds()

            result = {
                **final_result,
                "ai_enhancements": (
                    ai_enhancement["corrections"] if ai_enhancement else []
                ),
                "applied_corrections": final_corrections,
                "was_ai_assisted": (
                    ai_enhancement["enhancement_applied"]
                    if ai_enhancement
                    else False
                ),
                "leftovers_analysis": leftovers_analysis,
                "ai_confidence": (
                    ai_enhancement["ai_confidence"] if ai_enhancement else 0.0
                ),
                "processing_time_ms": int(processing_time * 1000),
                "timestamp": datetime.now().isoformat(),
            }

            # 7. Обновление статистики
            self._update_processing_stats(processing_time, result)

            # 8. Логирование результата
            self._log_processing_result(result, processing_time)

            return result

        except Exception as e:
            self.logger.error(f"Error in cutting job processing: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "order_id": order_data.get("order_id", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

    def _perform_base_optimization(
        self, order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Выполнение базовой оптимизации без AI."""
        try:
            # Использование традиционного оптимизатора
            optimization_result = self.optimizer.optimize(order_data)

            # Применение алгоритма упаковки
            packing_result = self.packing_algorithm.pack(
                optimization_result["pieces"],
                optimization_result["sheet_size"],
            )

            return {
                "status": "success",
                "optimization_result": optimization_result,
                "packing_result": packing_result,
                "utilization_rate": packing_result.get(
                    "utilization_rate", 0.0
                ),
                "waste_percentage": packing_result.get(
                    "waste_percentage", 0.0
                ),
                "total_pieces": len(optimization_result["pieces"]),
                "dxf_file": packing_result.get("dxf_file", ""),
                "was_ai_assisted": False,
            }

        except Exception as e:
            self.logger.error(f"Error in base optimization: {str(e)}")
            raise

    def _get_available_leftovers(
        self, order_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Получение доступных остатков для заказа."""
        try:
            # В реальной реализации здесь был бы запрос к базе данных остатков
            # Для примера возвращаем тестовые данные

            material_code = order_data.get("material_code", "MDF")

            return [
                {
                    "id": "leftover_001",
                    "area": 50000,  # 0.5м²
                    "width": 500,
                    "height": 100,
                    "material_code": material_code,
                    "thickness": order_data.get("thickness", 16.0),
                    "priority": 0.8,
                },
                {
                    "id": "leftover_002",
                    "area": 30000,  # 0.3м²
                    "width": 300,
                    "height": 100,
                    "material_code": material_code,
                    "thickness": order_data.get("thickness", 16.0),
                    "priority": 0.6,
                },
            ]

        except Exception as e:
            self.logger.error(f"Error getting available leftovers: {str(e)}")
            return []

    def _analyze_leftovers(
        self, available_leftovers: List[Dict], order_data: Dict
    ) -> Dict[str, Any]:
        """Анализ пригодности остатков для текущего заказа."""
        try:
            order_pieces = order_data.get("pieces", [])
            total_area = sum(p.get("area", 0) for p in order_pieces)

            suitable_leftovers = []
            total_leftover_area = 0

            for leftover in available_leftovers:
                # Простая оценка пригодности
                leftover_area = leftover.get("area", 0)
                if (
                    leftover_area > 0
                    and leftover.get("material_code")
                    == order_data.get("material_code")
                    and leftover.get("thickness")
                    == order_data.get("thickness", 16.0)
                ):
                    suitable_leftovers.append(leftover)
                    total_leftover_area += leftover_area

            # Использовать остатки если они покрывают >30% площади заказа
            use_leftovers = total_leftover_area >= total_area * 0.3

            return {
                "use_leftovers": use_leftovers,
                "suitable_leftovers": suitable_leftovers,
                "total_area_ratio": (
                    total_leftover_area / total_area if total_area > 0 else 0
                ),
                "estimation_savings": (
                    min(total_leftover_area / total_area, 1.0) * 100
                    if total_area > 0
                    else 0
                ),
                "leftovers_count": len(suitable_leftovers),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing leftovers: {str(e)}")
            return {
                "use_leftovers": False,
                "suitable_leftovers": [],
                "total_area_ratio": 0,
                "estimation_savings": 0,
                "leftovers_count": 0,
            }

    def _apply_ai_enhancements(
        self,
        base_result: Dict,
        order_data: Dict,
        leftovers_analysis: Optional[Dict],
    ) -> Dict[str, Any]:
        """Применение AI-улучшений к базовому результату."""
        try:
            # Проверка качества базовой оптимизации
            utilization_rate = base_result.get("utilization_rate", 0)
            waste_percentage = base_result.get("waste_percentage", 100)

            # AI применяется только если есть возможности для улучшения
            needs_improvement = (
                utilization_rate < 0.85 or waste_percentage > 15
            )

            if not needs_improvement:
                return {
                    "enhancement_applied": False,
                    "corrections": [],
                    "ai_confidence": 0.0,
                    "reason": "No improvement needed",
                }

            # Получение AI-корректировок
            dxf_path = Path(base_result.get("dxf_file", ""))
            if not dxf_path.exists():
                return {
                    "enhancement_applied": False,
                    "corrections": [],
                    "ai_confidence": 0.0,
                    "reason": "DXF file not found",
                }

            # Использование AI API для получения корректировок
            if leftovers_analysis and leftovers_analysis.get("use_leftovers"):
                ai_result = self.ai_api.optimize_with_leftovers(
                    dxf_path, order_data
                )
            else:
                ai_result = self.ai_api.get_corrections(dxf_path, order_data)

            if ai_result["status"] == "success":
                corrections = ai_result.get("corrections", [])
                confidence = ai_result.get("quality_metrics", {}).get(
                    "confidence", 0.0
                )

                # Фильтрация корректировок по уверенности
                high_confidence_corrections = [
                    c for c in corrections if c.get("confidence", 0) > 0.7
                ]

                return {
                    "enhancement_applied": len(high_confidence_corrections)
                    > 0,
                    "corrections": high_confidence_corrections,
                    "ai_confidence": confidence,
                    "total_suggestions": len(corrections),
                    "applied_suggestions": len(high_confidence_corrections),
                }
            else:
                return {
                    "enhancement_applied": False,
                    "corrections": [],
                    "ai_confidence": 0.0,
                    "reason": ai_result.get("error", "AI processing failed"),
                }

        except Exception as e:
            self.logger.error(f"Error applying AI enhancements: {str(e)}")
            return {
                "enhancement_applied": False,
                "corrections": [],
                "ai_confidence": 0.0,
                "reason": f"AI enhancement error: {str(e)}",
            }

    def _optimize_with_leftovers(
        self, order_data: Dict, leftovers: List[Dict]
    ) -> Dict[str, Any]:
        """Оптимизация с использованием остатков."""
        try:
            # Использование AI API для оптимизации с остатками
            dxf_path = Path(order_data.get("dxf_file", ""))
            if dxf_path.exists():
                optimization_result = self.ai_api.optimize_with_leftovers(
                    dxf_path, order_data
                )

                if optimization_result["status"] == "success":
                    # Обновление базы данных остатков
                    new_leftovers = optimization_result.get(
                        "new_leftovers", []
                    )
                    if new_leftovers:
                        self._update_leftovers_database(new_leftovers)

                    return {
                        "status": "success",
                        "optimization_strategy": "with_leftovers",
                        "used_leftovers": optimization_result.get(
                            "assignments", []
                        ),
                        "new_leftovers": new_leftovers,
                        "efficiency_metrics": optimization_result.get(
                            "efficiency_metrics", {}
                        ),
                        "material_savings": optimization_result.get(
                            "efficiency_metrics", {}
                        ).get("material_efficiency", 0)
                        * 100,
                        "was_ai_assisted": True,
                    }

            # Fallback к базовой оптимизации
            return self._perform_base_optimization(order_data)

        except Exception as e:
            self.logger.error(f"Error in leftover optimization: {str(e)}")
            return self._perform_base_optimization(order_data)

    def _apply_correction(
        self, correction: Dict, base_result: Dict
    ) -> Dict[str, Any]:
        """Применение отдельной корректировки."""
        try:
            # В реальной реализации здесь было бы применение корректировки к DXF
            # Для примера - симуляция успешного применения

            correction_type = correction.get("correction_type", "unknown")
            piece_id = correction.get("piece_id", "unknown")
            confidence = correction.get("confidence", 0.0)

            # Создание события корректировки
            correction_event = self._create_correction_event(
                correction, "applied"
            )

            return {
                "status": "success",
                "correction_type": correction_type,
                "piece_id": piece_id,
                "confidence": confidence,
                "corrected_file": base_result.get("dxf_file", ""),
                "event": correction_event,
            }

        except Exception as e:
            self.logger.error(f"Error applying correction: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "correction": correction,
            }

    def collect_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """Сбор обратной связи от пользователей."""
        try:
            if not self.feedback_enabled:
                return "feedback_disabled"

            # Дополнение данных обратной связи
            complete_feedback = {
                "timestamp": datetime.now().isoformat(),
                "ai_enabled": self.ai_enabled,
                "leftovers_enabled": self.leftovers_enabled,
                **feedback_data,
            }

            # Сохранение обратной связи
            feedback_dir = Path("data/feedback")
            feedback_dir.mkdir(parents=True, exist_ok=True)

            feedback_file = (
                feedback_dir
                / f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(feedback_file, "w", encoding="utf-8") as f:
                json.dump(complete_feedback, f, indent=2, ensure_ascii=False)

            # Обновление моделей на основе обратной связи
            self._update_models_from_feedback(complete_feedback)

            # Анализ эффективности
            effectiveness = self._analyze_feedback_effectiveness(
                complete_feedback
            )

            self.logger.info(f"Feedback collected: {effectiveness}")

            return "feedback_saved"

        except Exception as e:
            self.logger.error(f"Error collecting feedback: {str(e)}")
            return "feedback_error"

    def get_ai_effectiveness_metrics(self) -> Dict[str, Any]:
        """Получение метрик эффективности AI."""
        try:
            # Базовая статистика обработки
            base_metrics = {
                "total_jobs": self.processing_stats["total_jobs"],
                "ai_assisted_jobs": self.processing_stats["ai_assisted_jobs"],
                "leftovers_used": self.processing_stats["leftovers_used"],
                "average_processing_time": self.processing_stats[
                    "average_processing_time"
                ],
                "ai_usage_rate": (
                    self.processing_stats["ai_assisted_jobs"]
                    / max(self.processing_stats["total_jobs"], 1)
                ),
            }

            # Анализ обратной связи (если доступна)
            if self.feedback_enabled:
                feedback_dir = Path("data/feedback")
                if feedback_dir.exists():
                    feedback_files = list(feedback_dir.glob("feedback_*.json"))
                    if feedback_files:
                        # Простой анализ последних отзывов
                        recent_feedback = []
                        for file_path in feedback_files[-10:]:  # Последние 10
                            with open(file_path, "r", encoding="utf-8") as f:
                                feedback = json.load(f)
                                recent_feedback.append(feedback)

                        if recent_feedback:
                            satisfaction_ratings = [
                                f.get("satisfaction_rating", 3)
                                for f in recent_feedback
                            ]
                            acceptance_rates = [
                                len(f.get("accepted_corrections", []))
                                / max(
                                    len(f.get("accepted_corrections", []))
                                    + len(f.get("rejected_corrections", [])),
                                    1,
                                )
                                for f in recent_feedback
                            ]

                            base_metrics.update(
                                {
                                    "average_satisfaction": np.mean(
                                        satisfaction_ratings
                                    ),
                                    "average_acceptance_rate": np.mean(
                                        acceptance_rates
                                    ),
                                    "feedback_count": len(recent_feedback),
                                }
                            )

            return base_metrics

        except Exception as e:
            self.logger.error(
                f"Error getting AI effectiveness metrics: {str(e)}"
            )
            return {"error": str(e), "total_jobs": 0, "ai_assisted_jobs": 0}

    def _update_leftovers_database(self, new_leftovers: List[Dict]):
        """Обновление базы данных остатков."""
        try:
            self.ai_api.update_leftovers_db(new_leftovers)
            self.logger.info(
                f"Updated leftovers database with {len(new_leftovers)} new leftovers"
            )
        except Exception as e:
            self.logger.error(f"Error updating leftovers database: {str(e)}")

    def _log_processing_result(self, result: Dict, processing_time: float):
        """Логирование результата обработки."""
        try:
            self.logger.log_processing_step(
                "job_completed",
                {
                    "job_id": result.get("order_id", "unknown"),
                    "processing_time": processing_time,
                    "was_ai_assisted": result.get("was_ai_assisted", False),
                    "corrections_count": len(
                        result.get("applied_corrections", [])
                    ),
                    "ai_confidence": result.get("ai_confidence", 0),
                    "utilization_rate": result.get("utilization_rate", 0),
                    "waste_percentage": result.get("waste_percentage", 0),
                },
            )
        except Exception as e:
            self.logger.error(f"Error logging processing result: {str(e)}")

    def _create_correction_event(
        self, correction: Dict, event_type: str
    ) -> Dict[str, Any]:
        """Создание события корректировки для логирования."""
        return {
            "timestamp": datetime.now().isoformat(),
            "correction_type": correction.get("correction_type"),
            "piece_id": correction.get("piece_id"),
            "confidence": correction.get("confidence"),
            "event_type": event_type,
        }

    def _update_models_from_feedback(self, feedback_data: Dict):
        """Обновление моделей на основе обратной связи."""
        try:
            # Здесь будет логика дообучения моделей
            # Например, сохранение данных для переобучения

            feedback_entry = {
                "timestamp": datetime.now().isoformat(),
                "job_id": feedback_data.get("job_id"),
                "satisfaction": feedback_data.get("satisfaction_rating"),
                "accepted_corrections": feedback_data.get(
                    "accepted_corrections", []
                ),
                "rejected_corrections": feedback_data.get(
                    "rejected_corrections", []
                ),
                "comments": feedback_data.get("comments", ""),
            }

            # Сохраняем для будущего обучения
            training_data_dir = Path("data/training")
            training_data_dir.mkdir(parents=True, exist_ok=True)

            training_file = training_data_dir / "feedback_training_data.jsonl"
            with open(training_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            self.logger.error(f"Error updating models from feedback: {str(e)}")

    def _analyze_feedback_effectiveness(
        self, feedback_data: Dict
    ) -> Dict[str, Any]:
        """Анализ эффективности на основе обратной связи."""
        try:
            # Простой анализ удовлетворенности
            satisfaction = feedback_data.get("satisfaction_rating", 0)
            total_suggestions = len(
                feedback_data.get("accepted_corrections", [])
            ) + len(feedback_data.get("rejected_corrections", []))

            if total_suggestions > 0:
                acceptance_rate = (
                    len(feedback_data.get("accepted_corrections", []))
                    / total_suggestions
                )
            else:
                acceptance_rate = 0

            return {
                "user_satisfaction": satisfaction,
                "suggestion_acceptance_rate": acceptance_rate,
                "total_feedback_entries": total_suggestions,
                "ai_effectiveness_score": (satisfaction / 5)
                * acceptance_rate,  # Условная оценка
            }

        except Exception as e:
            self.logger.error(
                f"Error analyzing feedback effectiveness: {str(e)}"
            )
            return {
                "user_satisfaction": 0,
                "suggestion_acceptance_rate": 0,
                "total_feedback_entries": 0,
                "ai_effectiveness_score": 0,
            }

    def _update_processing_stats(self, processing_time: float, result: Dict):
        """Обновление статистики обработки."""
        try:
            self.processing_stats["total_jobs"] += 1

            if result.get("was_ai_assisted", False):
                self.processing_stats["ai_assisted_jobs"] += 1

            if result.get("leftovers_analysis", {}).get(
                "use_leftovers", False
            ):
                self.processing_stats["leftovers_used"] += 1

            # Обновление среднего времени обработки
            current_avg = self.processing_stats["average_processing_time"]
            total_jobs = self.processing_stats["total_jobs"]

            self.processing_stats["average_processing_time"] = (
                current_avg * (total_jobs - 1) + processing_time
            ) / total_jobs

        except Exception as e:
            self.logger.error(f"Error updating processing stats: {str(e)}")
