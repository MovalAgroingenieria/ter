# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""Load territory catalogs from CSV on upgrade (and install via post_init_hook)."""

import logging

import odoo
from odoo import api

_logger = logging.getLogger(__name__)


def migrate(cr, _version):
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    try:
        # pylint: disable=import-outside-toplevel
        from odoo.addons.base_ter_data_import.load_catalog_csv import load_catalogs_from_csv

        counts = load_catalogs_from_csv(env)
        _logger.info(
            "base_ter: loaded catalogs from CSV: %d profiles, %d use types, "
            "%d attributes, %d values",
            counts["profiles"],
            counts["use_types"],
            counts["attributes"],
            counts["values"],
        )
    except Exception as e:
        _logger.warning(
            "base_ter: could not load catalogs from CSV "
            "(install base_ter_data_import or run Import wizard if needed): %s",
            e,
        )
