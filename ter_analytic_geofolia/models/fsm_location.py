# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class FSMLocation(models.Model):
    _inherit = "fsm.location"

    geofolia_external_id = fields.Char(
        related="ter_use_unit_id.geofolia_external_id",
        string="Geofolia ID",
        readonly=True,
        help="Same as ter.use_unit.geofolia_external_id (1:1 link).",
    )
    ter_use_unit_id = fields.Many2one(
        comodel_name="ter.use_unit",
        string="Territory Use Unit",
        required=True,
        index=True,
        ondelete="restrict",
        help="Linked territory use unit (1:1 with this location).",
    )

    _sql_constraints = [
        (
            "geofolia_fsm_location_ter_use_unit_uniq",
            "unique(ter_use_unit_id)",
            "A location with this territory use unit already exists.",
        ),
    ]
