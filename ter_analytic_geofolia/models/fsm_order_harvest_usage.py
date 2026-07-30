# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class FsmOrderHarvestUsage(models.Model):
    """Harvested good produced during a field service order.

    Each record represents one harvested product (grain, forage…) obtained
    during a harvesting activity imported from Geofolia.  Quantities and
    units come from the JSON ``ActionHarvests`` block.
    """

    _name = "fsm.order.harvest.usage"
    _description = "FSM Order Harvest Usage"
    _inherit = "fsm.order.usage.mixin"

    _geofolia_protected_fields = (
        "name",
        "quantity",
        "uom_name",
        "geofolia_harvest_id",
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        ondelete="set null",
        index=True,
    )
    name = fields.Char(
        required=True,
        help="Harvested good name from Geofolia.",
    )
    quantity = fields.Float(digits=(16, 4))
    uom_name = fields.Char(
        string="Unit",
        help="Unit symbol from Geofolia (Kg, T…).",
    )
    geofolia_harvest_id = fields.Char(
        string="Geofolia Harvest ID",
        index=True,
    )

    @api.depends("name", "quantity", "uom_name")
    def _compute_display_name(self):
        for record in self:
            parts = [record.name or ""]
            if record.quantity:
                parts.append("%.2f" % record.quantity)
            if record.uom_name:
                parts.append(record.uom_name)
            record.display_name = " — ".join(parts)
