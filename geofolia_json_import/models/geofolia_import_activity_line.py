# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class GeofoliaImportActivityLine(models.Model):
    _name = "geofolia.import.activity.line"
    _description = "Geofolia Import Activity Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    farm_identification_code = fields.Char()
    external_id = fields.Char(index=True)  # ActionId
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
    maintenance_request_id = fields.Many2one(
        "maintenance.request",
        string="Maintenance Request",
        ondelete="set null",
        help="Target maintenance.request created from this activity.",
    )

    _sql_constraints = [
        (
            "geofolia_activity_job_ext_uniq",
            "unique(job_id, external_id)",
            "This activity has already been imported in this job.",
        ),
    ]
