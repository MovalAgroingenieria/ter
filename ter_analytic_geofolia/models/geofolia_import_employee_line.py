# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.exceptions import UserError


class GeofoliaImportEmployeeLine(models.Model):
    _name = "geofolia.import.employee.line"
    _description = "Geofolia Import Employee Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    email = fields.Char()
    phone = fields.Char()

    person_id = fields.Many2one("fsm.person", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_employee_job_ext_uniq",
            "unique(job_id, external_id)",
            "This employee has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        for record in self:
            if not record.job_id:
                raise UserError(self.env._("Missing job."))
            record.job_id.with_context(geofolia_sync=True)._apply_employee_line(
                record
            )  # pylint: disable=W0212
            record.job_id._recompute_apply_state()  # pylint: disable=W0212
