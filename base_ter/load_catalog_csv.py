# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

"""
Load territory catalogs (ter.profile, ter.use_type, ter.use_type.attribute,
ter.use_type.attribute.value) from CSV files in the module's catalogs_csv folder.
CSV format: UTF-8, separator ";", quote "\"".
- ter_profile.csv: alphanum_code;requires_total;is_standard;external_id (optional)
- ter_use_type.csv: name;parent_path;sequence;external_id (optional)
- ter_use_type_attribute.csv: use_type_path;attribute_name;external_id (opt.)
- ter_use_type_attribute_value.csv: use_type_path;attribute_name;value_name;
  external_id (opt.)

When external_id is present, ir.model.data is created so
env.ref("base_ter.<external_id>") works (e.g. data_translations_es.json).
"""

from __future__ import annotations

import csv
from pathlib import Path

from odoo import api
from odoo.modules import get_module_path

BOOL_TRUE = ("1", "true", "yes", "sí", "si")
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
    return path / "catalogs_csv"


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
    if not rows:
        return 0
    # simple.model: UNIQUE(name), name = alphanum_code[:size_name]. Dedupe by that.
    size_name = getattr(Profile, "_size_name", None) or getattr(
        Profile, "size_name", 30
    )
    existing_by_name = {r.name: r for r in Profile.search([])}
    to_create_by_key = {}
    external_ids = []
    for row in rows:
        code = (row.get("alphanum_code") or "").strip()
        if not code:
            continue
        name_key = (code or "")[:size_name]
        requires = _parse_bool(row.get("requires_total") or "")
        is_std = _parse_bool(row.get("is_standard") or "")
        external_id = (row.get("external_id") or "").strip()
        rec = existing_by_name.get(name_key)
        if rec:
            rec.write({"requires_total": requires, "is_standard": is_std})
            if external_id:
                external_ids.append((rec.id, external_id))
        else:
            to_create_by_key[name_key] = (
                {
                    "alphanum_code": code,
                    "requires_total": requires,
                    "is_standard": is_std,
                },
                external_id,
            )
    if to_create_by_key:
        to_create_vals = [v[0] for v in to_create_by_key.values()]
        to_create_external = [v[1] for v in to_create_by_key.values()]
        created = Profile.create(to_create_vals)
        for rec, ext_id in zip(created, to_create_external):
            if ext_id:
                external_ids.append((rec.id, ext_id))
    _set_external_ids_batch(env, "ter.profile", external_ids)
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
    if not filtered:
        return 0, path_to_ut
    all_existing = UseType.search([])
    existing_by_key = {
        (r.name, r.parent_id.id if r.parent_id else False): r for r in all_existing
    }
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
    return len(filtered), path_to_ut


def _load_attributes(
    env: api.Environment,
    base_dir: Path,
    path_to_ut: dict,
) -> tuple[int, dict]:
    Attribute = env["ter.use_type.attribute"].sudo()
    path = base_dir / "ter_use_type_attribute.csv"
    rows = _read_csv(path)
    if not rows:
        return 0, {}
    use_type_ids = [r.id for r in path_to_ut.values()]
    existing_map = {
        (r.use_type_id.id, r.name): r
        for r in Attribute.search([("use_type_id", "in", use_type_ids)])
    }
    attr_cache = {}
    to_create_by_key = {}
    external_ids = []
    for row in rows:
        ut_path = (row.get("use_type_path") or "").strip()
        attr_name = (row.get("attribute_name") or "").strip()
        if not ut_path or not attr_name:
            continue
        use_type = path_to_ut.get(ut_path)
        if not use_type:
            continue
        key = (use_type.id, attr_name)
        rec = existing_map.get(key)
        if rec:
            attr_cache[(ut_path, attr_name)] = rec
            ext_id = (row.get("external_id") or "").strip()
            if ext_id:
                external_ids.append((rec.id, ext_id))
        else:
            to_create_by_key[key] = (
                {"use_type_id": use_type.id, "name": attr_name},
                (ut_path, attr_name, (row.get("external_id") or "").strip()),
            )
    to_create = [v[0] for v in to_create_by_key.values()]
    to_create_meta = [v[1] for v in to_create_by_key.values()]
    for i in range(0, len(to_create), BATCH_SIZE):
        batch = to_create[i : i + BATCH_SIZE]
        meta_batch = to_create_meta[i : i + BATCH_SIZE]
        created = Attribute.create(batch)
        for rec, (ut_path, attr_name, ext_id) in zip(created, meta_batch):
            existing_map[(rec.use_type_id.id, rec.name)] = rec
            attr_cache[(ut_path, attr_name)] = rec
            if ext_id:
                external_ids.append((rec.id, ext_id))
    _set_external_ids_batch(env, "ter.use_type.attribute", external_ids)
    return len(rows), attr_cache


