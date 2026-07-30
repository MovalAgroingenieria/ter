# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import SUPERUSER_ID, api

from odoo.addons.ter_analytic_geofolia.hooks import (
    _ensure_geofolia_default_location,
)


def migrate(cr, version):
    """Remove the per-parcel Geofolia locations.

    Locations are no longer created per territorial unit: every imported work
    order uses the company's single default Geofolia location. This migration
    repoints existing Geofolia work orders to that default location and then
    deletes the now-unused per-parcel locations.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    _ensure_geofolia_default_location(env)
    location_obj = env["fsm.location"].sudo()
    per_unit_locs = location_obj.search(
        [
            ("geofolia_default", "=", False),
            ("ter_use_unit_id", "!=", False),
        ]
    ).filtered(lambda loc: loc.ter_use_unit_id.geofolia_external_id)
    if not per_unit_locs:
        return
    order_obj = env["fsm.order"].sudo()
    orders = order_obj.search([("location_id", "in", per_unit_locs.ids)])
    for order in orders:
        company = order.company_id or env.company
        default_loc = company.geofolia_default_fsm_location_id
        if default_loc:
            order.with_context(geofolia_sync=True).location_id = default_loc.id
    env["fsm.location.person"].sudo().search(
        [("location_id", "in", per_unit_locs.ids)]
    ).unlink()
    for loc in per_unit_locs:
        try:
            with cr.savepoint():
                loc.unlink()
        except Exception:  # noqa: BLE001  # pylint: disable=broad-except
            continue
