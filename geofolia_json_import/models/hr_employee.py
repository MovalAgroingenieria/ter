# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    geofolia_external_id = fields.Char(index=True)
    geofolia_first_name = fields.Char(string="Geofolia First Name")
    geofolia_national_identification_code = fields.Char(
        string="Geofolia National Identification Code",
    )
    geofolia_specific_number = fields.Char(
        string="Geofolia Specific Number",
    )
    geofolia_job_id = fields.Many2one("geofolia.import.job", ondelete="set null")
    geofolia_source_line_ref = fields.Reference(
        selection=[("geofolia.import.employee.line", "Geofolia Employee line")],
        string="Geofolia Source Line",
    )

    _sql_constraints = [
        (
            "geofolia_employee_uniq",
            "unique(geofolia_external_id)",
            "This Geofolia employee has already been imported.",
        ),
    ]

