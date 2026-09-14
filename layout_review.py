"""Editable, engine-independent layout snapshots for operator review."""

from dataclasses import dataclass
from typing import Hashable, Iterable


_EPSILON = 1e-9


@dataclass(frozen=True)
class Placement:
    """One packed rectangle; dimensions include the configured kerf."""

    placement_id: Hashable
    x: float
    y: float
    width: float
    height: float
    rotated: bool = False
    source_index: int | None = None

    @property
    def area(self):
        return self.width * self.height


@dataclass(frozen=True)
class LayoutSnapshot:
    """A reviewable snapshot of one sheet or remnant."""

    layout_id: str
    width: float
    height: float
    placements: tuple[Placement, ...]
    material_key: object = None
    container_type: str = ""
    container_id: object = None
    output_file: str = ""


@dataclass(frozen=True)
class LayoutMetrics:
    layout_count: int
    used_area: float
    container_area: float
    utilization: float


@dataclass(frozen=True)
class RepackProposal:
    layouts: tuple[LayoutSnapshot, ...]
    before: LayoutMetrics
    after: LayoutMetrics
    locked_ids: frozenset[Hashable]
    moved_ids: frozenset[Hashable]
    freed_layout_ids: tuple[str, ...]
    feasible: bool
    reason: str = ""


@dataclass(frozen=True)
class _FreeRectangle:
    x: float
    y: float
    width: float
    height: float

    @property
    def area(self):
        return self.width * self.height


def calculate_layout_metrics(layouts: Iterable[LayoutSnapshot]):
    """Calculate comparable sheet count and area utilization."""
    used_layouts = tuple(layout for layout in layouts if layout.placements)
    used_area = sum(
        placement.area
        for layout in used_layouts
        for placement in layout.placements
    )
    container_area = sum(
        layout.width * layout.height for layout in used_layouts)
    utilization = used_area / container_area if container_area else 0.0
    return LayoutMetrics(
        layout_count=len(used_layouts),
        used_area=used_area,
        container_area=container_area,
        utilization=utilization,
    )


def repack_unlocked(layouts, locked_ids):
    """Keep locked placements and repack all others into earlier layouts.

    The deterministic first-fit policy deliberately prefers existing earlier
    layouts. This makes the primary optimization target explicit: empty a late
    sheet without changing any operator-approved placement.
    """
    original_layouts = tuple(layouts)
    locked_ids = frozenset(locked_ids)
    before = calculate_layout_metrics(original_layouts)

    validation_error = _validate_layouts(original_layouts, locked_ids)
    if validation_error:
        return _failed_proposal(
            original_layouts, before, locked_ids, validation_error)

    locked_by_layout = []
    free_by_layout = []
    unlocked = []

    for layout in original_layouts:
        locked = tuple(
            placement for placement in layout.placements
            if placement.placement_id in locked_ids
        )
        locked_by_layout.append(list(locked))

        free_rectangles = [
            _FreeRectangle(0, 0, layout.width, layout.height)
        ]
        for placement in locked:
            free_rectangles = _reserve(free_rectangles, placement)
        free_by_layout.append(free_rectangles)

        unlocked.extend(
            placement for placement in layout.placements
            if placement.placement_id not in locked_ids
        )

    unlocked.sort(
        key=lambda item: (
            -item.area,
            -max(item.width, item.height),
            str(item.placement_id),
        )
    )

    for placement in unlocked:
        candidate = _best_position(placement, free_by_layout)
        if candidate is None:
            return _failed_proposal(
                original_layouts,
                before,
                locked_ids,
                f"Не удалось разместить деталь {placement.placement_id}",
            )

        layout_index, free_rectangle, width, height, rotated = candidate
        packed = Placement(
            placement_id=placement.placement_id,
            x=free_rectangle.x,
            y=free_rectangle.y,
            width=width,
            height=height,
            rotated=rotated,
            source_index=placement.source_index,
        )
        locked_by_layout[layout_index].append(packed)
        free_by_layout[layout_index] = _reserve(
            free_by_layout[layout_index], packed)

    candidate_layouts = tuple(
        LayoutSnapshot(
            layout_id=layout.layout_id,
            width=layout.width,
            height=layout.height,
            placements=tuple(locked_by_layout[index]),
            material_key=layout.material_key,
            container_type=layout.container_type,
            container_id=layout.container_id,
            output_file=layout.output_file,
        )
        for index, layout in enumerate(original_layouts)
        if locked_by_layout[index]
    )
    after = calculate_layout_metrics(candidate_layouts)
    original_locations = _placement_locations(original_layouts)
    candidate_locations = _placement_locations(candidate_layouts)
    moved_ids = frozenset(
        placement_id
        for placement_id, location in candidate_locations.items()
        if original_locations[placement_id] != location
    )
    candidate_layout_ids = {
        layout.layout_id for layout in candidate_layouts
    }
    freed_layout_ids = tuple(
        layout.layout_id
        for layout in original_layouts
        if layout.placements and layout.layout_id not in candidate_layout_ids
    )

    return RepackProposal(
        layouts=candidate_layouts,
        before=before,
        after=after,
        locked_ids=locked_ids,
        moved_ids=moved_ids,
        freed_layout_ids=freed_layout_ids,
        feasible=True,
    )


