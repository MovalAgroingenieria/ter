# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    geofolia_external_id = fields.Char(index=True)
    geofolia_job_id = fields.Many2one("geofolia.import.job", ondelete="set null")
    geofolia_activity_line_id = fields.Many2one(
        "geofolia.import.activity.line",
        ondelete="set null",
        index=True,
    )
    ter_unit_id = fields.Many2one(
        "ter.unit",
        string="Ter Unit",
        index=True,
        ondelete="set null",
    )
    ter_parcel_id = fields.Many2one(
        "ter.parcel",
        string="Parcel",
        index=True,
        ondelete="set null",
    )
    ter_property_id = fields.Many2one(
        "ter.property",
        string="Property",
        index=True,
        ondelete="set null",
    )
    ter_use_type_id = fields.Many2one(
        "ter.use_type",
        string="Use Type",
        index=True,
        ondelete="set null",
    )
    geofolia_operation_category = fields.Char(
        string="Geofolia Operation Category",
        help="Operation category from Geofolia (e.g. Soil work)",
    )
    geofolia_status_name = fields.Char(
        string="Geofolia Status",
        help="Activity status from Geofolia (e.g. Done)",
    )
    geofolia_status_code = fields.Char(
        string="Geofolia Status Code",
    )
    geofolia_worked_surface = fields.Float(
        string="Geofolia Worked Surface (m²)",
        help="Worked surface from CropZone for this employee/plot",
    )

    _sql_constraints = [
        (
            "geofolia_analytic_uniq",
            "unique(geofolia_external_id)",
            "This Geofolia activity has already been imported.",
        ),
    ]
