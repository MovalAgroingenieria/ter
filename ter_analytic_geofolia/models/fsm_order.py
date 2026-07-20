# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class FSMOrder(models.Model):
    _inherit = "fsm.order"

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
    worked_surface = fields.Float(
        digits=(16, 2),
        help="Total worked surface in m² (from Geofolia CropZones).",
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

    @api.depends("product_usage_ids", "equipment_usage_ids", "person_usage_ids")
    def _compute_usage_counts(self):
        for record in self:
            record.product_usage_count = len(record.product_usage_ids)
            record.equipment_usage_count = len(record.equipment_usage_ids)
            record.person_usage_count = len(record.person_usage_ids)

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

    @api.depends("template_id")
    def _compute_order_activity_ids(self):
        result = super()._compute_order_activity_ids()
        for record in self:
            if not record.template_id:
                record.order_activity_ids = self.env["fsm.activity"].search(
                    [("fsm_order_id", "=", record.id)]
                )
        return result
