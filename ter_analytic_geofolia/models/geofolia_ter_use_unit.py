# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

GEOFOLIA_IMPORT_GROUP = "ter_analytic_geofolia.group_geofolia_import"


class TerUseUnit(models.Model):
    _inherit = "ter.use_unit"

    geofolia_external_id = fields.Char(
        string="Geofolia ID",
        index=True,
        copy=False,
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

    def _strip_geofolia_external_id_if_no_access(self, vals):
        if not vals or "geofolia_external_id" not in vals:
            return vals
        if self.env.user.has_group(GEOFOLIA_IMPORT_GROUP):
            return vals
        if not isinstance(vals, dict):
            return vals
        vals = dict(vals)
        vals.pop("geofolia_external_id", None)
        return vals

    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        vals_list = [
            self._strip_geofolia_external_id_if_no_access(v) for v in vals_list
        ]
        return super().create(vals_list)

    def write(self, vals):
        vals = self._strip_geofolia_external_id_if_no_access(vals)
        return super().write(vals)
