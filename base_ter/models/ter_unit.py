# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import json
from odoo.exceptions import ValidationError


class TerUnit(models.Model):
    _name = "ter.unit"
    _description = "Ter Unit"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    partner_id = fields.Many2one('res.partner')
    description = fields.Html(help="Description to provide more information and context about this ter_unit")
    active = fields.Boolean(default=True, copy=False, export_string_translation=False)
    sequence = fields.Integer(default=10, export_string_translation=False)
    parcel_id = fields.Many2one('ter.parcel', required=True)
    date_start = fields.Date(string="Start date", required=True)
    date_end = fields.Date(string="End date", required=True)
    #
    date_range_id = fields.Many2one('date.range', domain=[('is_unit_use_type', '=', True)], required=True)
    #
    area_official = fields.Float(
        string="Official Area",
        digits=(32, 4),
        default=0,
        required=True,
        index=True,
    )
    account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    area_official_m2 = fields.Integer(
        string="Official Area (m²)",
        compute="_compute_area_official_m2",
    )
    use_type_id = fields.Many2one('ter.use_type')
    attribute_value_ids = fields.One2many(
        comodel_name="ter.unit.attribute.value",
        inverse_name="unit_id",
        string="Attributes",
        copy=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._ensure_attribute_lines()
        return records

    def _ensure_attribute_lines(self):
        for unit in self:
            if not unit.use_type_id:
                continue

            required_attrs = unit.use_type_id.all_attribute_ids
            existing_attrs = unit.attribute_value_ids.mapped("attribute_id")

            missing_attrs = required_attrs - existing_attrs

            lines = []
            for attr in missing_attrs:
                lines.append((0, 0, {
                    "attribute_id": attr.id,
                }))

            if lines:
                unit.write({
                    "attribute_value_ids": lines,
                })

    @api.onchange("use_type_id")
    def _onchange_use_type_id(self):
        if not self.use_type_id:
            self.attribute_value_ids = [(5, 0, 0)]
            return

        lines = []
        for attr in self.use_type_id.all_attribute_ids:
            lines.append((0, 0, {
                "attribute_id": attr.id,
            }))
        self.attribute_value_ids = lines

    @api.constrains("attribute_value_ids")
    def _check_required_attributes(self):
        for unit in self:
            for line in unit.attribute_value_ids:
                if line.required and not line.value_id:
                    raise ValidationError(
                        _("Attribute '%s' is required.") % line.attribute_id.name
                    )

    @api.depends("area_official")
    def _compute_area_official_m2(self):
        config = self.env["ir.config_parameter"].sudo()
        area_unit_is_ha = bool(config.get_param("base_ter.area_unit_is_ha", False))
        factor = 10000.0
        if not area_unit_is_ha:
            value_in_ha = float(
                config.get_param("base_ter.area_unit_value_in_ha", 0) or 0
            )
            if value_in_ha and value_in_ha != 1:
                factor = value_in_ha * 10000.0

        for record in self:
            record.area_official_m2 = round((record.area_official or 0.0) * factor)

