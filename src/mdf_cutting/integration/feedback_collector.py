"""
Система сбора и анализа обратной связи от пользователей.

Обеспечивает:
- Сбор обратной связи по AI-предложениям
- Анализ эффективности AI
- Статистику принятия предложений
- Тренды удовлетворенности пользователей
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config.loader import ConfigLoader


class FeedbackCollector:
    """Сбор и анализ обратной связи от пользователей."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """Инициализация системы сбора обратной связи."""
        self.config_loader = config_loader or ConfigLoader()
        self.config_loader.load_all()

        # Директория для хранения данных обратной связи
        self.feedback_dir = Path("data/feedback")
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

        # Конфигурация
        config = self.config_loader._configs.get("optimization_rules", {})
        self.feedback_enabled = config.get("feedback_enabled", True)
        self.auto_analysis_enabled = config.get("auto_analysis_enabled", True)

        # Кэш для быстрого доступа к статистике
        self._stats_cache = {}
        self._cache_expiry = None

    def collect_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """Сбор обратной связи."""
        try:
            if not self.feedback_enabled:
                return "feedback_disabled"

            # Генерация уникального ID для обратной связи
            feedback_id = str(uuid.uuid4())

            # Дополнение данных обратной связи
            complete_feedback = {
                "feedback_id": feedback_id,
                "timestamp": datetime.now().isoformat(),
                "ai_enabled": True,  # Предполагаем, что AI был использован
                "feedback_version": "1.0",
                **feedback_data,
            }

            # Валидация данных обратной связи
            validation_result = self._validate_feedback_data(complete_feedback)
            if not validation_result["is_valid"]:
                return f"validation_failed: {validation_result['reason']}"

            # Сохранение в файл
            feedback_file = self.feedback_dir / f"feedback_{feedback_id}.json"
            with open(feedback_file, "w", encoding="utf-8") as f:
                json.dump(complete_feedback, f, indent=2, ensure_ascii=False)

            # Обновление сводной статистики
            self._update_feedback_summary(complete_feedback)

            # Автоматический анализ эффективности
            if self.auto_analysis_enabled:
                effectiveness = self._analyze_feedback_effectiveness(
                    complete_feedback
                )
                complete_feedback["effectiveness_analysis"] = effectiveness

            # Сброс кэша статистики
            self._invalidate_cache()

            return feedback_id

        except Exception as e:
            return f"feedback_error: {str(e)}"

    def get_feedback_summary(self, days: int = 30) -> Dict[str, Any]:
        """Получение сводки по обратной связи за N дней."""
        try:
            # Проверка кэша
            cache_key = f"summary_{days}"
            if self._is_cache_valid() and cache_key in self._stats_cache:
                return self._stats_cache[cache_key]

            summary_file = self.feedback_dir / "summary.json"

            if summary_file.exists():
                with open(summary_file, "r", encoding="utf-8") as f:
                    summary = json.load(f)
            else:
                summary = self._generate_feedback_summary(days)

            # Кэширование результата
            if self._is_cache_valid():
                self._stats_cache[cache_key] = summary

            return summary

        except Exception as e:
            return {
                "error": str(e),
                "period_days": days,
                "total_feedback_entries": 0,
            }

    def get_ai_effectiveness_metrics(self) -> Dict[str, Any]:
        """Расчет метрик эффективности AI."""
        try:
            summary = self.get_feedback_summary()

            if not summary or "error" in summary:
                return {
                    "total_sessions": 0,
                    "average_satisfaction": 0,
                    "suggestion_acceptance_rate": 0,
                    "effective_suggestions_count": 0,
                    "ai_effectiveness_score": 0,
                }

            # Базовые метрики
            total_sessions = summary.get("total_feedback_entries", 0)
            average_satisfaction = summary.get("average_satisfaction", 0)
            acceptance_rate = summary.get("average_acceptance_rate", 0)

            # Расчет эффективности
            effectiveness_score = self._calculate_effectiveness_score(
                average_satisfaction, acceptance_rate, total_sessions
            )

            return {
                "total_sessions": total_sessions,
                "average_satisfaction": average_satisfaction,
                "suggestion_acceptance_rate": acceptance_rate,
                "effective_suggestions_count": summary.get(
                    "effective_suggestions_count", 0
                ),
                "ai_effectiveness_score": effectiveness_score,
                "improvement_trend": summary.get(
                    "satisfaction_trend", "stable"
                ),
                "recent_performance": self._get_recent_performance_metrics(),
            }

        except Exception as e:
            return {
                "error": str(e),
                "total_sessions": 0,
                "average_satisfaction": 0,
                "suggestion_acceptance_rate": 0,
                "effective_suggestions_count": 0,
                "ai_effectiveness_score": 0,
            }

    def get_feedback_trends(self, days: int = 30) -> Dict[str, Any]:
        """Анализ трендов обратной связи."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            feedback_files = list(self.feedback_dir.glob("feedback_*.json"))
            relevant_feedback = []

            for file_path in feedback_files:
                with open(file_path, "r", encoding="utf-8") as f:
                    feedback = json.load(f)

                    feedback_time = datetime.fromisoformat(
                        feedback["timestamp"]
                    )
                    if feedback_time >= cutoff_date:
                        relevant_feedback.append(feedback)

            if not relevant_feedback:
                return {"period_days": days, "trends": {}, "insights": []}

            # Анализ трендов
            trends = self._analyze_feedback_trends(relevant_feedback)
            insights = self._generate_feedback_insights(relevant_feedback)

            return {
                "period_days": days,
                "total_entries": len(relevant_feedback),
                "trends": trends,
                "insights": insights,
            }

        except Exception as e:
            return {
                "error": str(e),
                "period_days": days,
                "trends": {},
                "insights": [],
            }

    def _validate_feedback_data(self, feedback_data: Dict) -> Dict[str, Any]:
        """Валидация данных обратной связи."""
        validation_result = {"is_valid": True, "reason": None, "warnings": []}

        try:
            # Проверка обязательных полей
            required_fields = ["job_id", "satisfaction_rating"]
            for field in required_fields:
                if field not in feedback_data:
                    validation_result["is_valid"] = False
                    validation_result["reason"] = (
                        f"Missing required field: {field}"
                    )
                    return validation_result

            # Проверка рейтинга удовлетворенности
            satisfaction = feedback_data.get("satisfaction_rating", 0)
            if (
                not isinstance(satisfaction, (int, float))
                or satisfaction < 1
                or satisfaction > 5
            ):
                validation_result["is_valid"] = False
                validation_result["reason"] = (
                    "Invalid satisfaction rating (must be 1-5)"
                )
                return validation_result

            # Проверка корректировок
            accepted = feedback_data.get("accepted_corrections", [])
            rejected = feedback_data.get("rejected_corrections", [])

            if not isinstance(accepted, list) or not isinstance(
                rejected, list
            ):
                validation_result["warnings"].append(
                    "Invalid corrections format"
                )

            # Проверка комментариев
            comments = feedback_data.get("comments", "")
            if comments and len(comments) > 1000:
                validation_result["warnings"].append("Comments too long")

        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["reason"] = f"Validation error: {str(e)}"

        return validation_result

    def _update_feedback_summary(self, feedback: Dict):
        """Обновление сводной статистики обратной связи."""
        try:
            summary_file = self.feedback_dir / "summary.json"

            # Загрузка существующей сводки или создание новой
            if summary_file.exists():
                with open(summary_file, "r", encoding="utf-8") as f:
                    summary = json.load(f)
            else:
                summary = {
                    "total_feedback_entries": 0,
                    "total_satisfaction": 0,
                    "average_satisfaction": 0,
                    "accepted_suggestions": 0,
                    "rejected_suggestions": 0,
                    "average_acceptance_rate": 0,
                    "feedback_history": [],
                    "satisfaction_trend": "stable",
                    "last_updated": datetime.now().isoformat(),
                }

            # Обновление статистики
            satisfaction = feedback.get("satisfaction_rating", 3)
            accepted = len(feedback.get("accepted_corrections", []))
            rejected = len(feedback.get("rejected_corrections", []))
            total_suggestions = accepted + rejected

            summary["total_feedback_entries"] += 1
            summary["total_satisfaction"] += satisfaction
            summary["average_satisfaction"] = (
                summary["total_satisfaction"]
                / summary["total_feedback_entries"]
            )
            summary["accepted_suggestions"] += accepted
            summary["rejected_suggestions"] += rejected

            if total_suggestions > 0:
                session_acceptance = accepted / total_suggestions
                total_sessions = summary.get("total_feedback_entries", 1)
                current_rate = summary.get("average_acceptance_rate", 0)
                summary["average_acceptance_rate"] = (
                    current_rate * (total_sessions - 1) + session_acceptance
                ) / total_sessions

            # Анализ тенденций
            if len(summary.get("feedback_history", [])) >= 10:
                recent_trend = self._analyze_satisfaction_trend(
                    summary["feedback_history"][-10:], satisfaction
                )
                summary["satisfaction_trend"] = recent_trend

            summary["feedback_history"].append(
                {
                    "timestamp": feedback["timestamp"],
                    "satisfaction": satisfaction,
                    "acceptance_rate": (
                        accepted / total_suggestions
                        if total_suggestions > 0
                        else 0
                    ),
                }
            )

            summary["last_updated"] = datetime.now().isoformat()

            # Сохранение обновленной сводки
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error updating feedback summary: {e}")

    def _generate_feedback_summary(self, days: int) -> Dict[str, Any]:
        """Генерация сводки по обратной связи за N дней."""
        try:
            # Сбор всех файлов обратной связи за указанный период
            cutoff_date = datetime.now() - timedelta(days=days)

            feedback_files = list(self.feedback_dir.glob("feedback_*.json"))
            relevant_feedback = []

            for file_path in feedback_files:
                with open(file_path, "r", encoding="utf-8") as f:
                    feedback = json.load(f)

                    feedback_time = datetime.fromisoformat(
                        feedback["timestamp"]
                    )
                    if feedback_time >= cutoff_date:
                        relevant_feedback.append(feedback)

            if not relevant_feedback:
                return {}

            # Расчет статистики
            total_satisfaction = sum(
                f.get("satisfaction_rating", 3) for f in relevant_feedback
            )
            total_accepted = sum(
                len(f.get("accepted_corrections", []))
                for f in relevant_feedback
            )
            total_rejected = sum(
                len(f.get("rejected_corrections", []))
                for f in relevant_feedback
            )
            total_suggestions = total_accepted + total_rejected

            return {
                "period_days": days,
                "total_feedback_entries": len(relevant_feedback),
                "average_satisfaction": total_satisfaction
                / len(relevant_feedback),
                "total_accepted": total_accepted,
                "total_rejected": total_rejected,
                "average_acceptance_rate": (
                    total_accepted / total_suggestions
                    if total_suggestions > 0
                    else 0
                ),
                "feedback_ids": [f["feedback_id"] for f in relevant_feedback],
            }

        except Exception as e:
            return {"error": str(e)}

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
            return {
                "user_satisfaction": 0,
                "suggestion_acceptance_rate": 0,
                "total_feedback_entries": 0,
                "ai_effectiveness_score": 0,
                "error": str(e),
            }

    def _analyze_satisfaction_trend(
        self, history: List[Dict], current_satisfaction: float
    ) -> str:
        """Анализ тенденции удовлетворенности."""
        if len(history) < 5:
            return "stable"

        recent_avg = sum(h["satisfaction"] for h in history[-5:]) / 5

        if current_satisfaction > recent_avg + 0.5:
            return "improving"
        elif current_satisfaction < recent_avg - 0.5:
            return "declining"
        else:
            return "stable"

    def _calculate_effectiveness_score(
        self, satisfaction: float, acceptance_rate: float, total_sessions: int
    ) -> float:
        """Расчет общей оценки эффективности AI."""
        try:
            # Базовый скор на основе удовлетворенности и принятия предложений
            base_score = (satisfaction / 5) * acceptance_rate

            # Бонус за количество сессий (больше данных = более надежная оценка)
            session_bonus = min(total_sessions / 100, 0.1)

            return min(base_score + session_bonus, 1.0)

        except Exception:
            return 0.0

    def _get_recent_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик последней производительности."""
        try:
            # Анализ последних 7 дней
            recent_summary = self.get_feedback_summary(7)

            if "error" in recent_summary:
                return {}

            return {
                "recent_satisfaction": recent_summary.get(
                    "average_satisfaction", 0
                ),
                "recent_acceptance_rate": recent_summary.get(
                    "average_acceptance_rate", 0
                ),
                "recent_entries": recent_summary.get(
                    "total_feedback_entries", 0
                ),
            }

        except Exception:
            return {}

    def _analyze_feedback_trends(
        self, feedback_list: List[Dict]
    ) -> Dict[str, Any]:
        """Анализ трендов в обратной связи."""
        try:
            if not feedback_list:
                return {}

            # Тренд удовлетворенности
            satisfaction_trend = self._calculate_trend(
                [f.get("satisfaction_rating", 3) for f in feedback_list]
            )

            # Тренд принятия предложений
            acceptance_rates = []
            for f in feedback_list:
                accepted = len(f.get("accepted_corrections", []))
                total = accepted + len(f.get("rejected_corrections", []))
                if total > 0:
                    acceptance_rates.append(accepted / total)

            acceptance_trend = (
                self._calculate_trend(acceptance_rates)
                if acceptance_rates
                else "stable"
            )

            return {
                "satisfaction_trend": satisfaction_trend,
                "acceptance_trend": acceptance_trend,
                "total_entries": len(feedback_list),
            }

        except Exception:
            return {}

    def _calculate_trend(self, values: List[float]) -> str:
        """Расчет тренда для списка значений."""
        if len(values) < 3:
            return "stable"

        # Простой анализ тренда
        first_half = values[: len(values) // 2]
        second_half = values[len(values) // 2 :]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        if second_avg > first_avg + 0.3:
            return "improving"
        elif second_avg < first_avg - 0.3:
            return "declining"
        else:
            return "stable"

    def _generate_feedback_insights(
        self, feedback_list: List[Dict]
    ) -> List[str]:
        """Генерация инсайтов на основе обратной связи."""
        insights = []

        try:
            if not feedback_list:
                return ["Недостаточно данных для анализа"]

            # Анализ удовлетворенности
            satisfaction_scores = [
                f.get("satisfaction_rating", 3) for f in feedback_list
            ]
            avg_satisfaction = sum(satisfaction_scores) / len(
                satisfaction_scores
            )

            if avg_satisfaction < 3.0:
                insights.append("Низкая общая удовлетворенность пользователей")
            elif avg_satisfaction > 4.0:
                insights.append("Высокая удовлетворенность пользователей")

            # Анализ принятия предложений
            total_accepted = sum(
                len(f.get("accepted_corrections", [])) for f in feedback_list
            )
            total_rejected = sum(
                len(f.get("rejected_corrections", [])) for f in feedback_list
            )
            total_suggestions = total_accepted + total_rejected

            if total_suggestions > 0:
                acceptance_rate = total_accepted / total_suggestions
                if acceptance_rate < 0.5:
                    insights.append("Низкий процент принятия AI-предложений")
                elif acceptance_rate > 0.8:
                    insights.append("Высокий процент принятия AI-предложений")

            # Анализ комментариев
            comments = [
                f.get("comments", "")
                for f in feedback_list
                if f.get("comments")
            ]
            if comments:
                insights.append(f"Получено {len(comments)} текстовых отзывов")

        except Exception:
            insights.append("Ошибка при анализе инсайтов")

        return insights

    def _invalidate_cache(self):
        """Сброс кэша статистики."""
        self._stats_cache = {}
        self._cache_expiry = None

    def _is_cache_valid(self) -> bool:
        """Проверка валидности кэша."""
        if self._cache_expiry is None:
            return False
        return datetime.now() < self._cache_expiry
