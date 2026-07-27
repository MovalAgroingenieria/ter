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
