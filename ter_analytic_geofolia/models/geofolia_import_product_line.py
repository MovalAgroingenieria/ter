# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.exceptions import UserError


class GeofoliaImportProductLine(models.Model):
    _name = "geofolia.import.product.line"
    _description = "Geofolia Import Product Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    farm_identification_code = fields.Char(
        default="",
        index=True,
        help="Farm identification from Geofolia; same SupplyId can appear per farm.",
    )
    code = fields.Char()
    name = fields.Char()
    category_enum = fields.Integer()
    product_type_enum = fields.Integer()
    unit_symbol = fields.Char()

    product_id = fields.Many2one("product.product", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_product_job_ext_farm_uniq",
            "unique(job_id, external_id, farm_identification_code)",
            "This product (and farm) has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        for record in self:
            if not record.job_id:
                raise UserError(self.env._("Missing job."))
            if record.job_id.import_type != "full":
                continue
            record.job_id.with_context(geofolia_sync=True)._apply_product_line(
                record
            )  # pylint: disable=W0212
            record.job_id._recompute_apply_state()  # pylint: disable=W0212
