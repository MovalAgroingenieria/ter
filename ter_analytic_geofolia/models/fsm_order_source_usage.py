import json

from odoo import api, fields, models


class FsmOrderSourceUsage(models.Model):
    _name = "fsm.order.source.usage"
    _description = "Geofolia Original Consumption"
    _order = "fsm_order_id, kind, source_index, id"

    fsm_order_id = fields.Many2one(
        "fsm.order", required=True, index=True, ondelete="cascade"
    )
    company_id = fields.Many2one(
        related="fsm_order_id.company_id", store=True, index=True
    )
    source_key = fields.Char(required=True)
    source_index = fields.Integer()
    kind = fields.Selection(
        [
            ("product", "Material"),
            ("person", "Worker"),
            ("equipment", "Machinery"),
            ("harvest", "Harvest"),
        ],
        required=True,
        index=True,
    )
    name = fields.Char()
    external_id = fields.Char(index=True)
    recognition_id = fields.Char(index=True)
    plot_id = fields.Char(index=True)
    use_unit_id = fields.Many2one("ter.use_unit", index=True, ondelete="set null")
    parcel_id = fields.Many2one(related="use_unit_id.parcel_id", store=True, index=True)
    quantity = fields.Float(digits=(32, 10))
    uom_name = fields.Char()
    hours = fields.Float(digits=(16, 8))
    batch_number = fields.Char()
    rn_target_code = fields.Char()
    link_state = fields.Selection(
        [
            ("linked", "Linked"),
            ("missing_unit", "Crop Unit Not Found"),
            ("unresolved", "No Unique Crop Unit in Source"),
        ],
        required=True,
        index=True,
    )
    raw_json = fields.Json()
    raw_json_text = fields.Text(compute="_compute_raw_json_text")

    @api.depends("raw_json")
    def _compute_raw_json_text(self):
        for record in self:
            record.raw_json_text = (
                json.dumps(record.raw_json, ensure_ascii=False, indent=2)
                if record.raw_json is not False and record.raw_json is not None
                else False
            )

    _sql_constraints = [
        (
            "source_usage_key_unique",
            "unique(fsm_order_id, source_key)",
            "This original consumption row already exists for the work order.",
        ),
    ]
