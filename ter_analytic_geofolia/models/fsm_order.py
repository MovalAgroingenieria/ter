# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import UserError


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    _geofolia_lock_field = "from_geofolia"
    _geofolia_protected_fields = ("worked_surface",)

    product_usage_ids = fields.One2many(
        comodel_name="fsm.order.product.usage",
        inverse_name="fsm_order_id",
        string="Products Used",
    )
    equipment_usage_ids = fields.One2many(
        comodel_name="fsm.order.equipment.usage",
        inverse_name="fsm_order_id",
        string="Equipment Used",
    )
    person_usage_ids = fields.One2many(
        comodel_name="fsm.order.person.usage",
        inverse_name="fsm_order_id",
        string="Workers",
    )
    harvest_usage_ids = fields.One2many(
        comodel_name="fsm.order.harvest.usage",
        inverse_name="fsm_order_id",
        string="Harvested Goods",
    )
    worked_unit_ids = fields.One2many(
        comodel_name="fsm.order.worked.unit",
        inverse_name="fsm_order_id",
        string="Worked Crop Units",
    )
    worked_surface = fields.Float(
        digits=(16, 2),
        help="Total worked surface in m² (from Geofolia CropZones).",
    )
    from_geofolia = fields.Boolean(
        default=False,
        copy=False,
        help="Set when the order was created by the Geofolia import.",
    )
    geofolia_activity_id = fields.Char(
        string="Geofolia Activity ID",
        index=True,
        copy=False,
        help="External ID of the Geofolia activity that created this order. "
        "Used to re-sync the order on re-import instead of duplicating it.",
    )
    product_usage_count = fields.Integer(
        compute="_compute_usage_counts",
    )
    equipment_usage_count = fields.Integer(
        compute="_compute_usage_counts",
    )
    person_usage_count = fields.Integer(
        compute="_compute_usage_counts",
    )
    harvest_usage_count = fields.Integer(
        compute="_compute_usage_counts",
    )
    worked_unit_count = fields.Integer(
        compute="_compute_usage_counts",
    )

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

    def unlink(self):
        """Explain why a work order cannot be deleted.

        Field Service only allows deleting orders in the default stage.
        Orders imported from Geofolia are marked as executed (completed),
        so we replace the generic core error with an actionable message.
        The base ``fsm.order.unlink`` raises before ``super()`` runs, so an
        ``@api.ondelete`` hook would never fire; overriding ``unlink`` is the
        only way to surface a clearer message.
        """
        blocked = self.filtered(lambda order: not order.can_unlink())
        if blocked:
            default_stage = self._default_stage_id()
            details = "\n".join(
                self.env._(
                    "- %(name)s (current stage: %(stage)s)",
                    name=order.name or "",
                    stage=order.stage_id.name or "",
                )
                for order in blocked
            )
            raise UserError(  # pylint: disable=no-raise-unlink
                self.env._(
                    "A work order can only be deleted while it is in the "
                    '"%(stage)s" stage. The following orders are in another '
                    "stage:\n%(details)s\n\n"
                    "Work orders imported from Geofolia are created as already "
                    "executed (completed). To delete one, move it back to the "
                    '"%(stage)s" stage first.',
                    stage=default_stage.name or "",
                    details=details,
                )
            )
        return super().unlink()

    @api.depends(
        "product_usage_ids",
        "equipment_usage_ids",
        "person_usage_ids",
        "harvest_usage_ids",
        "worked_unit_ids",
    )
    def _compute_usage_counts(self):
        for record in self:
            record.product_usage_count = len(record.product_usage_ids)
            record.equipment_usage_count = len(record.equipment_usage_ids)
            record.person_usage_count = len(record.person_usage_ids)
            record.harvest_usage_count = len(record.harvest_usage_ids)
            record.worked_unit_count = len(record.worked_unit_ids)

    def action_view_product_usage(self):
        """Open product usage tree for this order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Products Used"),
            "res_model": "fsm.order.product.usage",
            "view_mode": "list,form",
            "domain": [("fsm_order_id", "=", self.id)],
            "context": {"default_fsm_order_id": self.id},
        }

    def action_view_equipment_usage(self):
        """Open equipment usage tree for this order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Equipment Used"),
            "res_model": "fsm.order.equipment.usage",
            "view_mode": "list,form",
            "domain": [("fsm_order_id", "=", self.id)],
            "context": {"default_fsm_order_id": self.id},
        }

    def action_view_person_usage(self):
        """Open person usage tree for this order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Workers"),
            "res_model": "fsm.order.person.usage",
            "view_mode": "list,form",
            "domain": [("fsm_order_id", "=", self.id)],
            "context": {"default_fsm_order_id": self.id},
        }

    def action_view_harvest_usage(self):
        """Open harvest usage tree for this order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Harvested Goods"),
            "res_model": "fsm.order.harvest.usage",
            "view_mode": "list,form",
            "domain": [("fsm_order_id", "=", self.id)],
            "context": {"default_fsm_order_id": self.id},
        }

    def action_view_worked_units(self):
        """Open worked crop-unit tree for this order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Worked Crop Units"),
            "res_model": "fsm.order.worked.unit",
            "view_mode": "list,form",
            "domain": [("fsm_order_id", "=", self.id)],
            "context": {"default_fsm_order_id": self.id},
        }
