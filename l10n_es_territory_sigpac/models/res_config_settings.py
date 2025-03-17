# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import glob
import os
import subprocess
import logging
from odoo import models, fields, api, tools, exceptions, _

DEF_INT_PERC = 5.0


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sigpac_path = fields.Char(
        string='Path of the SIGPAC shapefiles',
        size=255,
        help='Path of the official shapefiles of SIGPAC, in the server',
        config_parameter='l10n_es_territory_sigpac.sigpac_path')

    sigpac_names = fields.Char(
        string='Names of the SIGPAC shapefiles',
        help='Names of the official shapefiles of SIGPAC (separated by '
             'commas)',
        config_parameter='l10n_es_territory_sigpac.sigpac_names')

    sigpac_minimum_intersection_percentage = fields.Float(
        string='Minimum intersection percentage',
        default=DEF_INT_PERC,
        digits=(32, 4),
        required=True,
        help='Minimum intersection percentage allowed for parcels and SIGPAC '
             'enclosures',
        config_parameter='l10n_es_territory_sigpac.'
        'sigpac_minimum_intersection_percentage')

    sigpac_use_venv310 = fields.Boolean(
        string='venv310 (python)',
        config_parameter='l10n_es_territory_sigpac.sigpac_use_venv310')

    _sql_constraints = [
        ('valid_minimum_intersection_percentage',
         'CHECK (sigpac_minimum_intersection_percentage >= 0 '
         'and sigpac_minimum_intersection_percentage <= 100)',
         'The minimum intersection percentage must be a value between '
         '0 and 100.'),
        ]

    def action_load_sigpac(self):
        self.ensure_one()
        # Apply changes.
        self.execute()
        # Load SIGPAC.
        exit_code, message_error = self.load_sigpac()
        # Show tree view.
        if exit_code == 0:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Parcels'),
                'res_model': 'ter.parcel',
                'view_mode': 'tree,form',
                'target': 'current',
                'context': self.env.context,
            }
        else:
            raise exceptions.UserError(
                _('Loading SIGPAC enclosures: failed process '
                  '(error code: %s), message:\n%s') %
                (exit_code, message_error))

    @api.model
    def load_sigpac(self):
        # if exit_code is 0 then there is no error.
        exit_code = 0
        message_error = ''
        # Get parameters.
        model_ir_config = self.env['ir.config_parameter'].sudo()
        sigpac_path = model_ir_config.get_param(
            'l10n_es_territory_sigpac.sigpac_path')
        if ((not sigpac_path) or sigpac_path == ''):
            return -1, _('One or more shapefiles not found.')
        sigpac_names = model_ir_config.get_param(
            'l10n_es_territory_sigpac.sigpac_names')
        if (not sigpac_names):
            sigpac_names = ''
        else:
            sigpac_names = sigpac_names.strip()
        sigpac_use_venv310 = model_ir_config.get_param(
            'l10n_es_territory_sigpac.sigpac_use_venv310')
        # Get shapefiles and conditions.
        shp_list = self._get_shp_list(sigpac_path, sigpac_names)
        if (not shp_list):
            return -1, _('One or more shapefiles not found.')
        # Get parameters for ogr2ogr.
        host, port, user, password, dbname, srs = self._get_ogr_params()
        # Import features, step 1: empty "ter_gis_table".
        self.env.cr.execute('TRUNCATE TABLE ter_gis_sigpac')
        # Import features, step 2: rebuild the "ter_parcel_sigpaclink"
        # materiazed view.
        sigpac_minimum_intersection_percentage = model_ir_config.get_param(
            'l10n_es_territory_sigpac.sigpac_minimum_intersection_percentage')
        self._rebuild_ter_parcel_sigpaclink_view(
            sigpac_minimum_intersection_percentage)
        # Import features, step 3: call the program "load_sigpac".
        program_path = \
            '{}/../static/python/load_sigpac.py'.format(
                os.path.dirname(__file__))
        shptoimport = ''
        for shp in shp_list:
            shptoimport = shptoimport + '#' + shp['shapefile']
            if shp['condition'] != '':
                shptoimport = shptoimport + '(' + shp['condition'] + ')'
        shptoimport = shptoimport[1:]
        external_program = 'python'
        if sigpac_use_venv310:
            external_program = '/home/odoo10/venv3.10/bin/python'
        list_of_args = [external_program, program_path, host,
                        str(port), dbname, user, password,
                        shptoimport, str(srs)]
        python_ok = True
        try:
            subprocess.Popen(list_of_args)
        except Exception:
            python_ok = False
            exit_code = 1
            message_error = 'Python Error'
        if python_ok:
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info('load_sigpac.py (ogr2ogr) for... ' +
                         ' '.join([str(x) for x in list_of_args]))
        return exit_code, message_error

    def _get_shp_list(self, sigpac_path, sigpac_names):
        resp = []
        if sigpac_path == '' or sigpac_path[-1] != '/':
            sigpac_path = sigpac_path + '/'
        if sigpac_names == '':
            shapefiles = glob.glob(sigpac_path + '*.shp')
            for shapefile in (shapefiles or []):
                resp.append({'shapefile': shapefile,
                             'condition': ''})
        else:
            shapefiles = sigpac_names.split(',')
            for shapefile in shapefiles:
                condition = ''
                pos_initial_bracket = shapefile.find('(')
                if pos_initial_bracket != -1:
                    pos_final_bracket = shapefile.find(')')
                    if (pos_final_bracket != -1 and
                       pos_initial_bracket < pos_final_bracket):
                        condition = shapefile[
                            pos_initial_bracket + 1: pos_final_bracket]
                        shapefile = shapefile[:pos_initial_bracket]
                shapefile = sigpac_path + shapefile
                if os.path.isfile(shapefile):
                    resp.append({'shapefile': shapefile,
                                 'condition': condition})
                else:
                    resp = []
                    break
        return resp

    def _get_ogr_params(self):
        host = tools.config['db_host']
        port = tools.config['db_port']
        user = tools.config['db_user']
        password = tools.config['db_password']
        dbname = self.env.cr.dbname
        srs = self.env['ir.default'].get(
            'res.config.settings', 'url_gis_viewer_epsg_code')
        if not srs:
            srs = 25830
        return host, port, user, password, dbname, srs

    def _rebuild_ter_parcel_sigpaclink_view(
            self, minimum_intersection_percentage=DEF_INT_PERC):
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS ter_parcel_sigpaclink""")
        self.env.cr.execute("""
            CREATE MATERIALIZED VIEW ter_parcel_sigpaclink AS(
            SELECT gp.gid AS id,
                p.name || '-' || s.name AS name,
                p.id AS parcel_id,
                s.id AS sigpac_id,
                c.id AS municipality_id,
                ST_AREA(gp.geom) AS parcel_area,
                ST_AREA(gs.geom) AS sigpac_area,
                ST_AREA(ST_INTERSECTION(gp.geom, gs.geom)) AS area,
                (ST_AREA(ST_INTERSECTION(gp.geom, gs.geom)) / 10000) AS area_ha,
                100 * ST_AREA(ST_INTERSECTION(gp.geom, gs.geom)) / ST_AREA(gp.geom) AS intersection_percentage,
                s.pend_media_porc,
                s.coef_admis,
                s.coef_rega,
                s.uso_sigpac,
                s.incidencia,
                s.region,
                s.grp_cult,
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
            AND ST_AREA(gp.geom) > 0
            AND (100 * ST_AREA(ST_INTERSECTION(gp.geom, gs.geom)) / ST_AREA(gp.geom)) >= %s)""",(minimum_intersection_percentage,))
        self.env.cr.execute("""
            CREATE UNIQUE INDEX ter_parcel_sigpaclink_id_index
            ON ter_parcel_sigpaclink (id)""")
        self.env.cr.execute("""
            CREATE INDEX ter_parcel_sigpaclink_name_index
            ON ter_parcel_sigpaclink (name)""")
