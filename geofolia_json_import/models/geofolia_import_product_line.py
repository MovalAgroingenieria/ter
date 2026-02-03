# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, fields, models
from odoo.exceptions import UserError


class GeofoliaImportProductLine(models.Model):
    _name = "geofolia.import.product.line"
    _description = "Geofolia Import Product Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)  # SupplyId
    recognition_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    rn_reference_supply_name = fields.Char(string="RN Reference Supply Name")
    rn_reference_supply_code = fields.Char(string="RN Reference Supply Code")
    unit_symbol = fields.Char()
    product_form_enum = fields.Char(string="Product Form")
    category_enum = fields.Integer()
    product_type_enum = fields.Integer()

    product_component_n_total = fields.Float()
    product_component_p2o5 = fields.Float()
    product_component_k2o = fields.Float()

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        ondelete="set null",
        help="Target product.product created/updated by this line.",
    )

    _sql_constraints = [
        (
            "geofolia_product_job_ext_uniq",
            "unique(job_id, external_id)",
            "This product has already been imported in this job.",
        ),
    ]

    def action_transform(self):
        """Transform / apply this line (called by Apply / Carga)."""
        return self.action_apply_selected()

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            if line.job_id.import_type != "full":
                continue
            line.job_id._apply_product_line(line)
            line.job_id._recompute_apply_state()
