# План тестирования алгоритмов раскроя

## Цель

Сравнить алгоритмы `rectpack` на одинаковых наборах деталей и листов, не
меняя правила приоритета остатков, отступов и керфа. Базой сравнения считать
текущую схему: `MaxRectsBaf` для остатков и `MaxRectsBssf` для целых листов.

## Доступные стратегии в установленном rectpack

### MaxRects — основной кандидат для свободной раскладки

- `MaxRectsBl` — Bottom-Left;
- `MaxRectsBssf` — Best Short Side Fit;
- `MaxRectsBaf` — Best Area Fit;
- `MaxRectsBlsf` — Best Long Side Fit.

### Skyline — быстрый кандидат для больших серий деталей

- `SkylineBl`;
- `SkylineBlWm` — Bottom-Left с waste management;
- `SkylineMwf`;
- `SkylineMwfl`;
- `SkylineMwfWm` — Minimum Waste Fit с waste management;
- `SkylineMwflWm`.

### Guillotine — кандидат только при требовании прямых последовательных резов

Для каждого критерия выбора секции (`Bssf`, `Blsf`, `Baf`) доступны варианты
`Sas`, `Las`, `Slas`, `Llas`, `Maxas`, `Minas`:

- `GuillotineBssfSas`, `GuillotineBssfLas`, `GuillotineBssfSlas`,
  `GuillotineBssfLlas`, `GuillotineBssfMaxas`, `GuillotineBssfMinas`;
- `GuillotineBlsfSas`, `GuillotineBlsfLas`, `GuillotineBlsfSlas`,
  `GuillotineBlsfLlas`, `GuillotineBlsfMaxas`, `GuillotineBlsfMinas`;
- `GuillotineBafSas`, `GuillotineBafLas`, `GuillotineBafSlas`,
  `GuillotineBafLlas`, `GuillotineBafMaxas`, `GuillotineBafMinas`.

## Приоритет тестов

1. **Контроль:** текущая связка `MaxRectsBaf`/`MaxRectsBssf`.
2. **Высокий приоритет:** `MaxRectsBl`, `MaxRectsBlsf`, `SkylineBlWm`,
   `SkylineMwfWm`, `SkylineMwflWm`.
3. **Полный перебор качества:** остальные MaxRects и Skyline.
4. **Отдельный режим прямого реза:** все Guillotine, с проверкой не только
   площади, но и допустимости фактической технологии раскроя.

## Наборы данных

- `small-mixed`: 10–30 деталей, много разных размеров;
- `production-like`: копия реального `processed_data.csv` с материалами из
  `materials.csv`;
- `many-small`: 100+ мелких деталей;
- `large-parts`: крупные детали, близкие к размеру листа;
- `remnants-first`: одинаковые детали и несколько остатков разного размера;
- `rotation-sensitive`: вытянутые детали, где поворот существенно меняет
  результат;
- `edge-cases`: нулевая/минимальная площадь, неподходящий лист, детали,
  превышающие лист, и дубликаты `part_id`.

## Метрики

Для каждого запуска сохранять алгоритм, seed/порядок деталей и параметры
`margin`/`kerf`, затем измерять:

- число использованных остатков;
- число использованных целых листов;
- суммарную площадь отходов и процент заполнения по каждому листу;
- количество неразмещённых деталей;
- длину/число карт раскроя и время упаковки;
- корректность: отсутствие пересечений, выходов за рабочую область и
  дубликатов деталей;
- для Guillotine — прохождение отдельной проверки допустимости прямых резов.

Главный критерий — минимальное число целых листов при нуле неразмещённых
деталей. Вторичные критерии — площадь отходов, использование остатков,
время и технологическая пригодность DXF.

## Правила сравнения

- Один и тот же список деталей должен иметь одинаковую сортировку для всех
  алгоритмов; отдельно можно добавить эксперимент с несколькими сортировками.
- Алгоритмы сравниваются отдельно для фазы остатков и фазы целых листов, а не
  только одной общей цифрой.
- Любое улучшение должно пройти проверку DXF и не нарушать обновление таблицы
  материалов.
- Победитель принимается только после повторения на production-like и
  remnants-first наборах; единичная лучшая раскладка недостаточна.
