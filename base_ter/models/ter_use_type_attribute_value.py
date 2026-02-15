# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class UseTypeAttributeValue(models.Model):
    _name = "ter.use_type.attribute.value"
    _description = "Use Type Attribute Value"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)

    attribute_id = fields.Many2one(
        comodel_name="ter.use_type.attribute",
        required=True,
        ondelete="cascade",
    )
