# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
"""Post-migration for base_ter 18.0.1.3.0.

Territorial use units (``ter.use_unit``) now generate their own aerial
image from a dedicated WMS layer that filters by the unit ``name``. That
layer reads the real ``ter_gis_unit`` table, which is keyed by ``unit_id``
and now carries a denormalized ``name`` column (= the unit name).

Everything runs from ``post_init_hook`` on a fresh install, but that hook
does not run when an already-installed ``base_ter`` is merely upgraded.
This migration therefore, on existing databases:

1. Drops the short-lived ``ter_gis_unit_model`` view (an earlier iteration
   used a view; the real table is used now to avoid MapServer feature-id
   inconsistencies).
2. Ensures the ``ter_gis_unit`` table and its ``name`` column exist.
3. Backfills ``ter_gis_unit.name`` from ``ter_use_unit`` for existing rows.
"""

import logging

from odoo import SUPERUSER_ID, api
from odoo.addons.base_ter import hooks as base_ter_hooks

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("DROP VIEW IF EXISTS ter_gis_unit_model")
    base_ter_hooks._ensure_gis_unit_table(env)  # pylint: disable=protected-access
    cr.execute("""
        UPDATE ter_gis_unit tgu
        SET name = tu.name
        FROM ter_use_unit tu
        WHERE tu.id = tgu.unit_id
        AND tgu.name IS DISTINCT FROM tu.name
        """)
    _logger.info(
        "base_ter 18.0.1.3.0 migration: ensured ter_gis_unit.name column and "
        "backfilled %s row(s) for unit-use aerial images.",
        cr.rowcount,
    )
