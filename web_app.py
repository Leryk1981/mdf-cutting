"""Local FastAPI and SVG operator interface for MDF cutting."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from packer.config import setup_logging
from packer.constants import (
    DEFAULT_KERF,
    DEFAULT_MARGIN,
    DETAILS_REQUIRED_COLUMNS,
    MATERIALS_REQUIRED_COLUMNS,
    SUPPORTED_ENCODINGS,
)
from packer.layout_review import (
    calculate_layout_metrics,
    configure_cut_plan,
    move_placement,
    refresh_guillotine_cuts,
    repack_unlocked,
    rotate_placement,
    snap_placement,
    toggle_guillotine_cut,
    transfer_placement_at,
)
from packer.operator_review import finalize_materials_draft
from packer.packing import pack_and_generate_dxf
from packer.review_candidate import (
    build_material_ledger,
    publish_candidate_outputs,
    write_candidate_outputs,
)
from packer.utils import (
    check_critical_values,
    preprocess_dataframes,
    read_csv_files,
    validate_dataframes,
)


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
_PACK_LOCK = threading.RLock()


class RunRequest(BaseModel):
    details_path: str
    materials_path: str
    output_dir: str
    margin: int = Field(default=DEFAULT_MARGIN, ge=0, le=100)
    kerf: int = Field(default=DEFAULT_KERF, ge=0, le=30)


class MoveRequest(BaseModel):
    placement_id: str
    target_layout_id: str
    x: float
    y: float
    snap_tolerance: float = Field(default=40, ge=0, le=250)


class PlacementRequest(BaseModel):
    placement_id: str


class LayoutRequest(BaseModel):
    layout_id: str


class CutPlanRequest(BaseModel):
    layout_id: str
    max_cuts: int | None = Field(default=None, ge=0, le=3)
    toggle_first_orientation: bool = False


class TransferRequest(BaseModel):
    placement_id: str
    target_layout_id: str
    center_x: float
    center_y: float


class ApprovalRequest(BaseModel):
    variant: str = Field(pattern="^(current|original)$")


@dataclass
class WebReviewSession:
    session_id: str
    packing_result: Any
    details_df: Any
    materials_df: Any
    output_dir: Path
    pending_materials_path: Path
    published_materials_path: Path
    margin: int
    kerf: int
    original_layouts: tuple
    layouts: tuple
    locked_ids: set = field(default_factory=set)
    manual_ids: set = field(default_factory=set)
    undo_stack: list = field(default_factory=list)
    approved: bool = False
    public_ids: dict = field(default_factory=dict)

    def __post_init__(self):
        counter = 1
        for layout in self.original_layouts:
            for placement in layout.placements:
                if placement.placement_id not in self.public_ids:
                    self.public_ids[placement.placement_id] = f"p{counter}"
                    counter += 1

    def resolve_placement(self, public_id):
        for placement_id, candidate in self.public_ids.items():
            if candidate == public_id:
                return placement_id
        raise ValueError(f"Не найдена деталь {public_id}")

    def save_undo(self):
        self.undo_stack.append((
            self.layouts,
            frozenset(self.locked_ids),
            frozenset(self.manual_ids),
        ))
        self.undo_stack = self.undo_stack[-50:]

    @property
    def dirty(self):
        return self.layouts != self.original_layouts


class SessionStore:
    def __init__(self):
        self._sessions = {}
        self._lock = threading.RLock()

    def add(self, session):
        with self._lock:
            self._sessions[session.session_id] = session

    def get(self, session_id):
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Сеанс раскроя не найден")
        return session


store = SessionStore()
app = FastAPI(title="MDF Cutting", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")


def _safe_path(value, kind, must_exist=True):
    path = Path(value).expanduser().resolve()
    if must_exist and not path.exists():
        raise ValueError(f"Не найден {kind}: {path}")
    return path


def _detail_source(session, layout, placement):
    details = session.details_df[
        (session.details_df["thickness_mm"] == layout.thickness)
        & (session.details_df["material"] == layout.material)
    ].reset_index(drop=True)
    if placement.source_index is None or placement.source_index >= len(details):
        return {}
    row = details.iloc[placement.source_index]
    return {
        "part_id": str(row.get("part_id", "")),
        "order_id": str(row.get("order_id", "")),
    }


def _serialize_session(session):
    metrics = calculate_layout_metrics(session.layouts)
    ledger = build_material_ledger(
        session.materials_df,
        session.layouts,
        session.margin,
        session.kerf,
    )
    layouts = []
    for index, layout in enumerate(session.layouts):
        placements = []
        for placement in layout.placements:
            source = _detail_source(session, layout, placement)
            placements.append({
                "id": session.public_ids[placement.placement_id],
                "x": float(placement.x),
                "y": float(placement.y),
                "width": float(placement.width),
                "height": float(placement.height),
                "part_width": float(placement.width - session.kerf),
                "part_height": float(placement.height - session.kerf),
                "rotated": bool(placement.rotated),
                "locked": placement.placement_id in session.locked_ids,
                "manual": placement.placement_id in session.manual_ids,
                **source,
            })
        cut = layout.guillotine_cut
        plan = layout.cut_plan
        layouts.append({
            "number": index + 1,
            "id": layout.layout_id,
            "filename": Path(layout.output_file).name,
            "width": float(layout.width),
            "height": float(layout.height),
            "material": str(layout.material),
            "thickness": float(layout.thickness),
            "container_type": str(layout.container_type),
            "utilization": float(
                sum(item.area for item in layout.placements)
                / (layout.width * layout.height)
            ),
            "placements": placements,
            "cut": None if cut is None else {
                "orientation": str(cut.orientation),
                "position": float(cut.position),
                "x": float(cut.remnant_x),
                "y": float(cut.remnant_y),
                "width": float(cut.remnant_width),
                "height": float(cut.remnant_height),
                "area_m2": float(cut.area / 1_000_000),
                "usable": bool(
                    min(cut.remnant_width, cut.remnant_height) >= 60
                    and max(cut.remnant_width, cut.remnant_height) >= 1000
                ),
            },
            "cut_plan": {
                "max_cuts": plan.max_cuts,
                "preferred_first_orientation": (
                    plan.preferred_first_orientation),
                "cut_count": len(plan.cuts),
                "area_m2": float(plan.area / 1_000_000),
                "cuts": [{
                    "order": item.order,
                    "orientation": item.orientation,
                    "position": float(item.position),
                    "panel_x": float(item.panel_x),
                    "panel_y": float(item.panel_y),
                    "panel_width": float(item.panel_width),
                    "panel_height": float(item.panel_height),
                } for item in plan.cuts],
                "remnants": [{
                    "x": float(item.x),
                    "y": float(item.y),
                    "width": float(item.width),
                    "height": float(item.height),
                    "area_m2": float(item.area / 1_000_000),
                } for item in plan.remnants],
            },
        })
    return {
        "session_id": session.session_id,
        "layouts": layouts,
        "summary": {
            "layout_count": int(metrics.layout_count),
            "whole_sheets": int(session.packing_result.total_used_sheets),
            "remnant_count": int((ledger["is_remnant"] == True).sum()),
            "utilization": float(metrics.utilization),
            "undo_count": len(session.undo_stack),
            "dirty": bool(session.dirty),
            "approved": bool(session.approved),
            "output_dir": str(session.output_dir),
        },
    }


def _ensure_editable(session):
    if session.approved:
        raise ValueError("Этот раскрой уже утверждён")


def _raise_bad_request(error):
    raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/")
def index():
    return FileResponse(WEB_ROOT / "index.html")


@app.get("/api/config")
def config():
    return {
        "details_path": "",
        "materials_path": "",
        "output_dir": "",
        "margin": DEFAULT_MARGIN,
        "kerf": DEFAULT_KERF,
    }


@app.get("/api/browse")
def browse_path(
    kind: Literal["details", "materials", "output"],
    current: str | None = None,
):
    """Open a native local picker while the working UI stays in the browser."""
    import tkinter as tk
    from tkinter import filedialog

    initial = Path(current).expanduser() if current else ROOT
    if initial.is_file():
        initial = initial.parent
    if not initial.exists():
        initial = ROOT

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        if kind in {"details", "materials"}:
            selected = filedialog.askopenfilename(
                parent=root,
                title=(
                    "Выберите таблицу деталей"
                    if kind == "details"
                    else "Выберите таблицу склада"
                ),
                initialdir=initial,
                filetypes=(("CSV", "*.csv"), ("Все файлы", "*.*")),
            )
        else:
            selected = filedialog.askdirectory(
                parent=root,
                title="Выберите папку результатов",
                initialdir=initial,
            )
        return {"path": selected or None}
    finally:
        root.destroy()


@app.post("/api/run")
def run_cutting(request: RunRequest):
    try:
        details_path = _safe_path(request.details_path, "файл деталей")
        materials_path = _safe_path(request.materials_path, "файл склада")
        pattern_dir = ROOT / "patterns"
        output_dir = _safe_path(
            request.output_dir, "папка результатов", must_exist=False)
        if not details_path.is_file() or not materials_path.is_file():
            raise ValueError("Для деталей и склада должны быть выбраны CSV-файлы")
        pattern_dir.mkdir(exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        details_df, materials_df = read_csv_files(
            details_path, materials_path, SUPPORTED_ENCODINGS)
        if details_df is None or materials_df is None:
            raise ValueError("Не удалось прочитать CSV-файлы")
        valid, missing_details, missing_materials = validate_dataframes(
            details_df,
            materials_df,
            DETAILS_REQUIRED_COLUMNS,
            MATERIALS_REQUIRED_COLUMNS,
        )
        if not valid:
            problems = []
            if missing_details:
                problems.append("детали: " + ", ".join(missing_details))
            if missing_materials:
                problems.append("склад: " + ", ".join(missing_materials))
            raise ValueError("Отсутствуют колонки — " + "; ".join(problems))
        details_df, materials_df = preprocess_dataframes(
            details_df, materials_df)
        if details_df is None or materials_df is None:
            raise ValueError("Ошибка предобработки таблиц")
        if not check_critical_values(details_df, materials_df):
            raise ValueError("В исходных таблицах есть критические значения")

        pending = output_dir / "updated_materials.pending.csv"
        published = output_dir / "updated_materials.csv"
        with _PACK_LOCK:
            previous_directory = Path.cwd()
            try:
                os.chdir(output_dir)
                packing_result = pack_and_generate_dxf(
                    details_df,
                    materials_df,
                    pattern_dir,
                    request.margin,
                    request.kerf,
                    materials_output_path=pending,
                )
            finally:
                os.chdir(previous_directory)

        original = refresh_guillotine_cuts(packing_result.layouts)
        session = WebReviewSession(
            session_id=uuid4().hex,
            packing_result=packing_result,
            details_df=details_df,
            materials_df=materials_df,
            output_dir=output_dir,
            pending_materials_path=pending,
            published_materials_path=published,
            margin=request.margin,
            kerf=request.kerf,
            original_layouts=original,
            layouts=original,
        )
        store.add(session)
        return _serialize_session(session)
    except (OSError, ValueError) as error:
        _raise_bad_request(error)


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    return _serialize_session(store.get(session_id))


@app.post("/api/sessions/{session_id}/move")
def move(session_id: str, request: MoveRequest):
    session = store.get(session_id)
    try:
        _ensure_editable(session)
        placement_id = session.resolve_placement(request.placement_id)
        if placement_id in session.locked_ids:
            raise ValueError("Сначала снимите фиксацию детали")
        snapped_x, snapped_y = snap_placement(
            session.layouts,
            placement_id,
            request.target_layout_id,
            request.x,
            request.y,
            tolerance=request.snap_tolerance,
        )
        edited = move_placement(
            session.layouts,
            placement_id,
            request.target_layout_id,
            snapped_x,
            snapped_y,
        )
        session.save_undo()
        session.layouts = edited
        session.manual_ids.add(placement_id)
        payload = _serialize_session(session)
        payload["move"] = {
            "x": float(snapped_x),
            "y": float(snapped_y),
            "snapped": bool(
                snapped_x != request.x or snapped_y != request.y),
        }
        return payload
    except ValueError as error:
        _raise_bad_request(error)


@app.post("/api/sessions/{session_id}/rotate")
def rotate(session_id: str, request: PlacementRequest):
    session = store.get(session_id)
    try:
        _ensure_editable(session)
        placement_id = session.resolve_placement(request.placement_id)
        if placement_id in session.locked_ids:
            raise ValueError("Сначала снимите фиксацию детали")
        edited = rotate_placement(session.layouts, placement_id)
        session.save_undo()
        session.layouts = edited
        session.manual_ids.add(placement_id)
        return _serialize_session(session)
    except ValueError as error:
        _raise_bad_request(error)


@app.post("/api/sessions/{session_id}/transfer")
def transfer(session_id: str, request: TransferRequest):
    session = store.get(session_id)
    try:
        _ensure_editable(session)
        placement_id = session.resolve_placement(request.placement_id)
        if placement_id in session.locked_ids:
            raise ValueError("Сначала снимите фиксацию детали")
        edited, rotated = transfer_placement_at(
            session.layouts,
            placement_id,
            request.target_layout_id,
            request.center_x,
            request.center_y,
        )
        session.save_undo()
        session.layouts = edited
        session.manual_ids.add(placement_id)
        payload = _serialize_session(session)
        payload["transfer_rotated"] = rotated
        return payload
    except ValueError as error:
        _raise_bad_request(error)


@app.post("/api/sessions/{session_id}/lock")
def toggle_lock(session_id: str, request: PlacementRequest):
    session = store.get(session_id)
    try:
        _ensure_editable(session)
        placement_id = session.resolve_placement(request.placement_id)
        session.save_undo()
        if placement_id in session.locked_ids:
            session.locked_ids.remove(placement_id)
        else:
            session.locked_ids.add(placement_id)
        return _serialize_session(session)
    except ValueError as error:
        _raise_bad_request(error)


@app.post("/api/sessions/{session_id}/cut")
def toggle_cut(session_id: str, request: LayoutRequest):
    session = store.get(session_id)
    try:
        _ensure_editable(session)
        edited = toggle_guillotine_cut(session.layouts, request.layout_id)
        session.save_undo()
        session.layouts = edited
        return _serialize_session(session)
    except ValueError as error:
        _raise_bad_request(error)


@app.post("/api/sessions/{session_id}/cut-plan")
def update_cut_plan(session_id: str, request: CutPlanRequest):
    session = store.get(session_id)
    try:
        _ensure_editable(session)
        edited = configure_cut_plan(
            session.layouts,
            request.layout_id,
            max_cuts=request.max_cuts,
            toggle_first_orientation=request.toggle_first_orientation,
        )
        session.save_undo()
        session.layouts = edited
        return _serialize_session(session)
    except ValueError as error:
        _raise_bad_request(error)


@app.post("/api/sessions/{session_id}/repack")
def repack(session_id: str):
    session = store.get(session_id)
    try:
        _ensure_editable(session)
        proposal = repack_unlocked(
            session.layouts, session.locked_ids | session.manual_ids)
        if not proposal.feasible:
            raise ValueError(proposal.reason)
        changed = proposal.layouts != session.layouts
        if changed:
            session.save_undo()
            session.layouts = proposal.layouts
        payload = _serialize_session(session)
        payload["repack_changed"] = changed
        payload["freed_layouts"] = len(proposal.freed_layout_ids)
        return payload
    except ValueError as error:
        _raise_bad_request(error)


@app.post("/api/sessions/{session_id}/undo")
def undo(session_id: str):
    session = store.get(session_id)
    try:
        _ensure_editable(session)
        if not session.undo_stack:
            raise ValueError("Нет действий для отмены")
        layouts, locked_ids, manual_ids = session.undo_stack.pop()
        session.layouts = layouts
        session.locked_ids = set(locked_ids)
        session.manual_ids = set(manual_ids)
        return _serialize_session(session)
    except ValueError as error:
        _raise_bad_request(error)


@app.post("/api/sessions/{session_id}/reset")
def reset(session_id: str):
    session = store.get(session_id)
    try:
        _ensure_editable(session)
        if (
            session.layouts != session.original_layouts
            or session.locked_ids
            or session.manual_ids
        ):
            session.save_undo()
        session.layouts = session.original_layouts
        session.locked_ids.clear()
        session.manual_ids.clear()
        return _serialize_session(session)
    except ValueError as error:
        _raise_bad_request(error)


@app.post("/api/sessions/{session_id}/approve")
def approve(session_id: str, request: ApprovalRequest):
    session = store.get(session_id)
    try:
        _ensure_editable(session)
        backup_dir = None
        if request.variant == "current" and session.dirty:
            active = tuple(
                layout for layout in session.layouts if layout.placements)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            directory = session.output_dir / f"review_candidate_{stamp}"
            _paths, ledger = write_candidate_outputs(
                active,
                session.details_df,
                session.materials_df,
                directory,
                session.margin,
                session.kerf,
            )
            backup_dir = publish_candidate_outputs(
                session.original_layouts,
                active,
                directory,
                ledger,
                session.pending_materials_path,
            )
        result = finalize_materials_draft(
            session.pending_materials_path,
            session.published_materials_path,
            approved=True,
        )
        session.approved = True
        return {
            "approved": True,
            "variant": request.variant,
            "materials_path": str(result),
            "backup_dir": None if backup_dir is None else str(backup_dir),
            "output_dir": str(session.output_dir),
        }
    except (OSError, ValueError) as error:
        _raise_bad_request(error)


@app.post("/api/sessions/{session_id}/open-output")
def open_output(session_id: str):
    session = store.get(session_id)
    try:
        os.startfile(session.output_dir)
        return {"opened": True}
    except OSError as error:
        _raise_bad_request(error)


def main():
    import uvicorn

    setup_logging()
    uvicorn.run(app, host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
