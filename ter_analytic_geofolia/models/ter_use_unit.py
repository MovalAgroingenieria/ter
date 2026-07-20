# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class TerUseUnit(models.Model):
    _inherit = "ter.use_unit"

    geofolia_external_id = fields.Char(
        string="Geofolia ID",
        index=True,
        copy=False,
        groups="ter_analytic_geofolia.group_geofolia_import",
        help="External ID from Geofolia (Field) import. Prevents duplicate imports.",
    )
    fsm_location_id = fields.Many2one(
        comodel_name="fsm.location",
        string="FSM Location",
        index=True,
        ondelete="set null",
        help="Linked Field Service location (1:1 with this use unit).",
    )
    geofolia_code = fields.Char(copy=False)
    geofolia_harvest_year = fields.Integer(copy=False)
    geofolia_crop_name = fields.Char(copy=False)
    geofolia_city = fields.Char(copy=False)

    _sql_constraints = [
        (
            "geofolia_ter_use_unit_external_id_uniq",
            "unique(geofolia_external_id)",
            "A use unit with this Geofolia ID already exists.",
        ),
    ]
