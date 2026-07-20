# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class GeofoliaImportActivityLine(models.Model):
    _name = "geofolia.import.activity.line"
    _description = "Geofolia Import Activity Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    farm_identification_code = fields.Char()
    external_id = fields.Char(index=True)
    harvest_year = fields.Integer()

    operation_name = fields.Char()
    operation_category = fields.Char()

    status_name = fields.Char()
    status_code = fields.Char()

    starting_date = fields.Date()
    ending_date = fields.Date()
    duration_minutes = fields.Integer()

    last_modification_dt = fields.Datetime()
    comment = fields.Text()

    employee_line_ids = fields.One2many(
        "geofolia.import.activity.employee.line",
        "activity_line_id",
        string="Employees",
    )
    fsm_order_id = fields.Many2one(
        comodel_name="fsm.order",
        string="FSM Order",
        ondelete="set null",
        help="With fieldservice_timesheet, employee times link to this order.",
    )

    _sql_constraints = [
        (
            "geofolia_activity_job_ext_uniq",
            "unique(job_id, external_id)",
            "This activity has already been imported in this job.",
        ),
    ]
