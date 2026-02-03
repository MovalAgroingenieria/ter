# Copyright 2024-2026 Moval Agro-engineering
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    geofolia_timesheet_project_id = fields.Many2one(
        related="company_id.geofolia_timesheet_project_id",
        readonly=False,
    )
    geofolia_timesheet_task_id = fields.Many2one(
        related="company_id.geofolia_timesheet_task_id",
        readonly=False,
    )
    geofolia_default_date_range_id = fields.Many2one(
        related="company_id.geofolia_default_date_range_id",
        readonly=False,
    )
