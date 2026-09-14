"""Modal operator review UI for original and repacked cutting layouts."""

import os
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from .layout_review import repack_unlocked
from .review_candidate import (
    publish_candidate_outputs,
    write_candidate_outputs,
)


@dataclass(frozen=True)
class ReviewDecision:
    approved: bool
    candidate_applied: bool = False
    backup_dir: Path | None = None


class OperatorReviewDialog:
    """Let an operator lock placements and inspect a staged repack proposal."""

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
        self.locked_ids = set()
        self.detail_by_item = {}
        self.proposal = None
        self.candidate_dir = None
        self.candidate_materials_path = None
        self.decision = ReviewDecision(approved=False)

        self.window = tk.Toplevel(parent)
        self.window.title("Проверка карт раскроя")
        self.window.geometry("1000x680")
        self.window.minsize(850, 520)
        self.window.transient(parent)
        self.window.protocol("WM_DELETE_WINDOW", self._keep_draft)
        self._build()

    def show(self):
        self.window.grab_set()
        self.window.wait_visibility()
        self.window.focus_set()
        self.parent.wait_window(self.window)
        return self.decision

    def _build(self):
        summary = (
            f"Карт: {self.packing_result.layout_count}    "
            f"Целых листов: {self.packing_result.total_used_sheets}    "
            f"Остатков: {self.remnant_count}    "
            "Выберите детали и закрепите удачные позиции."
        )
        ttk.Label(
            self.window, text=summary, padding=(12, 10),
        ).pack(fill="x")

        columns = ("kind", "size", "details", "locked")
        self.tree = ttk.Treeview(
            self.window,
            columns=columns,
            show="tree headings",
            selectmode="extended",
        )
        self.tree.heading("#0", text="Карта / деталь")
        self.tree.heading("kind", text="Тип")
        self.tree.heading("size", text="Размер")
        self.tree.heading("details", text="Деталей")
        self.tree.heading("locked", text="Закреплена")
        self.tree.column("#0", width=320)
        self.tree.column("kind", width=100, anchor="center")
        self.tree.column("size", width=150, anchor="center")
        self.tree.column("details", width=80, anchor="center")
        self.tree.column("locked", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self._populate_tree()

        controls = ttk.Frame(self.window, padding=(12, 0, 12, 8))
        controls.pack(fill="x")
        ttk.Button(
            controls,
            text="Закрепить / снять",
            command=self._toggle_locks,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            controls,
            text="Попробовать освободить карту",
            command=self._build_candidate,
        ).pack(side="left", padx=(0, 8))
        self.open_button = ttk.Button(
            controls,
            text="Открыть улучшенный вариант",
            command=self._open_candidate,
            state="disabled",
        )
        self.open_button.pack(side="left")

        self.result_label = ttk.Label(
            self.window,
            text="Улучшенный вариант ещё не рассчитан.",
            padding=(12, 4, 12, 8),
        )
        self.result_label.pack(fill="x")

        actions = ttk.Frame(self.window, padding=(12, 0, 12, 12))
        actions.pack(fill="x")
        ttk.Button(
            actions,
            text="Оставить черновик",
            command=self._keep_draft,
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            actions,
            text="Утвердить исходный",
            command=self._approve_original,
        ).pack(side="right", padx=(8, 0))
        self.approve_candidate_button = ttk.Button(
            actions,
            text="Утвердить улучшенный",
            command=self._approve_candidate,
            state="disabled",
        )
        self.approve_candidate_button.pack(side="right")

    def _populate_tree(self):
        for layout_index, layout in enumerate(self.packing_result.layouts):
            layout_item = self.tree.insert(
                "",
                "end",
                iid=f"layout-{layout_index}",
                text=Path(layout.output_file).name,
                values=(
                    "остаток" if layout.container_type == "remnant" else "лист",
                    f"{layout.width:g} × {layout.height:g}",
                    len(layout.placements),
                    "",
                ),
                open=True,
            )
            material_details = self.details_df[
                (self.details_df["thickness_mm"] == layout.thickness)
                & (self.details_df["material"] == layout.material)
            ].reset_index(drop=True)
            for detail_index, placement in enumerate(layout.placements):
                source = material_details.iloc[placement.source_index]
                item = f"detail-{layout_index}-{detail_index}"
                self.tree.insert(
                    layout_item,
                    "end",
                    iid=item,
                    text=f"{source['part_id']} / {source['order_id']}",
                    values=(
                        "деталь",
                        f"{placement.width - self.kerf:g} × "
                        f"{placement.height - self.kerf:g}",
                        "",
                        "нет",
                    ),
                )
                self.detail_by_item[item] = placement.placement_id

    def _toggle_locks(self):
        changed = False
        for item in self.tree.selection():
            placement_id = self.detail_by_item.get(item)
            if placement_id is None:
                continue
            if placement_id in self.locked_ids:
                self.locked_ids.remove(placement_id)
                locked_text = "нет"
            else:
                self.locked_ids.add(placement_id)
                locked_text = "да"
            self.tree.set(item, "locked", locked_text)
            changed = True
        if changed:
            self._invalidate_candidate()

    def _invalidate_candidate(self):
        self.proposal = None
        self.approve_candidate_button.configure(state="disabled")
        self.open_button.configure(state="disabled")
        self.result_label.configure(
            text="Фиксация изменилась — пересчитайте улучшенный вариант.")

    def _build_candidate(self):
        proposal = repack_unlocked(
            self.packing_result.layouts, self.locked_ids)
        if not proposal.feasible:
            messagebox.showerror(
                "Переупаковка невозможна", proposal.reason,
                parent=self.window,
            )
            return

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        candidate_dir = self.output_dir / f"review_candidate_{stamp}"
        try:
            _dxf_paths, candidate_materials_path = write_candidate_outputs(
                proposal.layouts,
                self.details_df,
                self.materials_df,
                candidate_dir,
                self.margin,
                self.kerf,
            )
        except Exception as error:
            messagebox.showerror(
                "Ошибка улучшенного варианта",
                f"Не удалось сформировать проверочные файлы:\n{error}",
                parent=self.window,
            )
            return

        self.proposal = proposal
        self.candidate_dir = candidate_dir
        self.candidate_materials_path = candidate_materials_path
        freed = len(proposal.freed_layout_ids)
        self.result_label.configure(
            text=(
                f"До: {proposal.before.layout_count} карт, "
                f"заполнение {proposal.before.utilization:.1%}.  "
                f"После: {proposal.after.layout_count} карт, "
                f"заполнение {proposal.after.utilization:.1%}.  "
                f"Освобождено: {freed}; перемещено деталей: "
                f"{len(proposal.moved_ids)}."
            )
        )
        self.open_button.configure(state="normal")
        self.approve_candidate_button.configure(state="normal")

    def _open_candidate(self):
        if self.candidate_dir is None:
            return
        try:
            os.startfile(self.candidate_dir)
        except OSError as error:
            messagebox.showerror(
                "Не удалось открыть папку", str(error), parent=self.window)

    def _approve_original(self):
        self.decision = ReviewDecision(approved=True)
        self.window.destroy()

    def _approve_candidate(self):
        if self.proposal is None or self.candidate_dir is None:
            return
        try:
            backup_dir = publish_candidate_outputs(
                self.packing_result.layouts,
                self.proposal.layouts,
                self.candidate_dir,
                self.candidate_materials_path,
                self.pending_materials_path,
            )
        except Exception as error:
            messagebox.showerror(
                "Ошибка применения",
                f"Исходные файлы сохранены или восстановлены.\n{error}",
                parent=self.window,
            )
            return
        self.decision = ReviewDecision(
            approved=True,
            candidate_applied=True,
            backup_dir=backup_dir,
        )
        self.window.destroy()

    def _keep_draft(self):
        self.decision = ReviewDecision(approved=False)
        self.window.destroy()
