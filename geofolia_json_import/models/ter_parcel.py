# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, fields, models


class TerParcel(models.Model):
    _inherit = "ter.parcel"

    timesheet_count = fields.Integer(
        string="Timesheets",
        compute="_compute_timesheet_task_counts",
    )
    task_count = fields.Integer(
        string="Tasks",
        compute="_compute_timesheet_task_counts",
    )

    def _compute_timesheet_task_counts(self):
        AnalyticLine = self.env["account.analytic.line"]
        for rec in self:
            if not rec.id:
                rec.timesheet_count = 0
                rec.task_count = 0
                continue
            lines = AnalyticLine.search([("ter_parcel_id", "=", rec.id)])
            rec.timesheet_count = len(lines)
            task_ids = lines.mapped("task_id").filtered("id").ids
            rec.task_count = len(set(task_ids))

    def action_show_timesheets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Timesheets"),
            "res_model": "account.analytic.line",
            "view_mode": "list,form",
            "domain": [("ter_parcel_id", "=", self.id)],
        }

    def action_show_tasks(self):
        self.ensure_one()
        lines = self.env["account.analytic.line"].search(
            [("ter_parcel_id", "=", self.id)]
        )
        task_ids = lines.mapped("task_id").filtered("id").ids
        return {
            "type": "ir.actions.act_window",
            "name": _("Tasks"),
            "res_model": "project.task",
            "view_mode": "list,form",
            "domain": [("id", "in", list(set(task_ids)))],
        }

    geofolia_farm_identification_code = fields.Char(
        string="Geofolia Farm Identification Code",
        index=True,
        copy=False,
        help="Farm/plot identifier from Geofolia. Used for matching ter.use_unit "
        "to parcels when importing.",
    )
