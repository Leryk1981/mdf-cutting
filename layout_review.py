"""Editable, engine-independent layout snapshots for operator review."""

from dataclasses import dataclass, replace
from functools import lru_cache
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
    material_key: object = None

    @property
    def area(self):
        return self.width * self.height


@dataclass(frozen=True)
class GuillotineCut:
    """One full-width or full-height cut separating a stock remnant."""

    orientation: str
    position: float
    remnant_x: float
    remnant_y: float
    remnant_width: float
    remnant_height: float

    @property
    def area(self):
        return self.remnant_width * self.remnant_height


@dataclass(frozen=True)
class CutSegment:
    """One ordered guillotine cut scoped to a previously created panel."""

    order: int
    orientation: str
    position: float
    panel_x: float
    panel_y: float
    panel_width: float
    panel_height: float


@dataclass(frozen=True)
class RemnantRegion:
    """One non-overlapping empty leaf produced by a guillotine cut plan."""

    x: float
    y: float
    width: float
    height: float

    @property
    def area(self):
        return self.width * self.height


@dataclass(frozen=True)
class CutPlan:
    """An ordered cut tree and the usable remnants produced by its leaves."""

    cuts: tuple[CutSegment, ...] = ()
    remnants: tuple[RemnantRegion, ...] = ()
    max_cuts: int = 3
    preferred_first_orientation: str | None = None

    @property
    def area(self):
        return sum(remnant.area for remnant in self.remnants)


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
    thickness: float | None = None
    material: str = ""
    guillotine_cut: GuillotineCut | None = None
    cut_plan: CutPlan | None = None


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


def calculate_guillotine_cut(layout, orientation):
    """Build the safe outer cut for an orientation from current placements."""
    if orientation not in {"horizontal", "vertical"}:
        raise ValueError(f"Неизвестное направление реза: {orientation}")
    if not layout.placements:
        return None

    if orientation == "horizontal":
        position = max(item.y + item.height for item in layout.placements)
        remaining = max(0.0, layout.height - position)
        return GuillotineCut(
            orientation=orientation,
            position=position,
            remnant_x=0.0,
            remnant_y=position,
            remnant_width=layout.width,
            remnant_height=remaining,
        )

    position = max(item.x + item.width for item in layout.placements)
    remaining = max(0.0, layout.width - position)
    return GuillotineCut(
        orientation=orientation,
        position=position,
        remnant_x=position,
        remnant_y=0.0,
        remnant_width=remaining,
        remnant_height=layout.height,
    )


def select_guillotine_cut(layout, orientation=None):
    """Select a cut, defaulting to the candidate with the largest remnant."""
    if orientation is not None:
        return calculate_guillotine_cut(layout, orientation)
    candidates = tuple(
        cut for cut in (
            calculate_guillotine_cut(layout, "horizontal"),
            calculate_guillotine_cut(layout, "vertical"),
        )
        if cut is not None
    )
    if not candidates:
        return None

    def score(cut):
        usable = (
            min(cut.remnant_width, cut.remnant_height) >= 60
            and max(cut.remnant_width, cut.remnant_height) >= 1000
        )
        return usable, cut.area, cut.orientation == "horizontal"

    return max(
        candidates,
        key=score,
    )


@dataclass(frozen=True)
class _PlanOption:
    area: float
    cuts: tuple[CutSegment, ...]
    remnants: tuple[RemnantRegion, ...]


