# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, fields, models
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
        string="Partner",
        ondelete="set null",
        help="Target res.partner created/updated by this line.",
    )

    _sql_constraints = [
        (
            "geofolia_partner_job_ext_uniq",
            "unique(job_id, external_id)",
            "This partner has already been imported in this job.",
        ),
    ]

    def action_transform(self):
        """Transform / apply this line (called by Apply / Carga)."""
        return self.action_apply_selected()

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_partner_line(line)
            line.job_id._recompute_apply_state()
