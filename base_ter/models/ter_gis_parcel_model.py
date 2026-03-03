# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from psycopg2 import sql

from .. import hooks as base_ter_hooks


class TerGisParcelModel(models.Model):
    _name = "ter.gis.parcel.model"
    _description = "GIS Parcel"
    _auto = False
    _log_access = True

    def init(self):
        # Table ter_gis_parcel is created in pre_init_hook; view must exist
        # when Odoo checks. ter_parcel must exist too (depends on load order).
        if not base_ter_hooks._table_exists(self.env, "public", "ter_gis_parcel"):
            return
        if not base_ter_hooks._table_exists(self.env, "public", "ter_parcel"):
            return
        self.env.cr.execute(
            sql.SQL(
                """
                CREATE OR REPLACE VIEW {} AS (
                    SELECT
                        row_number() OVER (ORDER BY tgp.name) AS id,
                        tgp.name,
                        ST_AsGeoJSON(tgp.geom) AS geom_geojson,
                        tp.id AS parcel_id,
                        tp.partner_id AS partner_id,
                        tp.active AS is_active,
                        NULL::integer AS create_uid,
                        NOW() AT TIME ZONE 'UTC' AS create_date,
                        NULL::integer AS write_uid,
                        NOW() AT TIME ZONE 'UTC' AS write_date
                    FROM {}.{} tgp
                    LEFT JOIN ter_parcel tp ON tgp.name = tp.name
                )
                """
            ).format(
                sql.Identifier("ter_gis_parcel_model"),
                sql.Identifier("public"),
                sql.Identifier("ter_gis_parcel"),
            )
        )

    _aerial_image_size_small = 128

    name = fields.Char(string="Parcel Code", readonly=True)
    geom_geojson = fields.Char(string="GeoJSON Geometry", readonly=True)

    parcel_id = fields.Many2one(
        comodel_name="ter.parcel",
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Parcel Partner",
        readonly=True,
    )
    is_active = fields.Boolean(string="Active", readonly=True)

    diff_areas_threshold_exceeded = fields.Boolean(
        string="Threshold exceeded (difference between official and GIS areas)",
        related="parcel_id.diff_areas_threshold_exceeded",
        readonly=True,
    )
    diff_areas_threshold_exceeded_str = fields.Char(
        string="Threshold exceeded (difference between official and GIS areas) -str-",
        compute="_compute_diff_areas_threshold_exceeded_str",
        readonly=True,
    )

    gis_data = fields.Text(
        string="GIS Data", compute="_compute_gis_data", readonly=True
    )

    aerial_image_small = fields.Image(
        string="Aerial Image (small size)",
        max_width=_aerial_image_size_small,
        max_height=_aerial_image_size_small,
        related="parcel_id.aerial_image_small",
        readonly=True,
    )

    @api.depends("parcel_id", "parcel_id.diff_areas_threshold_exceeded")
    def _compute_diff_areas_threshold_exceeded_str(self):
        for record in self:
            if not record.parcel_id:
                record.diff_areas_threshold_exceeded_str = ""
                continue

            record.diff_areas_threshold_exceeded_str = (
                self.env.__("CHECK")
                if record.diff_areas_threshold_exceeded
                else self.env._("ok")
            )

    @api.depends(
        "parcel_id",
        "parcel_id.area_official_m2",
        "parcel_id.area_gis",
        "parcel_id.perimeter_gis",
        "parcel_id.bounding_box_str",
    )
    def _compute_gis_data(self):
        formatter = self.env["common.format"]
        for record in self:
            parcel = record.parcel_id
            if not parcel:
                record.gis_data = ""
                continue

            bbox = parcel.bounding_box_str or ""
            bbox = bbox[bbox.find("(") :] if "(" in bbox else bbox

            record.gis_data = "\n".join(
                [
                    "⸰ %s: %s"
                    % (
                        self.env._("Official Area (m²)"),
                        formatter.transform_integer_to_locale(parcel.area_official_m2),
                    ),
                    "⸰ %s: %s"
                    % (
                        self.env._("GIS Area (m²)"),
                        formatter.transform_integer_to_locale(parcel.area_gis),
                    ),
                    "⸰ %s: %s"
                    % (
                        self.env._("GIS Perimeter (m)"),
                        formatter.transform_integer_to_locale(parcel.perimeter_gis),
                    ),
                    "⸰ %s" % bbox,
                ]
            )
