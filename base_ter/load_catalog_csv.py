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


def _module_csv_dir(env: api.Environment) -> Path:
    path = Path(env["ir.module.module"]._get_module_path("base_ter") or "")
    return path / "catalogos_csv"


def _read_csv(path: Path, encoding: str = "utf-8"):
    if not path.exists():
        return []
    with open(path, encoding=encoding, newline="") as f:
        return list(csv.DictReader(f, delimiter=";", quotechar='"'))


def load_catalogs_from_csv(env: api.Environment) -> dict:
    """
    Load all catalog data from CSV files in base_ter/catalogos_csv/.
    Returns a dict with counts: profiles, use_types, attributes, values.
    """
    base_dir = _module_csv_dir(env)
    if not base_dir.exists():
        return {"profiles": 0, "use_types": 0, "attributes": 0, "values": 0}

    Profile = env["ter.profile"].sudo()
    UseType = env["ter.use_type"].sudo()
    Attribute = env["ter.use_type.attribute"].sudo()
    AttributeValue = env["ter.use_type.attribute.value"].sudo()

    # 1) Profiles
    profile_path = base_dir / "ter_profile.csv"
    rows = _read_csv(profile_path)
    for row in rows:
        code = (row.get("alphanum_code") or "").strip()
        if not code:
            continue
        requires = (row.get("requires_total") or "").strip().lower() in (
            "1",
            "true",
            "yes",
            "sí",
            "si",
        )
        is_std = (row.get("is_standard") or "").strip().lower() in (
            "1",
            "true",
            "yes",
            "sí",
            "si",
        )
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
    profile_count = len(rows)

    # 2) Use types: need to create in order of path depth (root first)
    use_type_path = base_dir / "ter_use_type.csv"
    ut_rows = _read_csv(use_type_path)
    path_to_ut = {}  # use_type_path -> record

    # sort by path depth so parent exists when creating child
    def path_depth(r):
        p = (r.get("parent_path") or "").strip()
        n = (r.get("name") or "").strip()
        if not n:
            return -1, ""
        full = f"{p}/{n}" if p else n
        return full.count("/"), full

    ut_rows_sorted = sorted(
        [r for r in ut_rows if (r.get("name") or "").strip()],
        key=path_depth,
    )
    for row in ut_rows_sorted:
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
            rec = existing
            rec.write({"sequence": seq})
        else:
            rec = UseType.create(
                {"name": name, "parent_id": parent_id, "sequence": seq}
            )
        path_to_ut[full_path] = rec
    use_type_count = len(ut_rows_sorted)

    # 3) Attributes
    attr_path = base_dir / "ter_use_type_attribute.csv"
    attr_rows = _read_csv(attr_path)
    attr_cache = {}  # (use_type_path, attribute_name) -> attribute record
    for row in attr_rows:
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
            attr_rec = Attribute.create({"use_type_id": use_type.id, "name": attr_name})
            attr_cache[(ut_path, attr_name)] = attr_rec
    attr_count = len(attr_rows)

    # 4) Attribute values
    val_path = base_dir / "ter_use_type_attribute_value.csv"
    val_rows = _read_csv(val_path)
    for row in val_rows:
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
    value_count = len(val_rows)

    return {
        "profiles": profile_count,
        "use_types": use_type_count,
        "attributes": attr_count,
        "values": value_count,
    }
