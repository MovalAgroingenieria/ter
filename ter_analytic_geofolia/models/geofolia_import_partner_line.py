# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.exceptions import UserError


class GeofoliaImportPartnerLine(models.Model):
    _name = "geofolia.import.partner.line"
    _description = "Geofolia Import Partner Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    vat = fields.Char()

    partner_id = fields.Many2one(
        "res.partner",
        ondelete="set null",
    )

    _sql_constraints = [
        (
            "geofolia_partner_job_ext_uniq",
            "unique(job_id, external_id)",
            "This partner has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        jobs = self.mapped("job_id")
        for record in self:
            if not record.job_id:
                raise UserError(self.env._("Missing job."))
            record.job_id.with_context(geofolia_sync=True)._apply_partner_line(
                record
            )  # pylint: disable=W0212
        for job in jobs:
            job._recompute_apply_state()  # pylint: disable=W0212
