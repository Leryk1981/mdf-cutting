"""Utilities for publishing an operator-approved material ledger."""

import csv
import os
from pathlib import Path


def count_material_remnants(materials_path):
    """Return the number of remnant rows in a persisted material ledger."""
    with Path(materials_path).open(
            "r", encoding="utf-8-sig", newline="") as materials_file:
        rows = csv.DictReader(materials_file, delimiter=";")
        if not rows.fieldnames or "is_remnant" not in rows.fieldnames:
            raise ValueError("В таблице материалов нет колонки is_remnant")
        return sum(
            str(row["is_remnant"]).strip().lower() in {"true", "1"}
            for row in rows
        )


def finalize_materials_draft(draft_path, published_path, approved):
    """Publish a calculated ledger only after explicit operator approval.

    A rejected draft is deliberately left in place for inspection. Publishing
    uses ``os.replace`` so readers never observe a partially written ledger.
    """
    draft = Path(draft_path)
    published = Path(published_path)

    if not approved:
        return draft

    if not draft.is_file():
        raise FileNotFoundError(f"Не найден черновик таблицы материалов: {draft}")

    published.parent.mkdir(parents=True, exist_ok=True)
    os.replace(draft, published)
    return published
