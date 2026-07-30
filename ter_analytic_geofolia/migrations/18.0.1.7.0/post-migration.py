# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import SUPERUSER_ID, api

from odoo.addons.ter_analytic_geofolia.hooks import (
    _ensure_geofolia_default_location,
)


def migrate(cr, version):
    """Ensure each company has the non-deletable default Geofolia location."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    _ensure_geofolia_default_location(env)
