from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class TerUnitAttributeValue(models.Model):
    _name = "ter.unit.attribute.value"
    _description = "Ter Unit Attribute Value"
    _rec_name = "attribute_id"

    unit_id = fields.Many2one(
        comodel_name="ter.unit",
        required=True,
        ondelete="cascade",
    )

    attribute_id = fields.Many2one(
        comodel_name="ter.use_type.attribute",
        required=True,
        ondelete="restrict",
    )

    value_id = fields.Many2one(
        comodel_name="ter.use_type.attribute.value",
        string="Value",
        domain="[('attribute_id', '=', attribute_id)]",
    )

    required = fields.Boolean(related="attribute_id.required", readonly=True)
