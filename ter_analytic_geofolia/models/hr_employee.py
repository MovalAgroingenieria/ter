# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    geofolia_external_id = fields.Char(
        string="Geofolia ID",
        index=True,
        copy=False,
        groups="ter_analytic_geofolia.group_geofolia_import",
        help="External ID from Geofolia import. Prevents duplicate imports.",
    )

    _sql_constraints = [
        (
            "geofolia_employee_external_id_uniq",
            "unique(geofolia_external_id)",
            "An employee with this Geofolia ID already exists.",
        ),
    ]
