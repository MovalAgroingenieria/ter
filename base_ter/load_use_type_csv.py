# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

"""
Load ter.use_type records from CSV files in base_ter/data/catalogs_csv/.
CSV format: UTF-8, separator ";", quote "\"".
- ter_use_type.csv: name;parent_path;sequence;external_id (optional)

When external_id is present, ir.model.data is created so
env.ref("base_ter.<external_id>") works.
"""

from __future__ import annotations

import csv
from pathlib import Path

from odoo import api
from odoo.modules import get_module_path

MODULE_NAME = "base_ter"
BATCH_SIZE = 500


def _set_external_ids_batch(
    env: api.Environment,
    model_name: str,
    items: list[tuple[int, str]],
) -> None:
    """Set ir.model.data for many records (one search, then create/update)."""
    if not items:
        return
    names = list({name for _, name in items if name})
    if not names:
        return
    IrModelData = env["ir.model.data"].sudo()
    existing_map = {}
    for rec in IrModelData.search(
        [
            ("module", "=", MODULE_NAME),
            ("model", "=", model_name),
            ("name", "in", names),
        ]
    ):
        existing_map[rec.name] = rec
    to_create = []
    for res_id, name in items:
        if not name:
            continue
        name = name.strip()
        if not name:
            continue
        existing = existing_map.get(name)
        if existing:
            if existing.res_id != res_id:
                existing.write({"res_id": res_id})
        else:
            to_create.append(
                {
                    "module": MODULE_NAME,
                    "name": name,
                    "model": model_name,
                    "res_id": res_id,
                    "noupdate": True,
                }
            )
            existing_map[name] = None
    if to_create:
        IrModelData.create(to_create)


def _module_csv_dir(_env: api.Environment) -> Path:
    path = Path(get_module_path(MODULE_NAME, display_warning=False) or "")
    return path / "data" / "catalogs_csv"


def _read_csv(path: Path, encoding: str = "utf-8"):
    if not path.exists():
        return []
    with open(path, encoding=encoding, newline="") as f:
        return list(csv.DictReader(f, delimiter=";", quotechar='"'))


def _use_type_path_depth(row: dict) -> tuple:
    parent_path = (row.get("parent_path") or "").strip()
    name = (row.get("name") or "").strip()
    if not name:
        return -1, ""
    full = f"{parent_path}/{name}" if parent_path else name
    return full.count("/"), full


def load_use_types_from_csv(env: api.Environment) -> dict:
    """
    Load ter.use_type records from CSV in base_ter/data/catalogs_csv/.
    Returns a dict with count: use_types.
    """
    base_dir = _module_csv_dir(env)
    if not base_dir.exists():
        return {"use_types": 0}
    env = env(context=dict(env.context, tracking_disable=True))
    UseType = env["ter.use_type"].sudo()
    path = base_dir / "ter_use_type.csv"
    rows = _read_csv(path)
    filtered = [r for r in rows if (r.get("name") or "").strip()]
    if not filtered:
        return {"use_types": 0}
    all_existing = UseType.search([])
    existing_by_key = {
        (r.name, r.parent_id.id if r.parent_id else False): r for r in all_existing
    }
    path_to_ut: dict = {}
    external_ids = []
    for row in sorted(filtered, key=_use_type_path_depth):
        name = (row.get("name") or "").strip()
        parent_path = (row.get("parent_path") or "").strip()
        try:
            seq = int((row.get("sequence") or "10").strip())
        except ValueError:
            seq = 10
        full_path = f"{parent_path}/{name}" if parent_path else name
        parent_id = False
        if parent_path:
            parent = path_to_ut.get(parent_path)
            if parent:
                parent_id = parent.id
        key = (name, parent_id)
        rec = existing_by_key.get(key)
        if rec:
            rec.write({"sequence": seq})
        else:
            rec = UseType.create(
                {"name": name, "parent_id": parent_id, "sequence": seq}
            )
            existing_by_key[key] = rec
        path_to_ut[full_path] = rec
        external_id = (row.get("external_id") or "").strip()
        if external_id:
            external_ids.append((rec.id, external_id))
    _set_external_ids_batch(env, "ter.use_type", external_ids)
    return {"use_types": len(filtered)}
