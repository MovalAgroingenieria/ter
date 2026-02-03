# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    geofolia_harvest_id = fields.Char(
        string="Geofolia Harvest ID",
        index=True,
        copy=False,
        help="Unique identifier from Geofolia HarvestedProducts (HarvestId).",
    )
    geofolia_botanical_species_name = fields.Char(
        string="Geofolia Botanical Species Name",
    )
    geofolia_botanical_species_id = fields.Integer(
        string="Geofolia Botanical Species ID",
    )
    geofolia_harvested_product_kind_id = fields.Integer(
        string="Geofolia Harvested Product Kind ID",
    )
    geofolia_unit_symbol = fields.Char(
        string="Geofolia Unit Symbol",
    )
