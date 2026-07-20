# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.exceptions import UserError


class GeofoliaImportHarvestedProductLine(models.Model):
    _name = "geofolia.import.harvested.product.line"
    _description = "Geofolia Import Harvested Product Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    unit_symbol = fields.Char()

    product_id = fields.Many2one("product.product", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_harvested_job_ext_uniq",
            "unique(job_id, external_id)",
            "This harvested product has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        for record in self:
            if not record.job_id:
                raise UserError(self.env._("Missing job."))
            record.job_id._apply_product_like(
                record, label="harvested_products"
            )  # pylint: disable=W0212
            record.job_id._recompute_apply_state()  # pylint: disable=W0212
