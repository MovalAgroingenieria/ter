# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
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
    fsm_order_id = fields.Many2one(
        related="activity_line_id.fsm_order_id",
        store=True,
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

    person_id = fields.Many2one("fsm.person", ondelete="set null")
    analytic_line_id = fields.Many2one("account.analytic.line", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_act_emp_uniq",
            "unique(job_id, employee_action_id, "
            "employee_recognition_id, employee_order)",
            "This activity employee entry has already been imported.",
        ),
    ]

    def action_apply_selected(self):
        for record in self:
            if not record.job_id:
                raise UserError(self.env._("Missing job."))
            record.job_id.with_context(
                geofolia_sync=True
            )._apply_activity_employee_line(record)  # pylint: disable=W0212
            record.job_id._recompute_apply_state()  # pylint: disable=W0212
