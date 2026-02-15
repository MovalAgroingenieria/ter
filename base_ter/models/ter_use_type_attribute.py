# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class UseTypeAttribute(models.Model):
    _name = "ter.use_type.attribute"
    _description = "Use Type Attribute"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)

    use_type_id = fields.Many2one(
        comodel_name="ter.use_type",
        required=True,
        ondelete="cascade",
    )

    value_ids = fields.One2many(
        comodel_name="ter.use_type.attribute.value",
        inverse_name="attribute_id",
        string="Allowed Values",
    )

    required = fields.Boolean(default=False)
