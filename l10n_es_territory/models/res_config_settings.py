# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cadastre_gis_import_enabled = fields.Boolean(
        related="company_id.cadastre_gis_import_enabled",
        readonly=False,
    )
    cadastre_match_min_intersection = fields.Float(
        related="company_id.cadastre_match_min_intersection",
        readonly=False,
    )
