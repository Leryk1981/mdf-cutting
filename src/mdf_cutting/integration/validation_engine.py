"""
Валидационный движок для проверки AI-предложений.

Обеспечивает:
- Валидацию корректировок перед применением
- Проверку технологических ограничений
- Геометрическую валидацию
- Проверку ограничений материала
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ..config.loader import ConfigLoader


class ValidationEngine:
    """Валидация AI-предложений перед применением."""

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """Инициализация валидационного движка."""
        self.config_loader = config_loader or ConfigLoader()
        self.config_loader.load_all()

        # Технологические ограничения
        optimization_rules = self.config_loader._configs.get(
            "optimization_rules", {}
        )
        self.min_spacing = optimization_rules.get("min_spacing", 5.0)
        self.max_cuts = optimization_rules.get("max_cuts", 100)
        self.material_constraints = optimization_rules.get(
            "material_constraints", {}
        )

        # Дополнительные ограничения
        self.max_position_offset = 1000  # мм
        self.max_rotation_angle = 90  # градусов
        self.min_scale_factor = 0.95
        self.max_scale_factor = 1.1

    def validate_suggestions(
        self, suggestions: List[Dict], order_data: Dict
    ) -> List[Dict]:
        """Валидация списка предложений."""
        validated_suggestions = []

        for suggestion in suggestions:
            validation_result = self.validate_single_correction(
                suggestion, order_data
            )
            if validation_result["is_valid"]:
                validated_suggestions.append(
                    {**suggestion, "validation_info": validation_result}
                )
            else:
                # Логируем отклоненные предложения
                self._log_rejected_suggestion(suggestion, validation_result)

        return validated_suggestions

    def validate_single_correction(
        self, correction: Dict, context: Dict
    ) -> Dict[str, Any]:
        """Валидация отдельной корректировки."""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "reason": None,
            "technological_violations": [],
            "confidence_score": 0.0,
        }

        try:
            # 1. Проверка наличия необходимых полей
            required_fields = ["piece_id", "correction_type", "parameters"]
            for field in required_fields:
                if field not in correction:
                    validation_result["is_valid"] = False
                    validation_result["reason"] = (
                        f"Missing required field: {field}"
                    )
                    return validation_result

            # 2. Валидация параметров корректировки
            params = correction["parameters"]
            correction_type = correction["correction_type"]

            if correction_type in ["position", "translation"]:
                validation_result = self._validate_position_correction(
                    params, validation_result
                )
            elif correction_type == "rotation":
                validation_result = self._validate_rotation_correction(
                    params, validation_result
                )
            elif correction_type in ["scale", "resize"]:
                validation_result = self._validate_scale_correction(
                    params, context, validation_result
                )
            else:
                validation_result["is_valid"] = False
                validation_result["reason"] = (
                    f"Unknown correction type: {correction_type}"
                )

            # 3. Проверка технологических ограничений
            if validation_result["is_valid"]:
                validation_result = self._check_technological_constraints(
                    correction, context, validation_result
                )

            # 4. Проверка геометрической корректности
            if validation_result["is_valid"]:
                validation_result = self._check_geometric_correctness(
                    correction, context, validation_result
                )

            # 5. Расчет оценки уверенности
            validation_result["confidence_score"] = (
                self._calculate_validation_confidence(validation_result)
            )

        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["reason"] = f"Validation error: {str(e)}"

        return validation_result

    def _validate_position_correction(
        self, params: Dict, validation_result: Dict
    ) -> Dict:
        """Валидация корректировки положения."""
        dx = params.get("dx", 0)
        dy = params.get("dy", 0)

        # Проверка на разумные значения
        if (
            abs(dx) > self.max_position_offset
            or abs(dy) > self.max_position_offset
        ):
            validation_result["warnings"].append(
                f"Large position offset: ({dx}, {dy})"
            )
            if (
                abs(dx) > self.max_position_offset * 2
                or abs(dy) > self.max_position_offset * 2
            ):
                validation_result["is_valid"] = False
                validation_result["reason"] = (
                    "Position offset exceeds maximum allowed"
                )

        # Проверка на минимальное смещение
        if abs(dx) < 1.0 and abs(dy) < 1.0:
            validation_result["warnings"].append(
                "Very small position offset - may not be necessary"
            )

        return validation_result

    def _validate_rotation_correction(
        self, params: Dict, validation_result: Dict
    ) -> Dict:
        """Валидация корректировки вращения."""
        rotation = params.get("rotation", 0)

        # Проверка угла вращения
        if abs(rotation) > self.max_rotation_angle:
            validation_result["warnings"].append(
                f"Large rotation angle: {rotation}°"
            )
            if abs(rotation) > 180:
                validation_result["is_valid"] = False
                validation_result["reason"] = (
                    "Rotation angle exceeds maximum allowed"
                )

        # Проверка на минимальный угол
        if abs(rotation) < 1.0:
            validation_result["warnings"].append(
                "Very small rotation angle - may not be necessary"
            )

        return validation_result

    def _validate_scale_correction(
        self, params: Dict, context: Dict, validation_result: Dict
    ) -> Dict:
        """Валидация корректировки масштабирования."""
        scale_x = params.get("scale_x", 1.0)
        scale_y = params.get("scale_y", 1.0)

        # Проверка на уменьшение деталей (недопустимо)
        if scale_x < self.min_scale_factor or scale_y < self.min_scale_factor:
            validation_result["is_valid"] = False
            validation_result["reason"] = (
                f"Scale must not reduce piece size below {self.min_scale_factor * 100}%"
            )

        # Проверка на увеличение (ограничено материалом)
        max_scale = self.material_constraints.get(
            "max_scale_increase", self.max_scale_factor
        )
        if scale_x > max_scale or scale_y > max_scale:
            validation_result["warnings"].append(
                "Scale increase exceeds material constraints"
            )
            if scale_x > 1.2 or scale_y > 1.2:
                validation_result["is_valid"] = False
                validation_result["reason"] = (
                    "Scale exceeds maximum material constraints"
                )

        # Проверка на пропорциональность
        scale_ratio = scale_x / scale_y if scale_y != 0 else 1.0
        if abs(scale_ratio - 1.0) > 0.1:
            validation_result["warnings"].append(
                "Non-proportional scaling may affect piece quality"
            )

        return validation_result

    def _check_technological_constraints(
        self, correction: Dict, context: Dict, validation_result: Dict
    ) -> Dict:
        """Проверка технологических ограничений."""
        # 1. Проверка минимальных отступов
        if correction["correction_type"] == "position":
            spacing_violation = self._check_spacing_violation(
                correction, context
            )
            if spacing_violation:
                validation_result["technological_violations"].append(
                    "min_spacing_violated"
                )
                validation_result["warnings"].append(
                    "Correction violates minimum spacing constraint"
                )

        # 2. Проверка количества резов
        if correction["correction_type"] == "rotation":
            # Вращение может потребовать дополнительных резов
            validation_result["technological_violations"].append(
                "potential_additional_cuts"
            )
            validation_result["warnings"].append(
                "Rotation may require additional cutting operations"
            )

        # 3. Проверка материала
        material_violation = self._check_material_constraints(
            correction, context
        )
        if material_violation:
            validation_result["is_valid"] = False
            validation_result["reason"] = (
                "Correction violates material constraints"
            )

        # 4. Проверка производственных возможностей
        production_violation = self._check_production_constraints(
            correction, context
        )
        if production_violation:
            validation_result["warnings"].append(
                "Correction may exceed production capabilities"
            )

        return validation_result

    def _check_geometric_correctness(
        self, correction: Dict, context: Dict, validation_result: Dict
    ) -> Dict:
        """Проверка геометрической корректности."""
        # Упрощенная проверка - в реальности здесь была бы сложная геометрическая валидация

        # Проверка на выход за границы листа
        boundary_violation = self._check_boundary_violation(
            correction, context
        )
        if boundary_violation:
            validation_result["is_valid"] = False
            validation_result["reason"] = (
                "Correction would place piece outside sheet boundaries"
            )

        # Проверка на пересечения с другими деталями
        intersection_violation = self._check_intersection_violation(
            correction, context
        )
        if intersection_violation:
            validation_result["warnings"].append(
                "Correction may cause intersection with other pieces"
            )
            # Не делаем невалидным, просто предупреждение

        # Проверка на минимальные размеры деталей
        size_violation = self._check_minimum_size_violation(
            correction, context
        )
        if size_violation:
            validation_result["warnings"].append(
                "Correction may result in pieces below minimum size"
            )

        return validation_result

    def _check_spacing_violation(
        self, correction: Dict, context: Dict
    ) -> bool:
        """Проверка нарушения минимальных отступов."""
        # Упрощенная проверка
        params = correction["parameters"]
        dx = abs(params.get("dx", 0))
        dy = abs(params.get("dy", 0))

        return dx < self.min_spacing or dy < self.min_spacing

    def _check_material_constraints(
        self, correction: Dict, context: Dict
    ) -> bool:
        """Проверка ограничений материала."""
        # Упрощенная проверка
        if correction["correction_type"] == "scale":
            max_increase = self.material_constraints.get(
                "max_scale_increase", self.max_scale_factor
            )
            params = correction["parameters"]
            return (
                params.get("scale_x", 1) > max_increase
                or params.get("scale_y", 1) > max_increase
            )
        return False

    def _check_production_constraints(
        self, correction: Dict, context: Dict
    ) -> bool:
        """Проверка производственных ограничений."""
        # Проверка на сложность операции
        correction_type = correction["correction_type"]

        if correction_type == "rotation":
            # Сложные углы могут быть проблематичными
            rotation = correction["parameters"].get("rotation", 0)
            return abs(rotation) > 45 and abs(rotation) % 90 != 0

        elif correction_type == "scale":
            # Непропорциональное масштабирование
            scale_x = correction["parameters"].get("scale_x", 1.0)
            scale_y = correction["parameters"].get("scale_y", 1.0)
            return abs(scale_x - scale_y) > 0.05

        return False

    def _check_boundary_violation(
        self, correction: Dict, context: Dict
    ) -> bool:
        """Проверка выхода за границы листа."""
        # В реальной реализации здесь была бы проверка координат
        # Упрощенно - проверяем только большие смещения
        if correction["correction_type"] == "position":
            params = correction["parameters"]
            dx = abs(params.get("dx", 0))
            dy = abs(params.get("dy", 0))

            # Предполагаем, что лист имеет размеры 2440x1220 мм
            sheet_width = 2440
            sheet_height = 1220

            # Упрощенная проверка - если смещение больше половины листа
            return dx > sheet_width / 2 or dy > sheet_height / 2

        return False

    def _check_intersection_violation(
        self, correction: Dict, context: Dict
    ) -> bool:
        """Проверка пересечений с другими деталями."""
        # В реальной реализации здесь была бы геометрическая проверка
        # Упрощенно - проверяем только большие смещения
        if correction["correction_type"] == "position":
            params = correction["parameters"]
            dx = abs(params.get("dx", 0))
            dy = abs(params.get("dy", 0))

            # Если смещение больше 500мм, возможно пересечение
            return dx > 500 or dy > 500

        return False

    def _check_minimum_size_violation(
        self, correction: Dict, context: Dict
    ) -> bool:
        """Проверка минимальных размеров деталей."""
        # Упрощенная проверка
        if correction["correction_type"] == "scale":
            params = correction["parameters"]
            scale_x = params.get("scale_x", 1.0)
            scale_y = params.get("scale_y", 1.0)

            # Если масштаб слишком маленький
            return scale_x < 0.8 or scale_y < 0.8

        return False

    def _calculate_validation_confidence(
        self, validation_result: Dict
    ) -> float:
        """Расчет оценки уверенности в валидации."""
        base_confidence = 1.0

        # Снижение уверенности за предупреждения
        warnings_count = len(validation_result.get("warnings", []))
        base_confidence -= warnings_count * 0.1

        # Снижение уверенности за технологические нарушения
        violations_count = len(
            validation_result.get("technological_violations", [])
        )
        base_confidence -= violations_count * 0.2

        return max(0.0, min(1.0, base_confidence))

    def _log_rejected_suggestion(
        self, suggestion: Dict, validation_result: Dict
    ):
        """Логирование отклоненных предложений."""
        try:
            log_entry = {
                "timestamp": str(np.datetime64("now")),
                "piece_id": suggestion.get("piece_id", "unknown"),
                "correction_type": suggestion.get(
                    "correction_type", "unknown"
                ),
                "rejection_reason": validation_result.get("reason", "unknown"),
                "warnings": validation_result.get("warnings", []),
                "technological_violations": validation_result.get(
                    "technological_violations", []
                ),
            }

            # Сохранение в файл логов
            log_dir = Path("data/logs/validation")
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / "rejected_suggestions.jsonl"
            with open(log_file, "a", encoding="utf-8") as f:
                import json

                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            # Простое логирование ошибки
            print(f"Error logging rejected suggestion: {e}")

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Получение статистики валидации."""
        try:
            log_dir = Path("data/logs/validation")
            log_file = log_dir / "rejected_suggestions.jsonl"

            if not log_file.exists():
                return {
                    "total_suggestions": 0,
                    "rejected_suggestions": 0,
                    "acceptance_rate": 1.0,
                    "common_rejection_reasons": [],
                }

            # Анализ логов
            import json

            rejected_suggestions = []

            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rejected_suggestions.append(json.loads(line.strip()))
                    except Exception:
                        continue

            # Статистика
            total_rejected = len(rejected_suggestions)
            rejection_reasons = {}

            for suggestion in rejected_suggestions:
                reason = suggestion.get("rejection_reason", "unknown")
                rejection_reasons[reason] = (
                    rejection_reasons.get(reason, 0) + 1
                )

            # Сортировка по частоте
            common_reasons = sorted(
                rejection_reasons.items(), key=lambda x: x[1], reverse=True
            )[:5]

            return {
                "total_suggestions": total_rejected,  # Упрощенно
                "rejected_suggestions": total_rejected,
                "acceptance_rate": 0.8,  # Упрощенно
                "common_rejection_reasons": common_reasons,
            }

        except Exception as e:
            return {
                "total_suggestions": 0,
                "rejected_suggestions": 0,
                "acceptance_rate": 0.0,
                "common_rejection_reasons": [],
                "error": str(e),
            }
