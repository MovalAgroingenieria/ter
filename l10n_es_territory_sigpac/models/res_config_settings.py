# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint:disable=too-many-locals

import glob
import logging
import os
import subprocess

import psycopg2
from odoo import api, exceptions, fields, models, tools

DEF_INT_PERC = 5.0

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sigpac_path = fields.Char(related="company_id.sigpac_path", readonly=False)
    sigpac_names = fields.Char(related="company_id.sigpac_names", readonly=False)
    sigpac_minimum_intersection_percentage = fields.Float(
        related="company_id.sigpac_minimum_intersection_percentage",
        readonly=False,
        digits=(32, 4),
        required=True,
    )
    wms_sigpac_url = fields.Char(related="company_id.wms_sigpac_url", readonly=False)
    wms_sigpac_layer = fields.Char(
        related="company_id.wms_sigpac_layer", readonly=False
    )
    sigpac_viewer_url = fields.Char(
        related="company_id.sigpac_viewer_url", readonly=False
    )
    python_venv_url = fields.Char(related="company_id.python_venv_url", readonly=False)

    @api.constrains("sigpac_minimum_intersection_percentage")
    def _check_sigpac_minimum_intersection_percentage(self):
        for record in self:
            value = record.sigpac_minimum_intersection_percentage
            if value < 0 or value > 100:
                raise exceptions.ValidationError(
                    record.env._(
                        "The minimum intersection percentage "
                        "must be a value between 0 and 100."
                    )
                )

    def action_load_sigpac(self):
        self.ensure_one()
        self.execute()

        exit_code, message_error = self.load_sigpac()
        if exit_code == 0:
            return {
                "type": "ir.actions.act_window",
                "name": self.env._("Parcels"),
                "res_model": "ter.parcel",
                "view_mode": "list,form",
                "target": "current",
                "context": self.env.context,
            }

        raise exceptions.UserError(
            self.env._(
                "Loading SIGPAC enclosures: failed process "
                "(error code: %(code)s), message:\n%(message)s",
                code=exit_code,
                message=message_error,
            )
        )

    @api.model
    def load_sigpac(self):
        company = self.env.company

        sigpac_path = company.sigpac_path or ""
        if not sigpac_path:
            return -1, self.env._("One or more shapefiles not found.")

        sigpac_names = (company.sigpac_names or "").strip()
        python_venv_url = company.python_venv_url or ""
        min_perc = company.sigpac_minimum_intersection_percentage or DEF_INT_PERC

        shp_list = self._get_shp_list(sigpac_path, sigpac_names)
        if not shp_list:
            return -1, self.env._("One or more shapefiles not found.")

        host, port, user, password, dbname, srs = self._get_ogr_params()

        self.env.cr.execute("TRUNCATE TABLE ter_gis_sigpac")
        self._rebuild_ter_parcel_sigpaclink_view(float(min_perc))

        program_path = os.path.normpath(
            os.path.join(
                os.path.dirname(__file__), "..", "static", "python", "load_sigpac.py"
            )
        )

        shptoimport = self._build_shapefiles_argument(shp_list)

        list_of_args = [
            python_venv_url,
            program_path,
            host or "",
            str(port or ""),
            dbname,
            user or "",
            password or "",
            shptoimport,
            str(srs),
        ]

        try:
            with subprocess.Popen(list_of_args) as proc:  # noqa: S603,S607
                _logger.info("load_sigpac.py launched with pid=%s", proc.pid)
        except (OSError, subprocess.SubprocessError) as err:
            _logger.exception("SIGPAC load process failed.")
            return 1, self.env._("Python Error: %(error)s", error=str(err))

        _logger.info(
            "load_sigpac.py launched with args: %s",
            " ".join([str(x) for x in list_of_args]),
        )
        return 0, ""

    def _build_shapefiles_argument(self, shp_list):
        parts = []
        for shp in shp_list:
            item = shp["shapefile"]
            condition = shp.get("condition") or ""
            if condition:
                item = f"{item}({condition})"
            parts.append(item)
        return "#".join(parts)

    def _get_shp_list(self, sigpac_path, sigpac_names):
        resp = []
        sigpac_path = sigpac_path if sigpac_path.endswith("/") else f"{sigpac_path}/"

        if not sigpac_names:
            shapefiles = glob.glob(f"{sigpac_path}*.shp")
            for shapefile in shapefiles or []:
                resp.append({"shapefile": shapefile, "condition": ""})
            return resp

        shapefiles = [x.strip() for x in sigpac_names.split(",") if x.strip()]
        for shapefile in shapefiles:
            condition = ""
            pos_initial = shapefile.find("(")
            if pos_initial != -1:
                pos_final = shapefile.find(")")
                if pos_final != -1 and pos_initial < pos_final:
                    condition = shapefile[pos_initial + 1 : pos_final]
                    shapefile = shapefile[:pos_initial].strip()

            full_path = f"{sigpac_path}{shapefile}"
            if os.path.isfile(full_path):
                resp.append({"shapefile": full_path, "condition": condition})
            else:
                return []
        return resp

    def _get_ogr_params(self):
        host = tools.config.get("db_host")
        port = tools.config.get("db_port")
        user = tools.config.get("db_user")
        password = tools.config.get("db_password")
        dbname = self.env.cr.dbname

        srs = (
            self.env["ir.default"].get(
                "res.config.settings", "url_gis_viewer_epsg_code"
            )
            or 25830
        )
        return host, port, user, password, dbname, srs

    def _rebuild_ter_parcel_sigpaclink_view(
        self, minimum_intersection_percentage=DEF_INT_PERC
    ):
        self.env.cr.execute(
            "DROP MATERIALIZED VIEW IF EXISTS ter_parcel_sigpaclink CASCADE"
        )
        self.env.cr.execute(
            """
            CREATE MATERIALIZED VIEW ter_parcel_sigpaclink AS(
            SELECT row_number() OVER () AS id,
                p.name || '-' || s.name AS name,
                p.id AS parcel_id,
                s.id AS sigpac_id,
                c.id AS municipality_id,
                ST_AREA(gp.geom) AS parcel_area,
                ST_AREA(gs.geom) AS sigpac_area,
                ST_AREA(ST_INTERSECTION(gp.geom, gs.geom)) AS area,
                (ST_AREA(ST_INTERSECTION(gp.geom, gs.geom)) / 10000) AS area_ha,
                100 * ST_AREA(ST_INTERSECTION(gp.geom, gs.geom)) /
                ST_AREA(gp.geom) AS intersection_percentage,
                s.pend_media_porc,
                s.coef_admis,
                s.coef_rega,
                s.uso_sigpac,
                s.incidencia,
                s.region,
                ST_INTERSECTION(gp.geom, gs.geom) AS geom,
                gs.gid AS sigpac_gid
            FROM ter_gis_parcel gp
            INNER JOIN ter_parcel p ON p.name = gp.name
            INNER JOIN res_municipality c ON p.municipality_id = c.id,
                ter_gis_sigpac gs
            INNER JOIN ter_sigpac s ON s.dn_oid = gs.dn_oid
            WHERE p.active = true
            AND ST_ISVALID(gp.geom)
            AND ST_ISVALID(gs.geom)
            AND ST_INTERSECTS(gp.geom, gs.geom)
            AND gs.uso_sigpac IN ('AG','CA','CF','CI','CS','CV','ED','EP',
            'FF','FL','FO','FS','FV','FY','IM','IV',
                                 'MT','OC','OF','OV','PA','PR','PS','TA',
                                 'TH','VF','VI','VO','ZC','ZU','ZV')
            AND ST_AREA(gp.geom) > 0
            AND (100 * ST_AREA(ST_INTERSECTION(gp.geom, gs.geom)) /
             ST_AREA(gp.geom)) >= %s)
            """,
            (minimum_intersection_percentage,),
        )
        self.env.cr.execute(
            "CREATE UNIQUE INDEX ter_parcel_sigpaclink_id_index "
            "ON ter_parcel_sigpaclink (id)"
        )
        self.env.cr.execute(
            "CREATE INDEX ter_parcel_sigpaclink_name_index "
            "ON ter_parcel_sigpaclink (name)"
        )
        self.env.cr.execute("REFRESH MATERIALIZED VIEW ter_parcel_sigpaclink")

    @api.model
    def update_geometry(self, old_epsg, new_epsg):
        try:
            self.env.cr.execute(
                "DROP MATERIALIZED VIEW IF EXISTS ter_parcel_sigpaclink CASCADE"
            )
        except psycopg2.Error as err:
            return (False, str(err))

        try:
            resp = super().update_geometry(old_epsg, new_epsg)
        except AttributeError:
            resp = (True, "")

        if not resp[0]:
            return resp

        try:
            perc = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("base_ter.def_int_perc", "")
            )
            self._rebuild_ter_parcel_sigpaclink_view(
                float(perc) if perc else DEF_INT_PERC
            )
        except (ValueError, psycopg2.Error) as err:
            return (False, str(err))

        return resp
