# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, fields, models
from psycopg2 import Error as PsycopgError
from psycopg2 import sql


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    area_unit_is_ha = fields.Boolean(
        related="company_id.area_unit_is_ha", readonly=False
    )
    area_unit_name = fields.Char(related="company_id.area_unit_name", readonly=False)
    area_unit_value_in_ha = fields.Float(
        related="company_id.area_unit_value_in_ha",
        readonly=False,
        digits=(32, 4),
    )
    warning_diff_areas = fields.Integer(
        related="company_id.warning_diff_areas", readonly=False
    )
    same_parcelmanager_propertyowner = fields.Boolean(
        related="company_id.same_parcelmanager_propertyowner",
        readonly=False,
    )
    aerial_image_wmsvec_url = fields.Char(
        related="company_id.aerial_image_wmsvec_url", readonly=False
    )
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
    ter_unit_sequence_id = fields.Many2one(
        related="company_id.ter_unit_sequence_id", readonly=False
    )

    def _on_gis_epsg_changed(self, old_epsg, new_epsg):
        """Reproject territory PostGIS layers."""
        super()._on_gis_epsg_changed(old_epsg, new_epsg)
        ok, details = self.update_geometry(old_epsg, new_epsg)
        if not ok:
            raise exceptions.UserError(
                self.env._(
                    "Unable to update geometry: %(details)s",
                    details=details,
                )
            )
        return None

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
        except PsycopgError as err:
            return False, f"{layer}\n\nERROR:\n\n{err}"
        return True, ""

    @api.model
    def _set_layers_to_update_geometry(self):
        return [
            "ter_gis_parcel",
            "ter_gis_property",
        ]
