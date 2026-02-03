# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, api, exceptions, fields, models
from psycopg2 import sql


class ResCompany(models.Model):
    _inherit = "res.company"

    area_unit_is_ha = fields.Boolean(string="Standard area unit: ha (y/n)")
    area_unit_name = fields.Char(string="Standard area unit: Name", size=255)
    area_unit_value_in_ha = fields.Float(
        string="Standard area unit: Equivalence in ha",
        digits=(32, 4),
    )
    warning_diff_areas = fields.Integer(
        string="Alert threshold due to the difference between the official area and the GIS area",
    )
    same_parcelmanager_propertyowner = fields.Boolean(
        string="Force the parcel manager and the property owner to be the same",
    )
    aerial_image_wmsbase_url = fields.Char(string="WMS of the base image: URL", size=255)
    aerial_image_wmsbase_layers = fields.Char(string="WMS of the base image: Layers", size=255)
    aerial_image_wmsvec_url = fields.Char(string="WMS of the vectorial image: URL", size=255)
    aerial_image_wmsvec_parcel_name = fields.Char(
        string="WMS of the vectorial image: Name of the parcels layer", size=255
    )
    aerial_image_wmsvec_parcel_filter = fields.Boolean(
        string="WMS of the vectorial image: Filtered parcels (y/n)",
    )
    aerial_image_wmsvec_property_name = fields.Char(
        string="WMS of the vectorial image: Name of the properties layer", size=255
    )
    aerial_image_wmsvec_property_filter = fields.Boolean(
        string="WMS of the vectorial image: Filtered properties (y/n)",
    )
    aerial_image_height = fields.Integer(string="WMS Services: Height of the images")
    aerial_image_zoom = fields.Float(string="WMS Services: Zoom", digits=(32, 4))
    gis_viewer_url = fields.Char(string="GIS Viewer: URL", size=255)
    gis_viewer_username = fields.Char(string="GIS Viewer: User name for the technical mode", size=255)
    gis_viewer_password = fields.Char(string="GIS Viewer: Password for the technical mode", size=255)
    gis_viewer_epsg = fields.Integer(string="GIS Viewer: Spatial Reference")
    gis_viewer_previs_additional_args = fields.Char(
        string="GIS Preview: Additional URL arguments", size=255
    )
    ter_unit_sequence_id = fields.Many2one(
        "ir.sequence",
        string="Ter Unit Sequence",
        help="Sequence used to generate ter.unit names. "
        "Name format: {type_code}-{date_start}-{date_end}-{parcel_code}-{sequence}.",
    )

    def _get_or_create_ter_unit_sequence(self):
        """Create default ter.unit sequence for company if missing."""
        for company in self:
            if company.ter_unit_sequence_id:
                continue
            seq = self.env["ir.sequence"].create({
                "name": _("%s – Ter Unit") % company.name,
                "code": "ter.unit.%s" % company.id,
                "prefix": "",
                "padding": 5,
                "number_increment": 1,
                "number_next": 1,
                "company_id": company.id,
            })
            company.ter_unit_sequence_id = seq

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        companies._get_or_create_ter_unit_sequence()
        return companies

    _sql_constraints = [
        (
            "area_unit_value_in_ha_ok",
            "CHECK (area_unit_value_in_ha > 0)",
            'Incorrect value of "Standard area unit: Equivalence in ha".',
        ),
        (
            "warning_diff_areas_ok",
            "CHECK (warning_diff_areas >= 0 AND warning_diff_areas <= 100)",
            'Incorrect value of "Alert threshold due to the difference between the official area and the GIS area".',
        ),
        (
            "aerial_image_height_ok",
            "CHECK (aerial_image_height > 0)",
            'Incorrect value of "WMS Services: Height of the images".',
        ),
        (
            "aerial_image_zoom_ok",
            "CHECK (aerial_image_zoom > 0)",
            'Incorrect value of "WMS Services: Zoom".',
        ),
        (
            "gis_viewer_epsg_ok",
            "CHECK (gis_viewer_epsg > 0)",
            'Incorrect value of "GIS Viewer: Spatial Reference".',
        ),
    ]