def calculate_cut_plan(
        layout, max_cuts=3, preferred_first_orientation=None,
        minimum_width=60, minimum_length=1000,
        extra_cut_penalty_area=200_000):
    """Find the best physically executable plan of up to ``max_cuts`` cuts."""
    max_cuts = max(0, min(3, int(max_cuts)))
    if preferred_first_orientation not in {None, "horizontal", "vertical"}:
        raise ValueError(
            f"Неизвестное направление реза: {preferred_first_orientation}")
    if not layout.placements or max_cuts == 0:
        return CutPlan(
            max_cuts=max_cuts,
            preferred_first_orientation=preferred_first_orientation,
        )

    placements = tuple(layout.placements)
    root = (0.0, 0.0, float(layout.width), float(layout.height))

    def usable(region):
        _x, _y, width, height = region
        return (
            min(width, height) >= minimum_width
            and max(width, height) >= minimum_length
        )

    def candidates(region, placement_ids, required_orientation):
        x, y, width, height = region
        selected = tuple(placements[index] for index in placement_ids)
        orientations = (
            (required_orientation,)
            if required_orientation is not None
            else ("vertical", "horizontal")
        )
        if "vertical" in orientations:
            positions = sorted({
                edge
                for item in selected
                for edge in (item.x, item.x + item.width)
            })
            for position in positions:
                if position <= x + _EPSILON or position >= x + width - _EPSILON:
                    continue
                if any(
                    item.x + _EPSILON < position
                    < item.x + item.width - _EPSILON
                    for item in selected
                ):
                    continue
                first_ids = tuple(
                    index for index in placement_ids
                    if placements[index].x + placements[index].width
                    <= position + _EPSILON
                )
                second_ids = tuple(
                    index for index in placement_ids
                    if placements[index].x >= position - _EPSILON
                )
                if len(first_ids) + len(second_ids) != len(placement_ids):
                    continue
                yield (
                    CutSegment(0, "vertical", position, x, y, width, height),
                    (x, y, position - x, height), first_ids,
                    (position, y, x + width - position, height), second_ids,
                )
        if "horizontal" in orientations:
            positions = sorted({
                edge
                for item in selected
                for edge in (item.y, item.y + item.height)
            })
            for position in positions:
                if position <= y + _EPSILON or position >= y + height - _EPSILON:
                    continue
                if any(
                    item.y + _EPSILON < position
                    < item.y + item.height - _EPSILON
                    for item in selected
                ):
                    continue
                first_ids = tuple(
                    index for index in placement_ids
                    if placements[index].y + placements[index].height
                    <= position + _EPSILON
                )
                second_ids = tuple(
                    index for index in placement_ids
                    if placements[index].y >= position - _EPSILON
                )
                if len(first_ids) + len(second_ids) != len(placement_ids):
                    continue
                yield (
                    CutSegment(0, "horizontal", position, x, y, width, height),
                    (x, y, width, position - y), first_ids,
                    (x, position, width, y + height - position), second_ids,
                )

    @lru_cache(maxsize=None)
    def options(region, placement_ids, cuts_left, required_orientation=None):
        if not placement_ids:
            if usable(region):
                remnant = RemnantRegion(*region)
                return {0: _PlanOption(remnant.area, (), (remnant,))}
            return {0: _PlanOption(0.0, (), ())}
        result = {0: _PlanOption(0.0, (), ())}
        if cuts_left == 0:
            return result
        for cut, first, first_ids, second, second_ids in candidates(
                region, placement_ids, required_orientation):
            first_options = options(first, first_ids, cuts_left - 1, None)
            second_options = options(second, second_ids, cuts_left - 1, None)
            for first_count, first_option in first_options.items():
                for second_count, second_option in second_options.items():
                    count = 1 + first_count + second_count
                    if count > cuts_left:
                        continue
                    proposal = _PlanOption(
                        first_option.area + second_option.area,
                        (cut,) + first_option.cuts + second_option.cuts,
                        first_option.remnants + second_option.remnants,
                    )
                    current = result.get(count)
                    if current is None or proposal.area > current.area + _EPSILON:
                        result[count] = proposal
        return result

    available = options(
        root,
        tuple(range(len(placements))),
        max_cuts,
        preferred_first_orientation,
    )
    ranked = []
    for count, option in available.items():
        if option.area <= _EPSILON:
            continue
        operational_score = (
            option.area - extra_cut_penalty_area * max(0, count - 1)
        )
        ranked.append((operational_score, option.area, -count, option))
    best = max(ranked, key=lambda item: item[:3], default=None)
    if best is None or best[0] <= 0:
        return CutPlan(
            max_cuts=max_cuts,
            preferred_first_orientation=preferred_first_orientation,
        )
    option = best[-1]
    ordered_cuts = tuple(
        replace(cut, order=index)
        for index, cut in enumerate(option.cuts, start=1)
    )
    return CutPlan(
        cuts=ordered_cuts,
        remnants=option.remnants,
        max_cuts=max_cuts,
        preferred_first_orientation=preferred_first_orientation,
    )


def refresh_guillotine_cut(layout):
    """Recalculate cut geometry while preserving the operator's direction."""
    orientation = (
        layout.guillotine_cut.orientation
        if layout.guillotine_cut is not None
        else None
    )
    cut = select_guillotine_cut(layout, orientation)
    if cut is None and orientation is not None:
        cut = select_guillotine_cut(layout)
    existing_plan = layout.cut_plan
    plan = calculate_cut_plan(
        layout,
        max_cuts=existing_plan.max_cuts if existing_plan is not None else 3,
        preferred_first_orientation=(
            existing_plan.preferred_first_orientation
            if existing_plan is not None else None
        ),
    )
    return replace(layout, guillotine_cut=cut, cut_plan=plan)


