# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    geofolia_external_id = fields.Char(
        string="Geofolia ID",
        index=True,
        copy=False,
        groups="ter_analytic_geofolia.group_geofolia_import",
        help="External ID from Geofolia (Partners) import. Prevents duplicate imports.",
    )

    _sql_constraints = [
        (
            "geofolia_res_partner_external_id_uniq",
            "unique(geofolia_external_id)",
            "A partner with this Geofolia ID already exists.",
        ),
    ]
