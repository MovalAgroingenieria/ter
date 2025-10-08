# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api


class TerParcel(models.Model):
    _name = 'ter.parcel'
    _inherit = ['ter.parcel']

    mapped_from_base = fields.Boolean(
        string="Mapped",
        default=False,
        readonly=True,
        help="Indicates if this parcel has been mapped from base entity.",
    )

    last_update = fields.Datetime(
        default=False,
        readonly=True,
        help="Date of the last update from with general instance.",
    )

    is_secondary = fields.Boolean(
        string="Secondary",
        default=False,
        readonly=True,
        help="Indicates if this parcel is a secondary parcel.",
    )

    partner_info = fields.Text(
        string="Partner Information",
        readonly=True,
        help="Information about the partner associated with this parcel.",
    )

    @api.depends('is_secondary')
    def _compute_mapped_from_base(self):
        for record in self:
            if not record.is_secondary:
                record.mapped_from_base = False
                record.last_update = False
                record.partner_info = False
