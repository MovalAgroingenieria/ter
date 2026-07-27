# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from psycopg2 import sql

import json

from odoo import api, fields, models


class PointGisPointModel(models.Model):
    _name = "point.gis.point.model"
    _description = "GIS Point"
    _auto = False
    _log_access = True

    name = fields.Char(readonly=True)
    geom_geojson = fields.Text(readonly=True)
    point_id = fields.Many2one("point.point", readonly=True)
    partner_id = fields.Many2one("res.partner", readonly=True)
    is_active = fields.Boolean(readonly=True)
    gis_data = fields.Text(compute="_compute_gis_data")

    @api.depends("geom_geojson")
    def _compute_gis_data(self):
        for record in self:
            values = {}
            if record.geom_geojson:
                try:
                    geojson = json.loads(record.geom_geojson)
                    values["coordinates"] = geojson.get("coordinates")
                    values["type"] = geojson.get("type")
                except ValueError:
                    values["coordinates"] = False
            record.gis_data = json.dumps(values)

    def init(self):
        self.env.cr.execute("SELECT to_regclass('public.point_gis_point')")
        has_point_table = bool(self.env.cr.fetchone()[0])

        if not has_point_table:
            self.env.cr.execute(
                sql.SQL(
                    """
                    CREATE OR REPLACE VIEW {} AS (
                        SELECT
                            row_number() OVER (ORDER BY pp.name) AS id,
                            pp.name,
                            NULL::text AS geom_geojson,
                            pp.id AS point_id,
                            pp.partner_id AS partner_id,
                            pp.active AS is_active,
                            NULL::integer AS create_uid,
                            NOW() AT TIME ZONE 'UTC' AS create_date,
                            NULL::integer AS write_uid,
                            NOW() AT TIME ZONE 'UTC' AS write_date
                        FROM point_point pp
                    )
                    """
                ).format(sql.Identifier("point_gis_point_model"))
            )
            return

        self.env.cr.execute(
            sql.SQL(
                """
                CREATE OR REPLACE VIEW {} AS (
                    SELECT
                        row_number() OVER (ORDER BY pgp.name) AS id,
                        pgp.name,
                        postgis.st_asgeojson(pgp.geom) AS geom_geojson,
                        pp.id AS point_id,
                        pp.partner_id AS partner_id,
                        pp.active AS is_active,
                        NULL::integer AS create_uid,
                        NOW() AT TIME ZONE 'UTC' AS create_date,
                        NULL::integer AS write_uid,
                        NOW() AT TIME ZONE 'UTC' AS write_date
                    FROM {}.{} pgp
                    LEFT JOIN point_point pp ON pgp.name = pp.name
                )
                """
            ).format(
                sql.Identifier("point_gis_point_model"),
                sql.Identifier("public"),
                sql.Identifier("point_gis_point"),
            )
        )
