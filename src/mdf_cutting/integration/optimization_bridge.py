"""
Мост между традиционным оптимизатором и AI.

Обеспечивает:
- Анализ качества текущей оптимизации
- Определение областей для улучшения
- Генерацию AI-предложений
- Оценку потенциала улучшений
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..ai_module.api.correction_api import CorrectionAPI
from ..ai_module.features.geometry import GeometryFeatureExtractor
from ..ai_module.features.optimization import OptimizationFeatureExtractor


class OptimizationBridge:
    """Мост между традиционным оптимизатором и AI."""

    def __init__(self, ai_api: CorrectionAPI):
        """Инициализация моста оптимизации."""
        self.ai_api = ai_api
        self.geometry_extractor = GeometryFeatureExtractor()
        self.optimization_extractor = OptimizationFeatureExtractor()

        # Пороги для принятия решений
        self.utilization_threshold = 0.8
        self.waste_threshold = 20.0
        self.improvement_threshold = 0.05

    def enhance_optimization(
        self, base_result: Dict[str, Any], order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Улучшение результата оптимизации с помощью AI."""

        try:
            # 1. Анализ текущей оптимизации
            quality_analysis = self._analyze_current_optimization(base_result)

            # 2. Определение областей для улучшения
            improvement_areas = self._identify_improvement_areas(
                quality_analysis
            )

            # 3. Генерация AI-предложений
            ai_suggestions = self._generate_ai_suggestions(
                base_result, order_data, improvement_areas
            )

            # 4. Оценка потенциала улучшений
            improvement_potential = self._estimate_improvement_potential(
                ai_suggestions, base_result
            )

            return {
                "quality_analysis": quality_analysis,
                "improvement_areas": improvement_areas,
                "ai_suggestions": ai_suggestions,
                "improvement_potential": improvement_potential,
                "enhancement_recommended": improvement_potential["overall"]
                > self.improvement_threshold,
            }

        except Exception as e:
            return {
                "quality_analysis": {},
                "improvement_areas": [],
                "ai_suggestions": [],
                "improvement_potential": {"overall": 0.0, "by_area": {}},
                "enhancement_recommended": False,
                "error": str(e),
            }

    def _analyze_current_optimization(
        self, base_result: Dict
    ) -> Dict[str, Any]:
        """Анализ качества текущей оптимизации."""
        try:
            dxf_data = base_result.get("dxf_data", {})
            metrics = base_result.get("current_metrics", {})

            # Извлечение признаков для анализа
            geometry_features = self.geometry_extractor.extract_features(
                dxf_data
            )
            optimization_features = (
                self.optimization_extractor.extract_features(dxf_data)
            )

            # Расчет дополнительных метрик
            utilization_rate = metrics.get("utilization_rate", 0)
            waste_percentage = metrics.get("waste_percentage", 0)
            total_pieces = metrics.get("total_pieces", 0)

            # Анализ геометрических характеристик
            geometric_analysis = {
                "average_piece_area": geometry_features.get(
                    "average_piece_area", 0
                ),
                "piece_size_variance": geometry_features.get(
                    "piece_size_variance", 0
                ),
                "placement_density": geometry_features.get(
                    "placement_density", 0
                ),
                "edge_utilization": geometry_features.get(
                    "edge_utilization", 0
                ),
            }

            # Анализ оптимизационных характеристик
            optimization_analysis = {
                "material_efficiency": optimization_features.get(
                    "material_efficiency", 0
                ),
                "cutting_efficiency": optimization_features.get(
                    "cutting_efficiency", 0
                ),
                "waste_distribution": optimization_features.get(
                    "waste_distribution", 0
                ),
            }

            return {
                "utilization_rate": utilization_rate,
                "waste_percentage": waste_percentage,
                "total_pieces": total_pieces,
                "optimization_score": self._calculate_optimization_score(
                    metrics
                ),
                "geometric_analysis": geometric_analysis,
                "optimization_analysis": optimization_analysis,
                "potential_issues": self._identify_potential_issues(
                    dxf_data, geometry_features
                ),
            }

        except Exception as e:
            return {
                "utilization_rate": 0,
                "waste_percentage": 100,
                "total_pieces": 0,
                "optimization_score": 0,
                "potential_issues": [],
                "error": str(e),
            }

    def _identify_improvement_areas(
        self, analysis: Dict
    ) -> List[Dict[str, Any]]:
        """Определение областей для улучшения."""
        improvements = []

        try:
            # 1. Низкая утилизация материала
            utilization_rate = analysis.get("utilization_rate", 0)
            if utilization_rate < self.utilization_threshold:
                improvements.append(
                    {
                        "area": "material_utilization",
                        "priority": "high",
                        "current_value": utilization_rate,
                        "target_value": 0.9,
                        "potential_improvement": 0.9 - utilization_rate,
                        "description": f"Утилизация материала {utilization_rate:.1%} ниже порога {self.utilization_threshold:.1%}",
                    }
                )

            # 2. Много отходов
            waste_percentage = analysis.get("waste_percentage", 0)
            if waste_percentage > self.waste_threshold:
                improvements.append(
                    {
                        "area": "waste_reduction",
                        "priority": "high",
                        "current_value": waste_percentage,
                        "target_value": 10,
                        "potential_improvement": (waste_percentage - 10) / 100,
                        "description": f"Процент отходов {waste_percentage:.1f}% превышает порог {self.waste_threshold}%",
                    }
                )

            # 3. Плотность размещения
            potential_issues = analysis.get("potential_issues", [])
            if len(potential_issues) > 0:
                improvements.append(
                    {
                        "area": "placement_density",
                        "priority": "medium",
                        "current_issues": len(potential_issues),
                        "target_issues": 0,
                        "potential_improvement": len(potential_issues) * 0.1,
                        "description": f"Обнаружено {len(potential_issues)} проблем с размещением деталей",
                    }
                )

            # 4. Геометрические проблемы
            geometric_analysis = analysis.get("geometric_analysis", {})
            placement_density = geometric_analysis.get("placement_density", 0)
            if placement_density < 0.7:
                improvements.append(
                    {
                        "area": "geometric_optimization",
                        "priority": "medium",
                        "current_value": placement_density,
                        "target_value": 0.8,
                        "potential_improvement": 0.8 - placement_density,
                        "description": f"Плотность размещения {placement_density:.1%} ниже оптимальной",
                    }
                )

            # 5. Эффективность резки
            optimization_analysis = analysis.get("optimization_analysis", {})
            cutting_efficiency = optimization_analysis.get(
                "cutting_efficiency", 0
            )
            if cutting_efficiency < 0.8:
                improvements.append(
                    {
                        "area": "cutting_optimization",
                        "priority": "medium",
                        "current_value": cutting_efficiency,
                        "target_value": 0.9,
                        "potential_improvement": 0.9 - cutting_efficiency,
                        "description": f"Эффективность резки {cutting_efficiency:.1%} ниже оптимальной",
                    }
                )

        except Exception as e:
            improvements.append(
                {
                    "area": "error_analysis",
                    "priority": "low",
                    "description": f"Ошибка анализа: {str(e)}",
                    "potential_improvement": 0,
                }
            )

        return improvements

    def _generate_ai_suggestions(
        self,
        base_result: Dict,
        order_data: Dict,
        improvement_areas: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Генерация предложений от AI для каждой области улучшения."""
        suggestions = []

        try:
            for area in improvement_areas:
                area_type = area["area"]

                if area_type == "material_utilization":
                    suggestion = self._suggest_utilization_improvement(
                        base_result, order_data
                    )
                elif area_type == "waste_reduction":
                    suggestion = self._suggest_waste_reduction(
                        base_result, order_data
                    )
                elif area_type == "placement_density":
                    suggestion = self._suggest_placement_improvement(
                        base_result, order_data
                    )
                elif area_type == "geometric_optimization":
                    suggestion = self._suggest_geometric_optimization(
                        base_result, order_data
                    )
                elif area_type == "cutting_optimization":
                    suggestion = self._suggest_cutting_optimization(
                        base_result, order_data
                    )
                else:
                    continue

                if suggestion:
                    suggestions.append(
                        {
                            **suggestion,
                            "priority": area["priority"],
                            "potential_improvement": area[
                                "potential_improvement"
                            ],
                            "area_type": area_type,
                        }
                    )

        except Exception as e:
            suggestions.append(
                {
                    "type": "error",
                    "description": f"Ошибка генерации предложений: {str(e)}",
                    "priority": "low",
                    "potential_improvement": 0,
                }
            )

        return suggestions

    def _suggest_utilization_improvement(
        self, base_result: Dict, order_data: Dict
    ) -> Optional[Dict]:
        """Предложение по улучшению утилизации материала."""
        try:
            # Получаем AI-рекомендации
            dxf_path = base_result.get("dxf_file")
            if not dxf_path or not Path(dxf_path).exists():
                return None

            ai_result = self.ai_api.get_corrections(Path(dxf_path), order_data)

            if ai_result["status"] == "success":
                return {
                    "type": "utilization_optimization",
                    "description": "AI предлагает перестроить расположение деталей для улучшения утилизации материала",
                    "corrections": ai_result.get("corrections", []),
                    "expected_improvement": ai_result.get(
                        "quality_metrics", {}
                    ).get("improvement_potential", 0.1),
                    "confidence": ai_result.get("model_info", {}).get(
                        "confidence", 0.0
                    ),
                    "suggested_actions": ["reposition", "rotate", "compact"],
                }

            return None

        except Exception as e:
            return {
                "type": "utilization_optimization",
                "description": f"Ошибка получения AI-рекомендаций: {str(e)}",
                "expected_improvement": 0.05,
                "confidence": 0.0,
            }

    def _suggest_waste_reduction(
        self, base_result: Dict, order_data: Dict
    ) -> Optional[Dict]:
        """Предложение по сокращению отходов."""
        try:
            # Анализ текущих отходов
            waste_analysis = self._analyze_waste_patterns(base_result)

            if waste_analysis["reducible_waste"] > 0.05:  # >5%
                return {
                    "type": "waste_reduction",
                    "description": "Обнаружена возможность реорганизации деталей для сокращения отходов",
                    "waste_areas": waste_analysis["waste_areas"],
                    "expected_reduction": waste_analysis["reducible_waste"],
                    "suggested_strategy": "rearrange_pieces",
                    "confidence": 0.8,
                }

            return None

        except Exception as e:
            return {
                "type": "waste_reduction",
                "description": f"Ошибка анализа отходов: {str(e)}",
                "expected_reduction": 0.02,
                "confidence": 0.0,
            }

    def _suggest_placement_improvement(
        self, base_result: Dict, order_data: Dict
    ) -> Optional[Dict]:
        """Предложение по улучшению размещения деталей."""
        try:
            issues = base_result.get("quality_analysis", {}).get(
                "potential_issues", []
            )

            if not issues:
                return None

            return {
                "type": "placement_optimization",
                "description": f"AI предлагает исправить {len(issues)} проблем при размещении деталей",
                "issues_to_fix": issues,
                "expected_improvement": len(issues) * 0.05,
                "suggested_actions": ["reposition", "rotate", "resize"],
                "confidence": 0.7,
            }

        except Exception as e:
            return {
                "type": "placement_optimization",
                "description": f"Ошибка анализа размещения: {str(e)}",
                "expected_improvement": 0.03,
                "confidence": 0.0,
            }

    def _suggest_geometric_optimization(
        self, base_result: Dict, order_data: Dict
    ) -> Optional[Dict]:
        """Предложение по геометрической оптимизации."""
        try:
            geometric_analysis = base_result.get("quality_analysis", {}).get(
                "geometric_analysis", {}
            )
            placement_density = geometric_analysis.get("placement_density", 0)

            if placement_density < 0.7:
                return {
                    "type": "geometric_optimization",
                    "description": "Предлагается оптимизация геометрического расположения деталей",
                    "current_density": placement_density,
                    "target_density": 0.8,
                    "expected_improvement": 0.8 - placement_density,
                    "suggested_actions": [
                        "compact_layout",
                        "optimize_spacing",
                    ],
                    "confidence": 0.75,
                }

            return None

        except Exception as e:
            return {
                "type": "geometric_optimization",
                "description": f"Ошибка геометрической оптимизации: {str(e)}",
                "expected_improvement": 0.02,
                "confidence": 0.0,
            }

    def _suggest_cutting_optimization(
        self, base_result: Dict, order_data: Dict
    ) -> Optional[Dict]:
        """Предложение по оптимизации резки."""
        try:
            optimization_analysis = base_result.get(
                "quality_analysis", {}
            ).get("optimization_analysis", {})
            cutting_efficiency = optimization_analysis.get(
                "cutting_efficiency", 0
            )

            if cutting_efficiency < 0.8:
                return {
                    "type": "cutting_optimization",
                    "description": "Предлагается оптимизация стратегии резки для повышения эффективности",
                    "current_efficiency": cutting_efficiency,
                    "target_efficiency": 0.9,
                    "expected_improvement": 0.9 - cutting_efficiency,
                    "suggested_actions": ["optimize_cut_path", "reduce_cuts"],
                    "confidence": 0.7,
                }

            return None

        except Exception as e:
            return {
                "type": "cutting_optimization",
                "description": f"Ошибка оптимизации резки: {str(e)}",
                "expected_improvement": 0.02,
                "confidence": 0.0,
            }

    def _calculate_optimization_score(self, metrics: Dict) -> float:
        """Расчет единой оценки качества оптимизации."""
        try:
            utilization = metrics.get("utilization_rate", 0)
            waste = metrics.get("waste_percentage", 100)

            # Комбинированная оценка (0-1)
            utilization_score = utilization
            waste_score = max(0, (100 - waste) / 100)

            return (utilization_score + waste_score) / 2

        except Exception:
            return 0.0

    def _identify_potential_issues(
        self, dxf_data: Dict, geometry_features: Dict
    ) -> List[str]:
        """Идентификация потенциальных проблем в оптимизации."""
        issues = []

        try:
            # Простая эвристика для выявления проблем
            entities = dxf_data.get("entities", [])

            # Проверка на перекрытия (упрощенная)
            if len(entities) > 10:  # Если много деталей
                issues.append("potential_overlaps")

            # Проверка плотности размещения
            placement_density = geometry_features.get("placement_density", 0)
            if placement_density < 0.6:
                issues.append("low_placement_density")

            # Проверка утилизации краев
            edge_utilization = geometry_features.get("edge_utilization", 0)
            if edge_utilization < 0.7:
                issues.append("poor_edge_utilization")

            # Проверка размера деталей
            average_piece_area = geometry_features.get("average_piece_area", 0)
            if average_piece_area > 50000:  # > 0.5м²
                issues.append("large_pieces_present")

        except Exception:
            issues.append("analysis_error")

        return issues

    def _analyze_waste_patterns(self, base_result: Dict) -> Dict[str, Any]:
        """Анализ паттернов отходов."""
        try:
            # Упрощенный анализ
            metrics = base_result.get("current_metrics", {})
            waste_percentage = metrics.get("waste_percentage", 0)

            return {
                "total_waste": waste_percentage,
                "reducible_waste": min(
                    waste_percentage * 0.5, waste_percentage - 5
                ),  # Условно
                "waste_areas": ["center_area", "edge_areas"],  # Упрощенно
                "optimization_potential": waste_percentage > 15,
            }

        except Exception:
            return {
                "total_waste": 0,
                "reducible_waste": 0,
                "waste_areas": [],
                "optimization_potential": False,
            }

    def _estimate_improvement_potential(
        self, suggestions: List[Dict], base_result: Dict
    ) -> Dict[str, float]:
        """Оценка общего потенциала улучшения."""
        try:
            if not suggestions:
                return {"overall": 0.0, "by_area": {}}

            by_area = {}
            total_potential = 0

            for suggestion in suggestions:
                improvement = suggestion.get("expected_improvement", 0)
                area = suggestion["type"]
                by_area[area] = improvement
                total_potential += improvement

            return {
                "overall": min(total_potential, 1.0),  # Ограничиваем сверху
                "by_area": by_area,
                "suggestions_count": len(suggestions),
            }

        except Exception:
            return {"overall": 0.0, "by_area": {}, "suggestions_count": 0}
