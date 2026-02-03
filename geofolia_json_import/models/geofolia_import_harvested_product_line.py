# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, fields, models
from odoo.exceptions import UserError


class GeofoliaImportHarvestedProductLine(models.Model):
    _name = "geofolia.import.harvested.product.line"
    _description = "Geofolia Import Harvested Product Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)  # HarvestId
    code = fields.Char()
    name = fields.Char()
    botanical_species_name = fields.Char(string="Botanical Species Name")
    botanical_species_id = fields.Integer(string="Botanical Species ID")
    harvested_product_kind_id = fields.Integer(string="Harvested Product Kind ID")
    unit_symbol = fields.Char()

    task_id = fields.Many2one(
        "project.task",
        string="Task",
        ondelete="set null",
        help="Target project.task created/updated by this line.",
    )

    _sql_constraints = [
        (
            "geofolia_harvested_job_ext_uniq",
            "unique(job_id, external_id)",
            "This harvested product has already been imported in this job.",
        ),
    ]

    def action_transform(self):
        """Transform / apply this line (called by Apply / Carga)."""
        return self.action_apply_selected()

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_harvested_product_line(line)
            line.job_id._recompute_apply_state()
