# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
"""Normalize FSM order stages for multi-company access.

Ensure order stages are shared (``company_id = False``) and defaults exist so
users can read FSM orders across companies when the stage is referenced.
"""

from odoo import SUPERUSER_ID, api

from odoo.addons.ter_analytic_geofolia.hooks import _ensure_fsm_prerequisites


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _ensure_fsm_prerequisites(env)
