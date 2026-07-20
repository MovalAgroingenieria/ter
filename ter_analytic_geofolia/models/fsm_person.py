# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class FSMPerson(models.Model):
    _inherit = "fsm.person"

    geofolia_external_id = fields.Char(
        string="Geofolia ID",
        index=True,
        copy=False,
        groups="ter_analytic_geofolia.group_geofolia_import",
        help="External ID from Geofolia (Employees) import. Prevents duplicates.",
    )

    _sql_constraints = [
        (
            "geofolia_fsm_person_external_id_uniq",
            "unique(geofolia_external_id)",
            "A field service person with this Geofolia ID already exists.",
        ),
    ]
