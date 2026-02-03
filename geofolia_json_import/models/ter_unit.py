# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class TerUnit(models.Model):
    _inherit = "ter.unit"

    geofolia_uid = fields.Char(
        string="Geofolia UID",
        index=True,
        copy=False,
        help="Unique identifier from Geofolia Field/Plot for matching.",
    )

    _sql_constraints = [
        (
            "ter_unit_geofolia_uid_uniq",
            "unique(geofolia_uid)",
            "Geofolia UID must be unique.",
        ),
    ]

