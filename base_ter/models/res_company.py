# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    area_unit_is_ha = fields.Boolean(string="Standard area unit: ha (y/n)")
    area_unit_name = fields.Char(string="Standard area unit: Name", size=255)
    area_unit_value_in_ha = fields.Float(
        string="Standard area unit: Equivalence in ha",
        digits=(32, 4),
    )
    warning_diff_areas = fields.Integer(
        string="Alert threshold due to the difference between the official "
        "area and the GIS area",
    )
    same_parcelmanager_propertyowner = fields.Boolean(
        string="Force the parcel manager and the property owner to be the same",
    )
    aerial_image_wmsbase_url = fields.Char(
        string="WMS of the base image: URL", size=255
    )
    aerial_image_wmsbase_layers = fields.Char(
        string="WMS of the base image: Layers", size=255
    )
    aerial_image_wmsvec_url = fields.Char(
        string="WMS of the vectorial image: URL", size=255
    )
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
    gis_viewer_username = fields.Char(
        string="GIS Viewer: User name for the technical mode", size=255
    )
    gis_viewer_password = fields.Char(
        string="GIS Viewer: Password for the technical mode", size=255
    )
    gis_viewer_cipher_key = fields.Char(
        string="GIS Viewer: Cipher key for technical mode", size=255
    )
    gis_viewer_epsg = fields.Integer(string="GIS Viewer: Spatial Reference")
    gis_viewer_previs_additional_args = fields.Char(
        string="GIS Preview: Additional URL arguments", size=255
    )
    ter_unit_sequence_id = fields.Many2one(
        "ir.sequence",
        help="Sequence used to generate ter.use_unit names. "
        "Name format: {type_code}-{date_start}-{date_end}-{parcel_code}-{sequence}.",
    )

    def _get_area_unit_params(self):
        """
        Return area unit settings for this company: (is_ha, unit_name, value_in_ha).
        Ensures area_unit_* fields use the current company's settings.
        """
        self.ensure_one()
        is_ha = bool(self.area_unit_is_ha)
        unit_name = (self.area_unit_name or "").strip() or "ha"
        value_in_ha = float(self.area_unit_value_in_ha or 0) or 1.0
        return (is_ha, unit_name, value_in_ha)

    def _get_or_create_ter_unit_sequence(self):
        """Create default ter.use_unit sequence for company if missing."""
        for company in self:
            if company.ter_unit_sequence_id:
                continue
            seq = self.env["ir.sequence"].create(
                {
                    "name": self.env._(
                        "%(company_name)s – Ter Unit", company_name=company.name
                    ),
                    "code": "ter.use_unit.%s" % company.id,
                    "prefix": "",
                    "padding": 6,
                    "implementation": "no_gap",
                    "number_increment": 1,
                    "number_next": 1,
                    "company_id": company.id,
                }
            )
            company.ter_unit_sequence_id = seq

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        companies._get_or_create_ter_unit_sequence()  # pylint: disable=protected-access
        return companies

    def write(self, vals):
        res = super().write(vals)
        area_unit_fields = {
            "area_unit_is_ha",
            "area_unit_value_in_ha",
            "area_unit_name",
        }
        if area_unit_fields & set(vals):
            self._invalidate_area_unit_dependent()
        return res

    def _invalidate_area_unit_dependent(self):
        """Invalidate computed fields that depend on company area unit settings.

        When area_unit_is_ha, area_unit_value_in_ha or area_unit_name change,
        surface-related computed fields must be recomputed (m² and unit label).
        Each user will then see values in their current company's unit on next read.
        """
        # pylint: disable=no-search-all
        # We need to invalidate all records so computed surface fields are recomputed
        area_fields_parcel = [
            "area_official_m2",
            "area_unit_name",
            "diff_areas_threshold_exceeded",
        ]
        area_fields_property = [
            "area_official_parcels_m2",
            "area_unit_name",
            "diff_areas_threshold_exceeded",
        ]
        area_fields_partner = [
            "area_official_parcels_m2",
            "area_official_properties_m2",
            "area_unit_name",
        ]
        area_fields_unit = ["area_official_m2", "area_unit_name"]
        self.env["ter.parcel"].search([]).invalidate_recordset(area_fields_parcel)
        self.env["ter.property"].search([]).invalidate_recordset(area_fields_property)
        self.env["res.partner"].search([]).invalidate_recordset(area_fields_partner)
        self.env["ter.use_unit"].search([]).invalidate_recordset(area_fields_unit)

    _sql_constraints = [
        (
            "area_unit_value_in_ha_ok",
            "CHECK (area_unit_value_in_ha > 0)",
            'Incorrect value of "Standard area unit: Equivalence in ha".',
        ),
        (
            "warning_diff_areas_ok",
            "CHECK (warning_diff_areas >= 0 AND warning_diff_areas <= 100)",
            'Incorrect value of "Alert threshold due to the difference between the '
            'official area and the GIS area".',
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
