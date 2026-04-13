# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class FsmOrderProductUsage(models.Model):
    """Product/supply consumed during a field service order.

    Each record represents one product (fertilizer, pesticide, seed…)
    applied during an activity imported from Geofolia.  Quantities and
    units come from the JSON ``ProductIds`` block.
    """

    _name = "fsm.order.product.usage"
    _description = "FSM Order Product Usage"
    _order = "sequence, id"

    fsm_order_id = fields.Many2one(
        comodel_name="fsm.order",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        comodel_name="product.product",
        ondelete="set null",
        index=True,
    )
    name = fields.Char(
        required=True,
        help="Product/supply name from Geofolia.",
    )
    quantity = fields.Float(digits=(16, 4))
    uom_name = fields.Char(
        string="Unit",
        help="Unit symbol from Geofolia (L, Kg…).",
    )
    geofolia_supply_id = fields.Char(
        string="Geofolia Supply ID",
        index=True,
    )
    geofolia_recognition_id = fields.Char(
        string="Geofolia Recognition ID",
    )

    location_id = fields.Many2one(
        related="fsm_order_id.location_id",
        store=True,
    )
    partner_id = fields.Many2one(
        related="fsm_order_id.location_id.owner_id",
        store=True,
        string="Owner",
    )

    @api.depends("name", "quantity", "uom_name")
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.name or ""]
            if rec.quantity:
                parts.append("%.2f" % rec.quantity)
            if rec.uom_name:
                parts.append(rec.uom_name)
            rec.display_name = " — ".join(parts)