def refresh_guillotine_cuts(layouts):
    return tuple(refresh_guillotine_cut(layout) for layout in layouts)


def toggle_guillotine_cut(layouts, layout_id):
    """Switch one layout between horizontal and vertical guillotine cuts."""
    edited = []
    found = False
    for layout in layouts:
        if layout.layout_id != layout_id:
            edited.append(layout)
            continue
        found = True
        current = refresh_guillotine_cut(layout).guillotine_cut
        orientation = (
            "vertical"
            if current is None or current.orientation == "horizontal"
            else "horizontal"
        )
        cut = calculate_guillotine_cut(layout, orientation)
        current_plan = layout.cut_plan or CutPlan()
        plan = calculate_cut_plan(
            layout,
            max_cuts=current_plan.max_cuts,
            preferred_first_orientation=orientation,
        )
        edited.append(replace(
            layout, guillotine_cut=cut, cut_plan=plan))
    if not found:
        raise ValueError(f"Не найдена карта {layout_id}")
    return tuple(edited)


def configure_cut_plan(
        layouts, layout_id, max_cuts=None, toggle_first_orientation=False):
    """Change an operator plan limit or request the opposite first cut."""
    edited = []
    found = False
    for layout in layouts:
        if layout.layout_id != layout_id:
            edited.append(layout)
            continue
        found = True
        current = layout.cut_plan or CutPlan()
        limit = current.max_cuts if max_cuts is None else int(max_cuts)
        preferred = current.preferred_first_orientation
        if toggle_first_orientation:
            first = current.cuts[0].orientation if current.cuts else preferred
            preferred = "vertical" if first != "vertical" else "horizontal"
        plan = calculate_cut_plan(
            layout,
            max_cuts=limit,
            preferred_first_orientation=preferred,
        )
        edited.append(replace(layout, cut_plan=plan))
    if not found:
        raise ValueError(f"Не найдена карта {layout_id}")
    return tuple(edited)


def guillotine_remnants(layout, minimum_width=60, minimum_length=1000):
    """Return all usable, non-overlapping remnants from the selected cut tree."""
    layout = refresh_guillotine_cut(layout)
    return tuple(
        (max(item.width, item.height), min(item.width, item.height))
        for item in layout.cut_plan.remnants
        if min(item.width, item.height) >= minimum_width
        and max(item.width, item.height) >= minimum_length
    )


def guillotine_remnant(layout, minimum_width=60, minimum_length=1000):
    """Return the largest selected remnant for legacy single-remnant callers."""
    remnants = guillotine_remnants(
        layout, minimum_width, minimum_length)
    return max(remnants, key=lambda item: item[0] * item[1], default=None)


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


def move_placement(layouts, placement_id, target_layout_id, x, y):
    """Move one placement, rejecting material mismatch, bounds, or collision."""
    layouts = tuple(layouts)
    source_index = None
    target_index = None
    placement = None
    for layout_index, layout in enumerate(layouts):
        if layout.layout_id == target_layout_id:
            target_index = layout_index
        for candidate in layout.placements:
            if candidate.placement_id == placement_id:
                if placement is not None:
                    raise ValueError(f"Повторяется ID детали {placement_id}")
                source_index = layout_index
                placement = candidate

    if placement is None:
        raise ValueError(f"Не найдена деталь {placement_id}")
    if target_index is None:
        raise ValueError(f"Не найдена карта {target_layout_id}")
    source_layout = layouts[source_index]
    target_layout = layouts[target_index]
    if source_layout.material_key != target_layout.material_key:
        raise ValueError("Нельзя переносить деталь на другой материал или толщину")

    moved = replace(placement, x=float(x), y=float(y))
    if not _inside_layout(moved, target_layout):
        raise ValueError("Деталь выходит за границы карты")
    for other in target_layout.placements:
        if other.placement_id != placement_id and _intersects(moved, other):
            raise ValueError(f"Деталь пересекается с {other.placement_id}")

    edited = list(layouts)
    if source_index == target_index:
        edited[source_index] = replace(
            source_layout,
            placements=tuple(
                moved if item.placement_id == placement_id else item
                for item in source_layout.placements
            ),
        )
    else:
        edited[source_index] = replace(
            source_layout,
            placements=tuple(
                item for item in source_layout.placements
                if item.placement_id != placement_id
            ),
        )
        edited[target_index] = replace(
            target_layout,
            placements=target_layout.placements + (moved,),
        )
    return refresh_guillotine_cuts(edited)


