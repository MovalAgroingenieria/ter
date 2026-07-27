# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TerUnitAttributeValue(models.Model):
    _name = "ter.unit.attribute.value"
    _description = "Ter Unit Attribute Value"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "attribute_id"
    _order = "attribute_id, id"

    _sql_constraints = [
        (
            "unit_attribute_unique",
            "unique(unit_id, attribute_id)",
            "Each attribute can only appear once per unit.",
        ),
    ]

    unit_id = fields.Many2one(
        comodel_name="ter.use_unit",
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
        # Domain is better enforced at view level too, but keep a safe server-side
        # check below.
    )

    value_id = fields.Many2one(
        comodel_name="ter.use_type.attribute.value",
        domain="[('attribute_id', '=', attribute_id)]",
        readonly=False,
    )
    color = fields.Integer(string="Color Index")
    required = fields.Boolean(related="attribute_id.required", readonly=True)
    display_name = fields.Char(compute="_compute_display_name")

    @api.depends("attribute_id", "value_id")
    def _compute_display_name(self):
        for record in self:
            parts = []
            if record.attribute_id:
                parts.append(record.attribute_id.name)
            if record.value_id:
                parts.append(record.value_id.name)
            record.display_name = ": ".join(parts) if parts else str(record.id)

    @api.constrains("attribute_id", "unit_id")
    def _check_attribute_belongs_to_use_type(self):
        for record in self:
            if not record.unit_id.use_type_id or not record.attribute_id:
                continue
            allowed = record.unit_id.use_type_id.all_attribute_ids
            if record.attribute_id not in allowed:
                raise ValidationError(
                    self.env._(
                        "Attribute '%(attr)s' is not allowed for use type '%(use)s'.",
                        attr=record.attribute_id.display_name,
                        use=record.unit_id.use_type_id.display_name,
                    )
                )
