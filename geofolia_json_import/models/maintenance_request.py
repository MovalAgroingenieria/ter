# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    geofolia_action_id = fields.Char(
        string="Geofolia Action ID",
        index=True,
        copy=False,
        help="Unique identifier from Geofolia Activity (ActionId). Idempotency key.",
    )
