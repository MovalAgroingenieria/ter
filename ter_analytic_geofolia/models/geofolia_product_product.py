# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

GEOFOLIA_IMPORT_GROUP = "ter_analytic_geofolia.group_geofolia_import"


class ProductProduct(models.Model):
    _inherit = "product.product"

    geofolia_external_id = fields.Char(
        string="Geofolia ID",
        index=True,
        copy=False,
        help="External ID from Geofolia import. Prevents duplicate imports.",
    )

    _sql_constraints = [
        (
            "geofolia_product_external_id_uniq",
            "unique(geofolia_external_id)",
            "A product with this Geofolia ID already exists.",
        ),
    ]

    def _strip_geofolia_external_id_if_no_access(self, vals):
        if not vals or "geofolia_external_id" not in vals:
            return vals
        if self.env.user.has_group(GEOFOLIA_IMPORT_GROUP):
            return vals
        if not isinstance(vals, dict):
            return vals
        vals = dict(vals)
        vals.pop("geofolia_external_id", None)
        return vals

    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        vals_list = [
            self._strip_geofolia_external_id_if_no_access(v) for v in vals_list
        ]
        return super().create(vals_list)

    def write(self, vals):
        vals = self._strip_geofolia_external_id_if_no_access(vals)
        return super().write(vals)
