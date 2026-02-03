# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class TerUnit(models.Model):
    _inherit = "ter.unit"

    geofolia_uid = fields.Char(
        string="Geofolia UID",
        index=True,
        copy=False,
        help="Unique identifier from Geofolia Field/Plot for matching.",
    )
    geofolia_last_modification_date = fields.Datetime(
        string="Geofolia Last Modification Date",
    )
    geofolia_last_modification_geometry_date = fields.Datetime(
        string="Geofolia Last Modification Geometry Date",
    )
    geofolia_code = fields.Char(string="Geofolia Code")
    geofolia_name = fields.Char(string="Geofolia Name")
    geofolia_parent_id1 = fields.Char(string="Geofolia Parent Id1")
    geofolia_area = fields.Float(string="Geofolia Area")
    geofolia_geography = fields.Text(string="Geofolia Geography (WKT)")
    geofolia_main_plot_id = fields.Char(string="Geofolia Main Plot Id")
    geofolia_irrigation_kind = fields.Integer(string="Geofolia Irrigation Kind")
    geofolia_irrigation_kind_name = fields.Char(
        string="Geofolia Irrigation Kind Name"
    )
    geofolia_comment = fields.Text(string="Geofolia Comment")
    geofolia_ferti_diary_comment = fields.Text(
        string="Geofolia Ferti Diary Comment"
    )
    geofolia_phyto_diary_comment = fields.Text(
        string="Geofolia Phyto Diary Comment"
    )
    geofolia_plot_kind = fields.Integer(string="Geofolia Plot Kind")
    geofolia_plot_kind_name = fields.Char(string="Geofolia Plot Kind Name")
    geofolia_crop_name = fields.Char(string="Geofolia Crop Name")
    geofolia_botanical_species_code = fields.Char(
        string="Geofolia Botanical Species Code"
    )
    geofolia_variety_name = fields.Char(string="Geofolia Variety Name")
    geofolia_unit = fields.Char(string="Geofolia Unit")

    _sql_constraints = [
        (
            "ter_unit_geofolia_uid_uniq",
            "unique(geofolia_uid)",
            "Geofolia UID must be unique.",
        ),
    ]

