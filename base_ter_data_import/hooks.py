# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from __future__ import annotations

import json
import logging
from pathlib import Path

from odoo import api

from .load_catalog_csv import load_catalogs_from_csv as _load_catalogs_from_csv_impl

_logger = logging.getLogger(__name__)

CATALOG_PARAM = "base_ter_data_import.show_catalog_import_wizard"


def _load_catalogs_from_csv(env: api.Environment) -> None:
    """Load territory catalogs from CSV files bundled in this module."""
    try:
        counts = _load_catalogs_from_csv_impl(env)
        _logger.info(
            "base_ter_data_import: loaded catalogs from CSV: "
            "%d profiles, %d use types, %d attributes, %d values",
            counts["profiles"],
            counts["use_types"],
            counts["attributes"],
            counts["values"],
        )
    except Exception as exc:
        _logger.warning(
            "base_ter_data_import: could not load territory catalogs from CSV: %s",
            exc,
        )


def _set_show_catalog_import_wizard(env: api.Environment) -> None:
    """Set flag so the Settings page prompts the user to run the import wizard."""
    env["ir.config_parameter"].sudo().set_param(CATALOG_PARAM, "True")
    todo = env.ref(
        "base_ter_data_import.config_todo_import_catalog_csv",
        raise_if_not_found=False,
    )
    if todo:
        todo.sudo().write({"state": "open"})


def _load_data_translations_es(env: api.Environment) -> None:
    """Load es_ES translations for all translatable catalog data."""
    path = Path(__file__).resolve().parent / "data" / "data_translations_es.json"
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for model_name, block in data.items():
        field_name = block.get("field", "name")
        entries = block.get("entries", {})
        for xmlid, es_value in entries.items():
            try:
                record = env.ref(xmlid, raise_if_not_found=False)
                if record and record._name == model_name:
                    record.sudo().update_field_translations(
                        field_name, {"es_ES": es_value}
                    )
            except Exception:
                continue


def post_init_hook(env: api.Environment) -> None:
    _load_catalogs_from_csv(env)
    _set_show_catalog_import_wizard(env)
    _load_data_translations_es(env)
