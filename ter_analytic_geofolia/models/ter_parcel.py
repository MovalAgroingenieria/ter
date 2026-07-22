# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class TerParcel(models.Model):
    _inherit = "ter.parcel"

    geofolia_created = fields.Boolean(
        string="Created from Geofolia",
        index=True,
        copy=False,
        help="Set when the parcel was auto-created during a Geofolia Fields import.",
    )
