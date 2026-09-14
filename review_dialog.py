"""Visual drag-and-drop editor for operator review."""

import os
import tkinter as tk
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from .layout_review import (
    calculate_layout_metrics,
    move_placement,
    repack_unlocked,
    rotate_placement,
    snap_placement,
)
from .review_candidate import publish_candidate_outputs, write_candidate_outputs


@dataclass(frozen=True)
class ReviewDecision:
    approved: bool
    candidate_applied: bool = False
    backup_dir: Path | None = None


class OperatorReviewDialog:
    """Display real layouts and edit placements directly on a sheet canvas."""

    def __init__(
            self, parent, packing_result, details_df, materials_df, output_dir,
            pending_materials_path, margin, kerf, remnant_count):
        self.parent = parent
        self.packing_result = packing_result
        self.details_df = details_df
        self.materials_df = materials_df
        self.output_dir = Path(output_dir)
        self.pending_materials_path = Path(pending_materials_path)
        self.margin = margin
        self.kerf = kerf
        self.remnant_count = remnant_count
        self.original_layouts = tuple(packing_result.layouts)
        self.layouts = self.original_layouts
        self.locked_ids = set()
        self.undo_stack = []
        self.current_index = 0
        self.selected_id = None
        self.transfer_id = None
        self.drag_state = None
        self.item_placements = {}
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.dirty = False
        self.decision = ReviewDecision(False)
        self.detail_sources = self._index_detail_sources()

        self.window = tk.Toplevel(parent)
        self.window.title("Визуальная проверка раскроя")
        self.window.geometry("1280x820")
        self.window.minsize(980, 650)
        self.window.transient(parent)
        self.window.protocol("WM_DELETE_WINDOW", self._keep_draft)
        self._build()

    def show(self):
        self.window.grab_set()
        self.window.wait_visibility()
        self.window.focus_set()
        self.parent.wait_window(self.window)
        return self.decision

    def _index_detail_sources(self):
        sources = {}
        for layout in self.original_layouts:
            details = self.details_df[
                (self.details_df["thickness_mm"] == layout.thickness)
                & (self.details_df["material"] == layout.material)
            ].reset_index(drop=True)
            for placement in layout.placements:
                sources[placement.placement_id] = details.iloc[
                    placement.source_index]
        return sources

    def _build(self):
        ttk.Label(
            self.window,
            text=(f"Карт: {self.packing_result.layout_count}    "
                  f"Целых листов: {self.packing_result.total_used_sheets}    "
                  f"Остатков: {self.remnant_count}"),
            padding=(12, 9),
        ).pack(fill="x")
        body = ttk.Panedwindow(self.window, orient="horizontal")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        left = ttk.Frame(body, width=235)
        body.add(left, weight=0)
        ttk.Label(left, text="Карты раскроя").pack(anchor="w", pady=(0, 5))
        self.layout_list = tk.Listbox(
            left, width=30, exportselection=False, font=("Segoe UI", 10))
        self.layout_list.pack(fill="both", expand=True)
        self.layout_list.bind("<<ListboxSelect>>", self._select_layout)

        center = ttk.Frame(body)
        body.add(center, weight=1)
        self.canvas_title = ttk.Label(
            center, font=("Segoe UI", 11, "bold"))
        self.canvas_title.pack(fill="x", pady=(0, 5))
        self.canvas = tk.Canvas(
            center, background="#d8dde5", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self._render())
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)

        right = ttk.Frame(body, width=270, padding=(10, 0, 0, 0))
        body.add(right, weight=0)
        ttk.Label(
            right, text="Выбранная деталь",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        self.detail_label = ttk.Label(
            right, text="Щёлкните по детали", wraplength=250,
            justify="left", padding=(0, 8, 0, 10),
        )
        self.detail_label.pack(fill="x")
        self._button(right, "Повернуть на 90°", self._rotate)
        self._button(right, "Закрепить / снять", self._toggle_lock)
        self._button(right, "Перенести на другую карту", self._start_transfer)
        self._button(right, "Отменить действие", self._undo)
        self._button(right, "Вернуть исходный раскрой", self._reset)
        ttk.Separator(right).pack(fill="x", pady=10)
        self._button(right, "Переупаковать незакреплённые", self._auto_repack)
        self._button(right, "Открыть DXF текущего варианта", self._open_preview)
        self.metrics_label = ttk.Label(
            right, wraplength=250, justify="left", padding=(0, 12, 0, 0))
        self.metrics_label.pack(fill="x")

        self.status_label = ttk.Label(
            self.window,
            text=("Перетаскивайте детали мышью — грани прилипают к листу и "
                  "соседним деталям."),
            padding=(12, 3, 12, 8),
        )
        self.status_label.pack(fill="x")
        actions = ttk.Frame(self.window, padding=(12, 0, 12, 12))
        actions.pack(fill="x")
        ttk.Button(
            actions, text="Оставить черновик", command=self._keep_draft,
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            actions, text="Утвердить исходный", command=self._approve_original,
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            actions, text="Утвердить текущую карту", command=self._approve_current,
        ).pack(side="right")
        self._refresh_navigation()
        self._render()

    @staticmethod
    def _button(parent, text, command):
        button = ttk.Button(parent, text=text, command=command)
        button.pack(fill="x", pady=3)

    def _current_layout(self):
        if not self.layouts:
            return None
        self.current_index = min(self.current_index, len(self.layouts) - 1)
        return self.layouts[self.current_index]

    def _refresh_navigation(self):
        current_id = getattr(self._current_layout(), "layout_id", None)
        self.layout_list.delete(0, "end")
        for index, layout in enumerate(self.layouts):
            used = sum(item.area for item in layout.placements)
            utilization = used / (layout.width * layout.height)
            kind = "Остаток" if layout.container_type == "remnant" else "Лист"
            self.layout_list.insert(
                "end", f"{index + 1}. {kind} · {utilization:.0%} · "
                       f"{len(layout.placements)} дет.")
            if layout.layout_id == current_id:
                self.current_index = index
        if self.layouts:
            self.layout_list.selection_set(self.current_index)
        self._update_metrics()

    def _select_layout(self, _event=None):
        selection = self.layout_list.curselection()
        if not selection:
            return
        self.current_index = selection[0]
        if self.transfer_id is None:
            self.selected_id = None
        self._render()

    def _render(self):
        self.canvas.delete("all")
        self.item_placements.clear()
        layout = self._current_layout()
        if layout is None:
            return
        width = max(self.canvas.winfo_width(), 300)
        height = max(self.canvas.winfo_height(), 300)
        self.scale = min((width - 70) / layout.width,
                         (height - 70) / layout.height)
        self.offset_x = (width - layout.width * self.scale) / 2
        self.offset_y = (height - layout.height * self.scale) / 2
        self.canvas.create_rectangle(
            self.offset_x, self.offset_y,
            self.offset_x + layout.width * self.scale,
            self.offset_y + layout.height * self.scale,
            fill="white", outline="#30343b", width=2)
        self.canvas_title.configure(
            text=f"{Path(layout.output_file).name} — "
                 f"{layout.width:g} × {layout.height:g} мм")
        for placement in layout.placements:
            coordinates = self._canvas_coordinates(placement)
            if placement.placement_id == self.selected_id:
                fill, outline, line = "#ffbf69", "#c95700", 3
            elif placement.placement_id in self.locked_ids:
                fill, outline, line = "#9ad5a5", "#287a3b", 3
            else:
                fill, outline, line = "#8ecae6", "#26779a", 1
            rectangle = self.canvas.create_rectangle(
                *coordinates, fill=fill, outline=outline, width=line)
            self.item_placements[rectangle] = placement.placement_id
            if coordinates[2] - coordinates[0] > 42 and coordinates[3] - coordinates[1] > 18:
                source = self.detail_sources[placement.placement_id]
                label = self.canvas.create_text(
                    (coordinates[0] + coordinates[2]) / 2,
                    (coordinates[1] + coordinates[3]) / 2,
                    text=str(source["part_id"]), fill="#102a36",
                    font=("Segoe UI", 9, "bold"))
                self.item_placements[label] = placement.placement_id
        self._update_detail()

    def _canvas_coordinates(self, placement):
        layout = self._current_layout()
        left = self.offset_x + placement.x * self.scale
        right = left + placement.width * self.scale
        top = self.offset_y + (
            layout.height - placement.y - placement.height) * self.scale
        return left, top, right, top + placement.height * self.scale

    def _to_model(self, x, y):
        layout = self._current_layout()
        return ((x - self.offset_x) / self.scale,
                layout.height - (y - self.offset_y) / self.scale)

    def _find_placement(self, placement_id):
        for layout in self.layouts:
            for placement in layout.placements:
                if placement.placement_id == placement_id:
                    return layout, placement
        return None, None

    def _press(self, event):
        if self.transfer_id is not None:
            self._finish_transfer(event)
            return
        current = self.canvas.find_withtag("current")
        self.selected_id = self.item_placements.get(current[0]) if current else None
        self._render()
        if self.selected_id is None or self.selected_id in self.locked_ids:
            return
        _layout, placement = self._find_placement(self.selected_id)
        model_x, model_y = self._to_model(event.x, event.y)
        self.drag_state = placement, model_x, model_y

    def _drag(self, event):
        if self.drag_state is None:
            return
        placement, start_x, start_y = self.drag_state
        model_x, model_y = self._to_model(event.x, event.y)
        x = round(placement.x + model_x - start_x)
        y = round(placement.y + model_y - start_y)
        x, y = snap_placement(
            self.layouts, placement.placement_id,
            self._current_layout().layout_id, x, y)
        preview = replace(placement, x=x, y=y)
        try:
            move_placement(
                self.layouts, placement.placement_id,
                self._current_layout().layout_id, x, y)
            preview_color = "#2a9d3f"
        except ValueError:
            preview_color = "#ef233c"
        self._render()
        self.canvas.create_rectangle(
            *self._canvas_coordinates(preview), outline=preview_color,
            width=3, dash=(6, 3))

    def _release(self, event):
        if self.drag_state is None:
            return
        placement, start_x, start_y = self.drag_state
        self.drag_state = None
        model_x, model_y = self._to_model(event.x, event.y)
        x = round(placement.x + model_x - start_x)
        y = round(placement.y + model_y - start_y)
        x, y = snap_placement(
            self.layouts, placement.placement_id,
            self._current_layout().layout_id, x, y)
        self._apply_move(
            placement.placement_id, self._current_layout().layout_id, x, y)

    def _apply_move(self, placement_id, target_id, x, y):
        try:
            edited = move_placement(self.layouts, placement_id, target_id, x, y)
        except ValueError as error:
            self._status(str(error), True)
            self._render()
            return
        self._save_undo()
        self.layouts = edited
        self.dirty = self.layouts != self.original_layouts
        self._refresh_navigation()
        self._render()
        self._status(f"Деталь перемещена в {x:g}; {y:g} мм.")

    def _rotate(self):
        if not self._editable_selection():
            return
        try:
            edited = rotate_placement(self.layouts, self.selected_id)
        except ValueError as error:
            self._status(str(error), True)
            return
        self._save_undo()
        self.layouts = edited
        self.dirty = True
        self._render()
        self._update_metrics()
        self._status("Деталь повёрнута на 90°.")

    def _toggle_lock(self):
        if self.selected_id is None:
            self._status("Сначала выберите деталь.", True)
            return
        if self.selected_id in self.locked_ids:
            self.locked_ids.remove(self.selected_id)
            self._status("Фиксация снята.")
        else:
            self.locked_ids.add(self.selected_id)
            self._status("Положение детали закреплено.")
        self._render()

    def _editable_selection(self):
        if self.selected_id is None:
            self._status("Сначала выберите деталь.", True)
            return False
        if self.selected_id in self.locked_ids:
            self._status("Сначала снимите фиксацию детали.", True)
            return False
        return True

    def _start_transfer(self):
        if not self._editable_selection():
            return
        self.transfer_id = self.selected_id
        self._status("Выберите карту слева и щёлкните по свободному месту.")

    def _finish_transfer(self, event):
        placement_id = self.transfer_id
        _layout, placement = self._find_placement(placement_id)
        model_x, model_y = self._to_model(event.x, event.y)
        x = round(model_x - placement.width / 2)
        y = round(model_y - placement.height / 2)
        x, y = snap_placement(
            self.layouts, placement_id, self._current_layout().layout_id, x, y)
        self.transfer_id = None
        self._apply_move(
            placement_id, self._current_layout().layout_id, x, y)

    def _auto_repack(self):
        proposal = repack_unlocked(self.layouts, self.locked_ids)
        if not proposal.feasible:
            self._status(proposal.reason, True)
            return
        self._save_undo()
        self.layouts = proposal.layouts
        self.current_index = 0
        self.selected_id = None
        self.dirty = self.layouts != self.original_layouts
        self._refresh_navigation()
        self._render()
        self._status(
            f"Переупаковка завершена; освобождено карт: "
            f"{len(proposal.freed_layout_ids)}.")

    def _save_undo(self):
        self.undo_stack.append(self.layouts)
        self.undo_stack = self.undo_stack[-50:]

    def _undo(self):
        if not self.undo_stack:
            self._status("Нет действий для отмены.", True)
            return
        self.layouts = self.undo_stack.pop()
        self.current_index = min(self.current_index, len(self.layouts) - 1)
        self.selected_id = None
        self.transfer_id = None
        self.dirty = self.layouts != self.original_layouts
        self._refresh_navigation()
        self._render()
        self._status("Последнее действие отменено.")

    def _reset(self):
        if self.layouts != self.original_layouts:
            self._save_undo()
        self.layouts = self.original_layouts
        self.current_index = 0
        self.selected_id = None
        self.transfer_id = None
        self.locked_ids.clear()
        self.dirty = False
        self._refresh_navigation()
        self._render()
        self._status("Восстановлен исходный раскрой.")

    def _update_detail(self):
        if self.selected_id is None:
            self.detail_label.configure(text="Щёлкните по детали")
            return
        _layout, placement = self._find_placement(self.selected_id)
        source = self.detail_sources[self.selected_id]
        locked = "да" if self.selected_id in self.locked_ids else "нет"
        self.detail_label.configure(text=(
            f"Деталь: {source['part_id']}\nЗаказ: {source['order_id']}\n"
            f"Размер: {placement.width - self.kerf:g} × "
            f"{placement.height - self.kerf:g} мм\n"
            f"Координаты: {placement.x:g}; {placement.y:g}\n"
            f"Закреплена: {locked}"))

    def _update_metrics(self):
        current = calculate_layout_metrics(self.layouts)
        original = calculate_layout_metrics(self.original_layouts)
        self.metrics_label.configure(text=(
            f"Текущий вариант\nКарт: {current.layout_count} "
            f"(исходно {original.layout_count})\n"
            f"Заполнение: {current.utilization:.1%}\n"
            f"Отмена: {len(self.undo_stack)} действий"))

    def _stage(self):
        active = tuple(layout for layout in self.layouts if layout.placements)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        directory = self.output_dir / f"review_candidate_{stamp}"
        _paths, ledger = write_candidate_outputs(
            active, self.details_df, self.materials_df,
            directory, self.margin, self.kerf)
        return active, directory, ledger

    def _open_preview(self):
        try:
            _active, directory, _ledger = self._stage()
            os.startfile(directory)
            self._status(f"Проверочные DXF: {directory}")
        except Exception as error:
            messagebox.showerror(
                "Ошибка проверочного DXF", str(error), parent=self.window)

    def _approve_original(self):
        self.decision = ReviewDecision(True)
        self.window.destroy()

    def _approve_current(self):
        if not self.dirty:
            self._approve_original()
            return
        try:
            active, directory, ledger = self._stage()
            backup = publish_candidate_outputs(
                self.original_layouts, active, directory, ledger,
                self.pending_materials_path)
        except Exception as error:
            messagebox.showerror(
                "Ошибка применения",
                f"Исходные файлы сохранены или восстановлены.\n{error}",
                parent=self.window)
            return
        self.decision = ReviewDecision(True, True, backup)
        self.window.destroy()

    def _status(self, text, error=False):
        self.status_label.configure(
            text=text, foreground="#b42318" if error else "#245b2a")

    def _keep_draft(self):
        self.decision = ReviewDecision(False)
        self.window.destroy()
