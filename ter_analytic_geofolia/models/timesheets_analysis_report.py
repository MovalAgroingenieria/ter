# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class TimesheetsAnalysisReport(models.Model):
    _inherit = "timesheets.analysis.report"

    geofolia_external_id = fields.Char(
        string="Geofolia ID",
        readonly=True,
    )

    @api.model
    def _select(self):
        return (
            super()._select()
            + """,
                A.geofolia_external_id AS geofolia_external_id
        """
        )
