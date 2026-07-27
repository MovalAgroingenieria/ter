# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import UserError


class TerUseUnit(models.Model):
    _inherit = "ter.use_unit"

    _geofolia_lock_field = "geofolia_external_id"
    _geofolia_protected_fields = (
        "geofolia_external_id",
        "geofolia_code",
        "geofolia_harvest_year",
        "geofolia_crop_name",
        "geofolia_city",
    )

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

    fsm_order_count = fields.Integer(
        compute="_compute_fsm_order_count",
    )

    _sql_constraints = [
        (
            "geofolia_ter_use_unit_external_id_uniq",
            "unique(geofolia_external_id)",
            "A use unit with this Geofolia ID already exists.",
        ),
    ]

    def write(self, vals):
        protected = [name for name in self._geofolia_protected_fields if name in vals]
        if protected and not self.env.context.get("geofolia_sync"):
            locked = self.sudo().filtered(self._geofolia_lock_field)
            if locked:
                raise UserError(
                    self.env._(
                        "These fields come from Geofolia and can only be "
                        "updated by re-importing from Geofolia: %(fields)s",
                        fields=", ".join(sorted(protected)),
                    )
                )
        return super().write(vals)

    @api.depends("fsm_location_id")
    def _compute_fsm_order_count(self):
        order_obj = self.env["fsm.order"]
        for record in self:
            if record.fsm_location_id:
                record.fsm_order_count = order_obj.search_count(
                    [("location_id", "=", record.fsm_location_id.id)]
                )
            else:
                record.fsm_order_count = 0

    def action_view_fsm_orders(self):
        """Open the work orders (fsm.order) linked to this use unit."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Work Orders"),
            "res_model": "fsm.order",
            "view_mode": "list,form,kanban",
            "domain": [("location_id", "=", self.fsm_location_id.id)],
            "context": {"default_location_id": self.fsm_location_id.id},
        }
