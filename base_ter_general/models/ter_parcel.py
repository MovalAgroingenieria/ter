# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class TerParcel(models.Model):
    _inherit = "ter.parcel"

    mapped_from_base = fields.Boolean(
        readonly=True,
        store=True,
        compute="_compute_mapped_from_base",
        help="Whether this parcel has been mapped from the base entity.",
    )
    last_update = fields.Datetime(
        readonly=True,
        help="Last update timestamp received from the base entity.",
    )
    is_secondary = fields.Boolean(
        default=False,
        help="Whether this parcel is marked as secondary.",
    )
    partner_info = fields.Text(
        readonly=True,
        help="Partner information received from the base entity.",
    )

    @api.depends("is_secondary")
    def _compute_mapped_from_base(self):
        for record in self:
            if record.is_secondary:
                continue
            record.mapped_from_base = False
            record.last_update = False
            record.partner_info = False