def snap_placement(
        layouts, placement_id, target_layout_id, x, y, tolerance=12):
    """Snap a proposed position to sheet or neighbour edges when valid."""
    target_layout = next(
        (layout for layout in layouts if layout.layout_id == target_layout_id),
        None,
    )
    if target_layout is None:
        raise ValueError(f"Не найдена карта {target_layout_id}")
    _source_layout, placement = next(
        ((layout, item) for layout in layouts for item in layout.placements
         if item.placement_id == placement_id),
        (None, None),
    )
    if placement is None:
        raise ValueError(f"Не найдена деталь {placement_id}")

    x_targets = {0.0, target_layout.width - placement.width}
    y_targets = {0.0, target_layout.height - placement.height}
    for other in target_layout.placements:
        if other.placement_id == placement_id:
            continue
        x_targets.update({
            other.x - placement.width,
            other.x + other.width,
        })
        y_targets.update({
            other.y - placement.height,
            other.y + other.height,
        })

    nearby_x = {
        target for target in x_targets if abs(target - x) <= tolerance}
    nearby_y = {
        target for target in y_targets if abs(target - y) <= tolerance}
    x_candidates = nearby_x or {float(x)}
    y_candidates = nearby_y or {float(y)}
    candidates = sorted(
        ((candidate_x, candidate_y)
         for candidate_x in x_candidates
         for candidate_y in y_candidates),
        key=lambda point: (
            abs(point[0] - x) + abs(point[1] - y),
            abs(point[0] - x),
            abs(point[1] - y),
        ),
    )
    for candidate_x, candidate_y in candidates:
        try:
            move_placement(
                layouts,
                placement_id,
                target_layout_id,
                candidate_x,
                candidate_y,
            )
        except ValueError:
            continue
        return candidate_x, candidate_y
    return float(x), float(y)


def transfer_fit(layouts, placement_id, target_layout_id):
    """Return ``direct``, ``rotated``, or ``None`` for a target layout."""
    layouts = tuple(layouts)
    target = next(
        (layout for layout in layouts if layout.layout_id == target_layout_id),
        None,
    )
    source, placement = _find_layout_placement(layouts, placement_id)
    if target is None or source is None:
        return None
    if source.material_key != target.material_key:
        return None
    for was_rotated, oriented, oriented_layouts in _transfer_orientations(
            layouts, placement_id):
        for x, y in _alignment_positions(target, oriented):
            try:
                move_placement(
                    oriented_layouts, placement_id, target_layout_id, x, y)
                return "rotated" if was_rotated else "direct"
            except ValueError:
                continue
    return None


def transfer_placement_at(
        layouts, placement_id, target_layout_id, center_x, center_y,
        tolerance=12):
    """Place at the requested target point, rotating automatically if needed."""
    layouts = tuple(layouts)
    source, _placement = _find_layout_placement(layouts, placement_id)
    target = next(
        (layout for layout in layouts if layout.layout_id == target_layout_id),
        None,
    )
    if source is None or target is None:
        raise ValueError("Не найдена деталь или целевая карта")
    if source.material_key != target.material_key:
        raise ValueError("Целевая карта имеет другой материал или толщину")

    for was_rotated, oriented, oriented_layouts in _transfer_orientations(
            layouts, placement_id):
        x = round(center_x - oriented.width / 2)
        y = round(center_y - oriented.height / 2)
        x, y = snap_placement(
            oriented_layouts,
            placement_id,
            target_layout_id,
            x,
            y,
            tolerance,
        )
        try:
            edited = move_placement(
                oriented_layouts, placement_id, target_layout_id, x, y)
            return edited, was_rotated
        except ValueError:
            continue
    raise ValueError(
        "В выбранной точке деталь не помещается даже после поворота")


def _find_layout_placement(layouts, placement_id):
    for layout in layouts:
        for placement in layout.placements:
            if placement.placement_id == placement_id:
                return layout, placement
    return None, None


def _transfer_orientations(layouts, placement_id):
    _source, placement = _find_layout_placement(layouts, placement_id)
    if placement is None:
        return ()
    orientations = [(False, placement, layouts)]
    if abs(placement.width - placement.height) <= _EPSILON:
        return tuple(orientations)
    rotated = replace(
        placement,
        width=placement.height,
        height=placement.width,
        rotated=not placement.rotated,
    )
    rotated_layouts = tuple(
        replace(
            layout,
            placements=tuple(
                rotated if item.placement_id == placement_id else item
                for item in layout.placements
            ),
        )
        for layout in layouts
    )
    orientations.append((True, rotated, rotated_layouts))
    return tuple(orientations)


