# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    geofolia_partner_id = fields.Char(
        string="Geofolia Partner ID",
        index=True,
        copy=False,
        help="Unique identifier from Geofolia (PartnerId).",
    )
    geofolia_registration_number = fields.Char(
        string="Geofolia Registration Number",
    )
    geofolia_national_identification_code = fields.Char(
        string="Geofolia National Identification Code",
    )