def _failed_proposal(layouts, before, locked_ids, reason):
    return RepackProposal(
        layouts=layouts,
        before=before,
        after=before,
        locked_ids=locked_ids,
        moved_ids=frozenset(),
        freed_layout_ids=(),
        feasible=False,
        reason=reason,
    )


def _validate_layouts(layouts, locked_ids):
    known_ids = set()
    for layout in layouts:
        if layout.width <= 0 or layout.height <= 0:
            return f"Некорректный размер карты {layout.layout_id}"
        for placement in layout.placements:
            if placement.placement_id in known_ids:
                return f"Повторяется ID детали {placement.placement_id}"
            known_ids.add(placement.placement_id)
            if not _inside_layout(placement, layout):
                return f"Деталь {placement.placement_id} выходит за границы карты"

    unknown_ids = locked_ids - known_ids
    if unknown_ids:
        return f"Неизвестные закреплённые детали: {sorted(map(str, unknown_ids))}"

    for layout in layouts:
        locked = [
            placement for placement in layout.placements
            if placement.placement_id in locked_ids
        ]
        for index, first in enumerate(locked):
            if any(_intersects(first, second) for second in locked[index + 1:]):
                return f"Закреплённые детали на карте {layout.layout_id} пересекаются"
    return ""


def _inside_layout(placement, layout):
    return (
        placement.x >= -_EPSILON
        and placement.y >= -_EPSILON
        and placement.width > 0
        and placement.height > 0
        and placement.x + placement.width <= layout.width + _EPSILON
        and placement.y + placement.height <= layout.height + _EPSILON
    )


def _best_position(placement, free_by_layout):
    best = None
    best_score = None
    orientations = [(placement.width, placement.height, placement.rotated)]
    if abs(placement.width - placement.height) > _EPSILON:
        orientations.append(
            (placement.height, placement.width, not placement.rotated))

    for layout_index, free_rectangles in enumerate(free_by_layout):
        for free_rectangle in free_rectangles:
            for width, height, rotated in orientations:
                if (
                    width <= free_rectangle.width + _EPSILON
                    and height <= free_rectangle.height + _EPSILON
                ):
                    score = (
                        layout_index,
                        free_rectangle.area - width * height,
                        min(
                            free_rectangle.width - width,
                            free_rectangle.height - height,
                        ),
                        rotated != placement.rotated,
                        free_rectangle.y,
                        free_rectangle.x,
                    )
                    if best_score is None or score < best_score:
                        best_score = score
                        best = (
                            layout_index,
                            free_rectangle,
                            width,
                            height,
                            rotated,
                        )
    return best


def _reserve(free_rectangles, placement):
    remaining = []
    for free_rectangle in free_rectangles:
        remaining.extend(_subtract(free_rectangle, placement))
    return [rectangle for rectangle in remaining if rectangle.area > _EPSILON]


def _subtract(free_rectangle, placement):
    if not _intersects(free_rectangle, placement):
        return [free_rectangle]

    free_right = free_rectangle.x + free_rectangle.width
    free_top = free_rectangle.y + free_rectangle.height
    used_right = placement.x + placement.width
    used_top = placement.y + placement.height
    overlap_left = max(free_rectangle.x, placement.x)
    overlap_right = min(free_right, used_right)

    pieces = []
    if placement.x > free_rectangle.x:
        pieces.append(_FreeRectangle(
            free_rectangle.x,
            free_rectangle.y,
            placement.x - free_rectangle.x,
            free_rectangle.height,
        ))
    if used_right < free_right:
        pieces.append(_FreeRectangle(
            used_right,
            free_rectangle.y,
            free_right - used_right,
            free_rectangle.height,
        ))
    if placement.y > free_rectangle.y and overlap_right > overlap_left:
        pieces.append(_FreeRectangle(
            overlap_left,
            free_rectangle.y,
            overlap_right - overlap_left,
            placement.y - free_rectangle.y,
        ))
    if used_top < free_top and overlap_right > overlap_left:
        pieces.append(_FreeRectangle(
            overlap_left,
            used_top,
            overlap_right - overlap_left,
            free_top - used_top,
        ))
    return pieces


def _intersects(first, second):
    return not (
        first.x + first.width <= second.x + _EPSILON
        or second.x + second.width <= first.x + _EPSILON
        or first.y + first.height <= second.y + _EPSILON
        or second.y + second.height <= first.y + _EPSILON
    )


def _placement_locations(layouts):
    return {
        placement.placement_id: (
            layout.layout_id,
            placement.x,
            placement.y,
            placement.width,
            placement.height,
            placement.rotated,
        )
        for layout in layouts
        for placement in layout.placements
    }