def _alignment_positions(layout, placement):
    x_positions = {0, layout.width - placement.width}
    y_positions = {0, layout.height - placement.height}
    for other in layout.placements:
        if other.placement_id == placement.placement_id:
            continue
        x_positions.update({
            other.x - placement.width,
            other.x + other.width,
        })
        y_positions.update({
            other.y - placement.height,
            other.y + other.height,
        })
    return tuple(
        (x, y) for x in sorted(x_positions) for y in sorted(y_positions))


def rotate_placement(layouts, placement_id):
    """Rotate and find the nearest valid aligned position on the same layout."""
    for layout in layouts:
        for placement in layout.placements:
            if placement.placement_id != placement_id:
                continue
            center_x = placement.x + placement.width / 2
            center_y = placement.y + placement.height / 2
            rotated = replace(
                placement,
                width=placement.height,
                height=placement.width,
                rotated=not placement.rotated,
            )
            center_position = (
                center_x - rotated.width / 2,
                center_y - rotated.height / 2,
            )
            rotated_layouts = tuple(
                replace(
                    candidate_layout,
                    placements=tuple(
                        rotated if item.placement_id == placement_id else item
                        for item in candidate_layout.placements
                    ),
                ) if candidate_layout.layout_id == layout.layout_id
                else candidate_layout
                for candidate_layout in layouts
            )
            x_candidates = {
                center_position[0],
                placement.x,
                placement.x + placement.width - rotated.width,
                min(max(center_position[0], 0), layout.width - rotated.width),
                0,
                layout.width - rotated.width,
            }
            y_candidates = {
                center_position[1],
                placement.y,
                placement.y + placement.height - rotated.height,
                min(max(center_position[1], 0), layout.height - rotated.height),
                0,
                layout.height - rotated.height,
            }
            for other in layout.placements:
                if other.placement_id == placement_id:
                    continue
                x_candidates.update({
                    other.x - rotated.width,
                    other.x + other.width,
                })
                y_candidates.update({
                    other.y - rotated.height,
                    other.y + other.height,
                })
            preferred_positions = [
                (placement.x, placement.y),
                center_position,
                (placement.x + placement.width - rotated.width, placement.y),
                (placement.x, placement.y + placement.height - rotated.height),
                (
                    placement.x + placement.width - rotated.width,
                    placement.y + placement.height - rotated.height,
                ),
                (
                    min(max(placement.x, 0), layout.width - rotated.width),
                    min(max(placement.y, 0), layout.height - rotated.height),
                ),
            ]
            remaining_positions = sorted(
                ((x, y) for x in x_candidates for y in y_candidates),
                key=lambda point: (
                    abs(point[0] - center_position[0])
                    + abs(point[1] - center_position[1]),
                    abs(point[0] - center_position[0]),
                ),
            )
            positions = []
            for position in preferred_positions + remaining_positions:
                if position not in positions:
                    positions.append(position)
            for x, y in positions:
                snapped_x, snapped_y = snap_placement(
                    rotated_layouts,
                    placement_id,
                    layout.layout_id,
                    x,
                    y,
                )
                candidates = [(x, y)]
                if (snapped_x, snapped_y) != (x, y):
                    candidates.append((snapped_x, snapped_y))
                for candidate_x, candidate_y in candidates:
                    try:
                        return move_placement(
                            rotated_layouts,
                            placement_id,
                            layout.layout_id,
                            candidate_x,
                            candidate_y,
                        )
                    except ValueError:
                        continue
            raise ValueError(
                "После поворота нет свободного места для детали на этой карте")
    raise ValueError(f"Не найдена деталь {placement_id}")


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
        candidate = _best_position(
            placement, free_by_layout, original_layouts)
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
            material_key=placement.material_key,
        )
        locked_by_layout[layout_index].append(packed)
        free_by_layout[layout_index] = _reserve(
            free_by_layout[layout_index], packed)

    candidate_layouts = tuple(
        refresh_guillotine_cut(replace(
            layout,
            placements=tuple(locked_by_layout[index]),
        ))
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


def _best_position(placement, free_by_layout, layouts):
    best = None
    best_score = None
    orientations = [(placement.width, placement.height, placement.rotated)]
    if abs(placement.width - placement.height) > _EPSILON:
        orientations.append(
            (placement.height, placement.width, not placement.rotated))

    for layout_index, free_rectangles in enumerate(free_by_layout):
        if layouts[layout_index].material_key != placement.material_key:
            continue
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
