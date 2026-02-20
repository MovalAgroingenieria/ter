# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

"""
Load territory catalogs (ter.profile, ter.use_type, ter.use_type.attribute,
ter.use_type.attribute.value) from CSV files in the module's catalogos_csv folder.
CSV format: UTF-8, separator ";", quote "\"".
- ter_profile.csv: alphanum_code;requires_total;is_standard
- ter_use_type.csv: name;parent_path;sequence (parent_path empty for root)
- ter_use_type_attribute.csv: use_type_path;attribute_name
- ter_use_type_attribute_value.csv: use_type_path;attribute_name;value_name
"""

from __future__ import annotations

import csv
from pathlib import Path

from odoo import api

BOOL_TRUE = ("1", "true", "yes", "sí", "si")


def _module_csv_dir(env: api.Environment) -> Path:
    path = Path(env["ir.module.module"]._get_module_path("base_ter") or "")
    return path / "catalogos_csv"


def _read_csv(path: Path, encoding: str = "utf-8"):
    if not path.exists():
        return []
    with open(path, encoding=encoding, newline="") as f:
        return list(csv.DictReader(f, delimiter=";", quotechar='"'))


def _parse_bool(val: str) -> bool:
    return (val or "").strip().lower() in BOOL_TRUE


def _load_profiles(env: api.Environment, base_dir: Path) -> int:
    Profile = env["ter.profile"].sudo()
    path = base_dir / "ter_profile.csv"
    rows = _read_csv(path)
    for row in rows:
        code = (row.get("alphanum_code") or "").strip()
        if not code:
            continue
        requires = _parse_bool(row.get("requires_total") or "")
        is_std = _parse_bool(row.get("is_standard") or "")
        existing = Profile.search([("alphanum_code", "=", code)], limit=1)
        if existing:
            existing.write({"requires_total": requires, "is_standard": is_std})
        else:
            Profile.create(
                {
                    "alphanum_code": code,
                    "requires_total": requires,
                    "is_standard": is_std,
                }
            )
    return len(rows)


def _use_type_path_depth(row: dict) -> tuple:
    parent_path = (row.get("parent_path") or "").strip()
    name = (row.get("name") or "").strip()
    if not name:
        return -1, ""
    full = f"{parent_path}/{name}" if parent_path else name
    return full.count("/"), full


def _load_use_types(env: api.Environment, base_dir: Path) -> tuple[int, dict]:
    UseType = env["ter.use_type"].sudo()
    path = base_dir / "ter_use_type.csv"
    rows = _read_csv(path)
    path_to_ut = {}
    filtered = [r for r in rows if (r.get("name") or "").strip()]
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
        existing = UseType.search(
            [("name", "=", name), ("parent_id", "=", parent_id)],
            limit=1,
        )
        if existing:
            existing.write({"sequence": seq})
            rec = existing
        else:
            rec = UseType.create(
                {"name": name, "parent_id": parent_id, "sequence": seq}
            )
        path_to_ut[full_path] = rec
    return len(filtered), path_to_ut


def _load_attributes(
    env: api.Environment,
    base_dir: Path,
    path_to_ut: dict,
) -> tuple[int, dict]:
    Attribute = env["ter.use_type.attribute"].sudo()
    path = base_dir / "ter_use_type_attribute.csv"
    rows = _read_csv(path)
    attr_cache = {}
    for row in rows:
        ut_path = (row.get("use_type_path") or "").strip()
        attr_name = (row.get("attribute_name") or "").strip()
        if not ut_path or not attr_name:
            continue
        use_type = path_to_ut.get(ut_path)
        if not use_type:
            continue
        existing = Attribute.search(
            [
                ("use_type_id", "=", use_type.id),
                ("name", "=", attr_name),
            ],
            limit=1,
        )
        if existing:
            attr_cache[(ut_path, attr_name)] = existing
        else:
            rec = Attribute.create({"use_type_id": use_type.id, "name": attr_name})
            attr_cache[(ut_path, attr_name)] = rec
    return len(rows), attr_cache


def _load_attribute_values(
    env: api.Environment,
    base_dir: Path,
    path_to_ut: dict,
    attr_cache: dict,
) -> int:
    Attribute = env["ter.use_type.attribute"].sudo()
    AttributeValue = env["ter.use_type.attribute.value"].sudo()
    path = base_dir / "ter_use_type_attribute_value.csv"
    rows = _read_csv(path)
    for row in rows:
        ut_path = (row.get("use_type_path") or "").strip()
        attr_name = (row.get("attribute_name") or "").strip()
        val_name = (row.get("value_name") or "").strip()
        if not ut_path or not attr_name or not val_name:
            continue
        attr_rec = attr_cache.get((ut_path, attr_name))
        if not attr_rec:
            use_type = path_to_ut.get(ut_path)
            if use_type:
                attr_rec = Attribute.search(
                    [
                        ("use_type_id", "=", use_type.id),
                        ("name", "=", attr_name),
                    ],
                    limit=1,
                )
                if attr_rec:
                    attr_cache[(ut_path, attr_name)] = attr_rec
        if not attr_rec:
            continue
        existing = AttributeValue.search(
            [
                ("attribute_id", "=", attr_rec.id),
                ("name", "=", val_name),
            ],
            limit=1,
        )
        if not existing:
            AttributeValue.create({"attribute_id": attr_rec.id, "name": val_name})
    return len(rows)


def load_catalogs_from_csv(env: api.Environment) -> dict:
    """
    Load all catalog data from CSV files in base_ter/catalogos_csv/.
    Returns a dict with counts: profiles, use_types, attributes, values.
    """
    base_dir = _module_csv_dir(env)
    if not base_dir.exists():
        return {"profiles": 0, "use_types": 0, "attributes": 0, "values": 0}

    profile_count = _load_profiles(env, base_dir)
    use_type_count, path_to_ut = _load_use_types(env, base_dir)
    attr_count, attr_cache = _load_attributes(env, base_dir, path_to_ut)
    value_count = _load_attribute_values(env, base_dir, path_to_ut, attr_cache)

    return {
        "profiles": profile_count,
        "use_types": use_type_count,
        "attributes": attr_count,
        "values": value_count,
    }
