# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    geofolia_external_id = fields.Char(
        string="Geofolia ID",
        index=True,
        copy=False,
        help="Geofolia supply kind id (SupplyKindId). Products imported from "
        "Geofolia with this kind id are assigned to this category.",
    )

    _sql_constraints = [
        (
            "geofolia_category_external_id_uniq",
            "unique(geofolia_external_id)",
            "A product category with this Geofolia ID already exists.",
        ),
    ]
