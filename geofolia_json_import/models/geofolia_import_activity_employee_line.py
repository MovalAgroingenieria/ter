# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, fields, models
from odoo.exceptions import UserError


class GeofoliaImportActivityEmployeeLine(models.Model):
    _name = "geofolia.import.activity.employee.line"
    _description = "Geofolia Import Activity Employee Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    activity_line_id = fields.Many2one(
        "geofolia.import.activity.line",
        required=True,
        ondelete="cascade",
    )
    activity_operation_name = fields.Char(
        related="activity_line_id.operation_name",
        string="Activity",
        readonly=True,
    )

    employee_action_id = fields.Char(index=True)
    employee_recognition_id = fields.Char(index=True)
    employee_order = fields.Integer()

    employee_farm_identification_code = fields.Char()
    employee_first_name = fields.Char()
    employee_name = fields.Char()
    employee_id_external = fields.Char(index=True)
    employee_time = fields.Float()

    plot_code = fields.Char(
        string="Plot Code",
        help="Parcel code from CropZone (for debugging)",
    )
    worked_surface = fields.Float(
        string="Worked Surface (m²)",
        help="Worked surface from CropZone for this employee/plot",
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        ondelete="set null",
        help="Target hr.employee for this line.",
    )
    analytic_line_id = fields.Many2one(
        "account.analytic.line",
        string="Analytic Line",
        ondelete="set null",
        help="Target account.analytic.line created/updated by this line.",
    )

    _sql_constraints = [
        (
            "geofolia_act_emp_uniq",
            "unique(job_id, employee_action_id, employee_recognition_id, "
            "employee_order)",
            "This activity employee entry has already been imported in this job.",
        ),
    ]

    def action_transform(self):
        """Transform / apply this line (called by Apply / Carga)."""
        return self.action_apply_selected()

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_activity_employee_line(line)
            line.job_id._recompute_apply_state()
