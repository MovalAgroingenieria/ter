# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
"""Backfill from_geofolia markers and ensure FSM prerequisites.

- Mark existing FSM usage lines and orders that originate from Geofolia so the
  new write-protection locks them (only re-import can edit their data).
- Ensure at least one default FSM order stage and a team exist, so creating a
  work order no longer fails with "You must create an FSM order stage first.".
"""

from odoo import SUPERUSER_ID, api

from odoo.addons.ter_analytic_geofolia.hooks import _ensure_fsm_prerequisites


def migrate(cr, version):
    # Every previously imported usage line came from Geofolia.
    cr.execute(
        "UPDATE fsm_order_person_usage SET from_geofolia = true "
        "WHERE from_geofolia IS NOT TRUE"
    )
    cr.execute(
        "UPDATE fsm_order_product_usage SET from_geofolia = true "
        "WHERE from_geofolia IS NOT TRUE"
    )
    cr.execute(
        "UPDATE fsm_order_equipment_usage SET from_geofolia = true "
        "WHERE from_geofolia IS NOT TRUE"
    )
    # Orders referenced by an imported activity line are Geofolia orders.
    cr.execute("""
        UPDATE fsm_order o
        SET from_geofolia = true
        WHERE o.from_geofolia IS NOT TRUE
          AND EXISTS (
              SELECT 1 FROM geofolia_import_activity_line al
              WHERE al.fsm_order_id = o.id
          )
        """)
    env = api.Environment(cr, SUPERUSER_ID, {})
    _ensure_fsm_prerequisites(env)
