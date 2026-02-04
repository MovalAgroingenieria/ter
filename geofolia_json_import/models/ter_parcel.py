# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class TerParcel(models.Model):
    _inherit = "ter.parcel"

    geofolia_farm_identification_code = fields.Char(
        string="Geofolia Farm Identification Code",
        index=True,
        copy=False,
        help="Farm or plot identifier from Geofolia (FarmIdentificationCode, Field Code). "
        "Used for matching ter.unit to parcels when importing.",
    )
