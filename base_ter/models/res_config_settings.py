# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, api, exceptions, fields, models
from psycopg2 import sql


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    _inherit = "res.config.settings"

    area_unit_is_ha = fields.Boolean(related="company_id.area_unit_is_ha", readonly=False)
    area_unit_name = fields.Char(related="company_id.area_unit_name", readonly=False)
    area_unit_value_in_ha = fields.Float(
        related="company_id.area_unit_value_in_ha",
        readonly=False,
        digits=(32, 4),
    )
    warning_diff_areas = fields.Integer(related="company_id.warning_diff_areas", readonly=False)
    same_parcelmanager_propertyowner = fields.Boolean(
        related="company_id.same_parcelmanager_propertyowner",
        readonly=False,
    )
    aerial_image_wmsbase_url = fields.Char(related="company_id.aerial_image_wmsbase_url", readonly=False)
    aerial_image_wmsbase_layers = fields.Char(related="company_id.aerial_image_wmsbase_layers", readonly=False)
    aerial_image_wmsvec_url = fields.Char(related="company_id.aerial_image_wmsvec_url", readonly=False)
    aerial_image_wmsvec_parcel_name = fields.Char(
        related="company_id.aerial_image_wmsvec_parcel_name",
        readonly=False,
    )
    aerial_image_wmsvec_parcel_filter = fields.Boolean(
        related="company_id.aerial_image_wmsvec_parcel_filter",
        readonly=False,
    )
    aerial_image_wmsvec_property_name = fields.Char(
        related="company_id.aerial_image_wmsvec_property_name",
        readonly=False,
    )
    aerial_image_wmsvec_property_filter = fields.Boolean(
        related="company_id.aerial_image_wmsvec_property_filter",
        readonly=False,
    )
    aerial_image_height = fields.Integer(related="company_id.aerial_image_height", readonly=False)
    aerial_image_zoom = fields.Float(
        related="company_id.aerial_image_zoom",
        readonly=False,
        digits=(32, 4),
    )
    gis_viewer_url = fields.Char(related="company_id.gis_viewer_url", readonly=False)
    gis_viewer_username = fields.Char(related="company_id.gis_viewer_username", readonly=False)
    gis_viewer_password = fields.Char(related="company_id.gis_viewer_password", readonly=False)
    gis_viewer_epsg = fields.Integer(related="company_id.gis_viewer_epsg", readonly=False)
    gis_viewer_previs_additional_args = fields.Char(
        related="company_id.gis_viewer_previs_additional_args",
        readonly=False,
    )
    ter_unit_sequence_id = fields.Many2one(related="company_id.ter_unit_sequence_id", readonly=False)


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
