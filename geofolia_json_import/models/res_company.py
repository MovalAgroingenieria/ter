# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    geofolia_timesheet_project_id = fields.Many2one(
        comodel_name="project.project",
        string="Geofolia Timesheet Project",
    )
    geofolia_timesheet_task_id = fields.Many2one(
        comodel_name="project.task",
        string="Geofolia Timesheet Task",
        domain="[('project_id', '=', geofolia_timesheet_project_id)]",
    )
    geofolia_default_date_range_id = fields.Many2one(
        comodel_name="date.range",
        string="Geofolia Default Campaign",
        domain="[('is_unit_use_type', '=', True)]",
        help="Default campaign (date range) for ter.unit created from Geofolia Fields.",
    )
