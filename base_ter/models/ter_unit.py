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
    _inherits = {'account.analytic.line': 'line_id'}

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            self.account_id = self.project_id.account_id.id

    project_id = fields.Many2one('ter.project')
    line_id = fields.Many2one('account.analytic.line')
    description = fields.Html(help="Description to provide more information and context about this ter_unit")
    active = fields.Boolean(default=True, copy=False, export_string_translation=False)
    sequence = fields.Integer(default=10, export_string_translation=False)
    parcel_id = fields.Many2one('ter.parcel', required=True)
    date_end = fields.Date(string="End date", required=True)

    area_official = fields.Float(
        string="Official Area",
        digits=(32, 4),
        default=0,
        required=True,
        index=True,
    )
    area_official_m2 = fields.Integer(
        string="Official Area (m²)",
        compute="_compute_area_official_m2",
    )
    categ_id = fields.Many2one('product.category', string='Product Category', required=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', required=True)

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        if not self.categ_id:
            self.product_tmpl_id = False
            self.product_id = False
        else:
            if not self.product_tmpl_id:
                self.product_id = False
            else:
                if self.product_tmpl_id.categ_id.id != self.categ_id.id:
                    self.product_tmpl_id = False
                    self.product_id = False

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        if not self.product_tmpl_id:
            self.product_id = False
        else:
            if self.product_id:
                if self.product_id.product_tmpl_id.id != self.product_tmpl_id.id:
                    self.product_id = False


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

