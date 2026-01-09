# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, api, exceptions, fields, models
from psycopg2 import sql


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    area_unit_is_ha = fields.Boolean(
        string="Standard area unit: ha (y/n)",
        config_parameter="base_ter.area_unit_is_ha",
    )
    area_unit_name = fields.Char(
        string="Standard area unit: Name",
        size=255,
        config_parameter="base_ter.area_unit_name",
    )
    area_unit_value_in_ha = fields.Float(
        string="Standard area unit: Equivalence in ha",
        digits=(32, 4),
        config_parameter="base_ter.area_unit_value_in_ha",
    )
    warning_diff_areas = fields.Integer(
        string="Alert threshold due to the difference between the official area and the GIS area",
        config_parameter="base_ter.warning_diff_areas",
    )
    same_parcelmanager_propertyowner = fields.Boolean(
        string="Force the parcel manager and the property owner to be the same",
        config_parameter="base_ter.same_parcelmanager_propertyowner",
    )
    aerial_image_wmsbase_url = fields.Char(
        string="WMS of the base image: URL",
        size=255,
        config_parameter="base_ter.aerial_image_wmsbase_url",
    )
    aerial_image_wmsbase_layers = fields.Char(
        string="WMS of the base image: Layers",
        size=255,
        config_parameter="base_ter.aerial_image_wmsbase_layers",
    )
    aerial_image_wmsvec_url = fields.Char(
        string="WMS of the vectorial image: URL",
        size=255,
        config_parameter="base_ter.aerial_image_wmsvec_url",
    )
    aerial_image_wmsvec_parcel_name = fields.Char(
        string="WMS of the vectorial image: Name of the parcels layer",
        size=255,
        config_parameter="base_ter.aerial_image_wmsvec_parcel_name",
    )
    aerial_image_wmsvec_parcel_filter = fields.Boolean(
        string="WMS of the vectorial image: Filtered parcels (y/n)",
        config_parameter="base_ter.aerial_image_wmsvec_parcel_filter",
    )
    aerial_image_wmsvec_property_name = fields.Char(
        string="WMS of the vectorial image: Name of the properties layer",
        size=255,
        config_parameter="base_ter.aerial_image_wmsvec_property_name",
    )
    aerial_image_wmsvec_property_filter = fields.Boolean(
        string="WMS of the vectorial image: Filtered properties (y/n)",
        config_parameter="base_ter.aerial_image_wmsvec_property_filter",
    )
    aerial_image_height = fields.Integer(
        string="WMS Services: Height of the images",
        config_parameter="base_ter.aerial_image_height",
    )
    aerial_image_zoom = fields.Float(
        string="WMS Services: Zoom",
        digits=(32, 4),
        config_parameter="base_ter.aerial_image_zoom",
    )
    gis_viewer_url = fields.Char(
        string="GIS Viewer: URL",
        size=255,
        config_parameter="base_ter.gis_viewer_url",
    )
    gis_viewer_username = fields.Char(
        string="GIS Viewer: User name for the technical mode",
        size=255,
        config_parameter="base_ter.gis_viewer_username",
    )
    gis_viewer_password = fields.Char(
        string="GIS Viewer: Password for the technical mode",
        size=255,
        config_parameter="base_ter.gis_viewer_password",
    )
    gis_viewer_epsg = fields.Integer(
        string="GIS Viewer: Spatial Reference",
        config_parameter="base_ter.gis_viewer_epsg",
    )
    gis_viewer_previs_additional_args = fields.Char(
        string="GIS Preview: Additional URL arguments",
        size=255,
        config_parameter="base_ter.gis_viewer_previs_additional_args",
    )

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

    def set_values(self):
        self.ensure_one()
        config = self.env["ir.config_parameter"].sudo()
        prev_epsg = int(config.get_param("base_ter.gis_viewer_epsg") or 0)

        res = super().set_values()

        new_epsg = int(self.gis_viewer_epsg or 0)
        if prev_epsg and new_epsg and prev_epsg != new_epsg:
            ok, details = self.update_geometry(prev_epsg, new_epsg)
            if not ok:
                raise exceptions.UserError(_("Unable to update geometry: %s") % details)

        return res

    @api.model
    def update_geometry(self, old_epsg, new_epsg):
        layers = self._set_layers_to_update_geometry()
        for layer in layers or []:
            ok, details = self._update_layer_geometry(layer, old_epsg, new_epsg)
            if not ok:
                return False, details
        return True, ""

    @api.model
    def _update_layer_geometry(self, layer, old_epsg, new_epsg):
        cr = self.env.cr
        try:
            cr.execute("DROP VIEW IF EXISTS ter_gis_parcel_model")
            cr.execute(
                sql.SQL(
                    "ALTER TABLE {table} ALTER COLUMN geom "
                    "TYPE postgis.geometry(Geometry, %s) "
                    "USING postgis.ST_Transform(postgis.ST_SetSRID(geom, %s), %s)"
                ).format(table=sql.Identifier(layer)),
                (new_epsg, old_epsg, new_epsg),
            )
            cr.execute(
                """
                CREATE VIEW ter_gis_parcel_model AS
                (
                SELECT ROW_NUMBER()                      OVER() AS id, tgp.name,
                       postgis.st_asgeojson(tgp.geom) AS geom_geojson,
                       tp.id                          AS parcel_id,
                       tp.partner_id                  as partner_id,
                       tp.active                      as is_active
                FROM ter_gis_parcel tgp
                         LEFT JOIN ter_parcel tp ON tgp.name = tp.name
                WHERE tp.partner_id IS NOT NULL
                   OR tp.partner_id IS NULL
                ORDER BY tgp.name)
                """
            )
        except Exception as err:
            return False, f"{layer}\n\nERROR:\n\n{err}"
        return True, ""

    @api.model
    def _set_layers_to_update_geometry(self):
        return [
            "ter_gis_parcel",
            "ter_gis_property",
        ]
