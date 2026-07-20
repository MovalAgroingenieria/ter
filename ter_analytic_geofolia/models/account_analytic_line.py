# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    geofolia_external_id = fields.Char(
        string="Geofolia ID",
        index=True,
        copy=False,
        groups="ter_analytic_geofolia.group_geofolia_import",
        help="External ID from Geofolia import. Prevents duplicate imports.",
    )

    _sql_constraints = [
        (
            "geofolia_analytic_external_id_uniq",
            "unique(geofolia_external_id)",
            "An analytic line with this Geofolia ID already exists.",
        ),
    ]
