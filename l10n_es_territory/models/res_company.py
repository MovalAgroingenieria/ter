# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cadastre_gis_import_enabled = fields.Boolean(
        string="Enable Cadastre GIS import",
        default=True,
        help="Allow importing parcel geometries from the Cadastre WFS service.",
    )
    cadastre_match_min_intersection = fields.Float(
        string="Cadastre match minimum overlap (%)",
        default=50.0,
        help="Minimum intersection percentage for a cadastral parcel to be "
        "proposed as a suggested match during the background cadastre scan.",
    )
