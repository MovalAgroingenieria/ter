# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
"""Ensure FSM prerequisites exist for every company on existing installs.

Multi-company databases installed before this version only got a single FSM
team (for the install company).  Importing Geofolia under another company then
failed with "You must create an FSM team first.".  Re-run the prerequisite
setup so every company has its own team and shared default order stages exist.
"""

from odoo import SUPERUSER_ID, api

from odoo.addons.ter_analytic_geofolia.hooks import _ensure_fsm_prerequisites


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _ensure_fsm_prerequisites(env)
