from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class UseTypeAttributeValue(models.Model):
    _name = "ter.use_type.attribute.value"
    _description = "Use Type Attribute Value"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)

    attribute_id = fields.Many2one(
        comodel_name="ter.use_type.attribute",
        required=True,
        ondelete="cascade",
    )
