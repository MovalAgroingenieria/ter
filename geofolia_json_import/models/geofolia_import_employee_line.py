# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, fields, models
from odoo.exceptions import UserError


class GeofoliaImportEmployeeLine(models.Model):
    _name = "geofolia.import.employee.line"
    _description = "Geofolia Import Employee Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)  # EmployeeId
    code = fields.Char()
    name = fields.Char()
    first_name = fields.Char(string="First Name")
    national_identification_code = fields.Char(string="National Identification Code")
    specific_number = fields.Char(string="Specific Number")
    email = fields.Char()
    phone = fields.Char()

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        ondelete="set null",
        help="Target hr.employee created/updated by this line.",
    )

    _sql_constraints = [
        (
            "geofolia_employee_job_ext_uniq",
            "unique(job_id, external_id)",
            "This employee has already been imported in this job.",
        ),
    ]

    def action_transform(self):
        """Transform / apply this line (called by Apply / Carga)."""
        return self.action_apply_selected()

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_employee_line(line)
            line.job_id._recompute_apply_state()
