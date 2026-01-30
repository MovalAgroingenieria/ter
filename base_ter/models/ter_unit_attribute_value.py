from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TerUnitAttributeValue(models.Model):
    _name = "ter.unit.attribute.value"
    _description = "Ter Unit Attribute Value"
    _rec_name = "attribute_id"
    _order = "attribute_id, id"

    unit_id = fields.Many2one(
        comodel_name="ter.unit",
        required=True,
        ondelete="cascade",
        index=True,
    )

    use_type_id = fields.Many2one(
        comodel_name="ter.use_type",
        related="unit_id.use_type_id",
        store=True,
        readonly=True,
    )

    attribute_id = fields.Many2one(
        comodel_name="ter.use_type.attribute",
        required=True,
        ondelete="restrict",
        index=True,
        readonly=False,
        # Domain is better enforced at view level too, but keep a safe server-side check below.
    )

    value_id = fields.Many2one(
        comodel_name="ter.use_type.attribute.value",
        string="Value",
        domain="[('attribute_id', '=', attribute_id)]",
        readonly=False
    )

    required = fields.Boolean(related="attribute_id.required", readonly=True)

    _sql_constraints = [
        (
            "unit_attribute_unique",
            "unique(unit_id, attribute_id)",
            "Each attribute can only appear once per unit.",
        ),
    ]

    @api.constrains("attribute_id", "unit_id")
    def _check_attribute_belongs_to_use_type(self):
        for line in self:
            if not line.unit_id.use_type_id or not line.attribute_id:
                continue
            allowed = line.unit_id.use_type_id.all_attribute_ids
            if line.attribute_id not in allowed:
                raise ValidationError(
                    _("Attribute '%s' is not allowed for use type '%s'.")
                    % (line.attribute_id.display_name, line.unit_id.use_type_id.display_name)
                )
