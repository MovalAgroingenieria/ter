# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    geofolia_equipment_id = fields.Char(
        string="Geofolia Equipment ID",
        index=True,
        copy=False,
        help="Unique identifier from Geofolia (EquipmentId). Idempotency key.",
    )
