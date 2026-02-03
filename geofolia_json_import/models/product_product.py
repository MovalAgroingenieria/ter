# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    geofolia_external_id = fields.Char(index=True)
    geofolia_recognition_id = fields.Char(index=True)
    geofolia_product_component_n_total = fields.Float(
        string="Geofolia N Total (%)",
    )
    geofolia_product_component_p2o5 = fields.Float(
        string="Geofolia P2O5 (%)",
    )
    geofolia_product_component_k2o = fields.Float(
        string="Geofolia K2O (%)",
    )
    geofolia_source = fields.Selection(
        selection=[
            ("products", "Products"),
            ("harvested", "HarvestedProducts"),
            ("equipments", "Equipments"),
        ],
        index=True,
    )
    geofolia_job_id = fields.Many2one("geofolia.import.job", ondelete="set null")
    geofolia_source_line_ref = fields.Reference(
        selection=[
            ("geofolia.import.product.line", "Geofolia Product line"),
            ("geofolia.import.harvested.product.line", "Geofolia Harvested Product line"),
            ("geofolia.import.equipment.line", "Geofolia Equipment line"),
        ],
        string="Geofolia Source Line",
    )

    _sql_constraints = [
        (
            "geofolia_product_uniq",
            "unique(geofolia_source, geofolia_external_id)",
            "This Geofolia product has already been imported.",
        ),
    ]

