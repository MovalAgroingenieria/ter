# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import UserError


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
        index=True,
        ondelete="restrict",
        help="Linked territory use unit (1:1 with this location).",
    )
    geofolia_default = fields.Boolean(
        string="Geofolia default location",
        copy=False,
        help="Generic location used for all Geofolia work orders. It cannot "
        "be deleted while a company points to it.",
    )

    _sql_constraints = [
        (
            "geofolia_fsm_location_ter_use_unit_uniq",
            "unique(ter_use_unit_id)",
            "A location with this territory use unit already exists.",
        ),
    ]

    @api.ondelete(at_uninstall=False)
    def _unlink_except_geofolia_default(self):
        if any(self.mapped("geofolia_default")):
            raise UserError(
                self.env._(
                    "The default Geofolia location cannot be deleted; it is "
                    "used to create the imported work orders."
                )
            )