def _resolve_attr_for_row(attr_cache, path_to_ut, Attribute, ut_path, attr_name):
    """Get attribute record from cache or search; update cache if found."""
    attr_rec = attr_cache.get((ut_path, attr_name))
    if attr_rec:
        return attr_rec
    use_type = path_to_ut.get(ut_path)
    if not use_type:
        return None
    attr_rec = Attribute.search(
        [
            ("use_type_id", "=", use_type.id),
            ("name", "=", attr_name),
        ],
        limit=1,
    )
    if attr_rec:
        attr_cache[(ut_path, attr_name)] = attr_rec
    return attr_rec


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
    if not rows:
        return 0
    attr_ids = list({r.id for r in attr_cache.values()})
    existing_map = {
        (r.attribute_id.id, r.name): r
        for r in AttributeValue.search([("attribute_id", "in", attr_ids)])
    }
    to_create = []
    to_create_external = []
    external_ids = []
    to_create_by_key = {}
    for row in rows:
        ut_path = (row.get("use_type_path") or "").strip()
        attr_name = (row.get("attribute_name") or "").strip()
        val_name = (row.get("value_name") or "").strip()
        if not ut_path or not attr_name or not val_name:
            continue
        attr_rec = _resolve_attr_for_row(
            attr_cache, path_to_ut, Attribute, ut_path, attr_name
        )
        if not attr_rec:
            continue
        key = (attr_rec.id, val_name)
        if key in existing_map:
            rec = existing_map[key]
            ext_id = (row.get("external_id") or "").strip()
            if ext_id:
                external_ids.append((rec.id, ext_id))
        else:
            to_create_by_key[key] = (
                {"attribute_id": attr_rec.id, "name": val_name},
                (row.get("external_id") or "").strip(),
            )
    to_create = [v[0] for v in to_create_by_key.values()]
    to_create_external = [v[1] for v in to_create_by_key.values()]
    for i in range(0, len(to_create), BATCH_SIZE):
        batch = to_create[i : i + BATCH_SIZE]
        ext_batch = to_create_external[i : i + BATCH_SIZE]
        created = AttributeValue.create(batch)
        for rec, ext_id in zip(created, ext_batch):
            existing_map[(rec.attribute_id.id, rec.name)] = rec
            if ext_id:
                external_ids.append((rec.id, ext_id))
    _set_external_ids_batch(env, "ter.use_type.attribute.value", external_ids)
    return len(rows)


def load_catalogs_from_csv(env: api.Environment) -> dict:
    """
    Load all catalog data from CSV files in base_ter/catalogs_csv/.
    Returns a dict with counts: profiles, use_types, attributes, values.
    Uses preloaded lookups and batch creates for speed.
    """
    base_dir = _module_csv_dir(env)
    if not base_dir.exists():
        return {"profiles": 0, "use_types": 0, "attributes": 0, "values": 0}
    env = env(context=dict(env.context, tracking_disable=True))
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
