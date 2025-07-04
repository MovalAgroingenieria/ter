# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .models.res_config_settings import DEF_INT_PERC
from odoo import api, SUPERUSER_ID, exceptions, _


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Initial condition: does "ter_gis_parcel" exist?
    exists_ter_gis_parcel = True
    try:
        env.cr.execute('SELECT name, geom FROM public.ter_gis_parcel LIMIT 1')
    except Exception:
        exists_ter_gis_parcel = False
    if not exists_ter_gis_parcel:
        raise exceptions.MissingError(
            _('ATTENTION: it is not possible to install this module, because '
              'the table "ter_gis_parcel" does not exist (the parcels do not '
              'have GIS links).'))
    # EPSG code.
    epsg = 25830
    env.cr.execute("""
        SELECT value FROM ir_config_parameter
        WHERE key = 'base_ter.gis_viewer_epsg'""")
    query_results = env.cr.dictfetchall()
    if (query_results and
       query_results[0].get('value') is not None):
        raw_epsg = query_results[0].get('value').splitlines()[0]
        if raw_epsg[0] == 'I' and len(raw_epsg) > 1:
            raw_epsg = raw_epsg[1:]
            if raw_epsg.isdigit():
                epsg = int(raw_epsg)
    # Creation of the "ter_gis_sigpac" table.
    env.cr.execute("""
        CREATE SEQUENCE IF NOT EXISTS public.ter_gis_sigpac_gid_seq
            INCREMENT 1
            START 1
            MINVALUE 1
            MAXVALUE 2147483647
            CACHE 1""")
    env.cr.execute("""
        CREATE TABLE IF NOT EXISTS public.ter_gis_sigpac(
            gid INTEGER NOT NULL DEFAULT NEXTVAL(
                'ter_gis_sigpac_gid_seq'::regclass),
            dn_oid NUMERIC(18,0),
            provincia NUMERIC(4,0),
            municipio NUMERIC(6,0),
            agregado NUMERIC(6,0),
            zona NUMERIC(4,0),
            poligono NUMERIC(6,0),
            parcela NUMERIC(11,0),
            recinto NUMERIC(11,0),
            dn_surface NUMERIC(20,8),
            dn_perim NUMERIC(20,8),
            pend_media NUMERIC(6,0),
            coef_admis NUMERIC(6,0),
            coef_rega NUMERIC(6,0),
            uso_sigpac CHARACTER VARYING(2),
            incidencia CHARACTER VARYING(50),
            region CHARACTER VARYING(4),
            geom POSTGIS.GEOMETRY(Polygon,%s),
            CONSTRAINT ter_gis_sigpac_pkey PRIMARY KEY (gid))""", (epsg,))
    env.cr.execute("""
        CREATE INDEX IF NOT EXISTS ter_gis_sigpac_idx
        ON public.ter_gis_sigpac USING gist (geom)""")
    # Creation of the "ter_sigpac" materialized-view (and indexes).
    env.cr.execute("""
        CREATE MATERIALIZED VIEW ter_sigpac AS
        (SELECT row_number() OVER () AS id,
        TO_CHAR(provincia, 'fm00') || '-' ||
        TO_CHAR(municipio, 'fm000') || '-' ||
        TO_CHAR(agregado, 'fm0000') || '-' ||
        TO_CHAR(zona, 'fm000') || '-' ||
        TO_CHAR(poligono, 'fm000') || '-' ||
        TO_CHAR(parcela, 'fm00000') || '-' ||
        TO_CHAR(recinto, 'fm000') AS name,
        dn_oid, provincia, municipio, agregado, zona,
        poligono, parcela, recinto,
        dn_surface, (dn_surface/10000) AS dn_surface_ha, dn_perim,
        pend_media, (pend_media/10) AS pend_media_porc,
        COALESCE(coef_admis, 0) AS coef_admis,
        COALESCE(coef_rega, 0) AS coef_rega,
        uso_sigpac,
        COALESCE(incidencia, '') AS incidencia,
        COALESCE(region, '') AS region
        FROM ter_gis_sigpac
        WHERE uso_sigpac IN ('AG', 'CA', 'CF', 'CI', 'CS', 'CV', 'ED',
                            'EP', 'FF', 'FL', 'FO', 'FS', 'FV', 'FY', 'IM',
                            'IV','MT', 'OC',
                            'OF', 'OV', 'PA', 'PR', 'PS', 'TA', 'TH', 'VF',
                            'VI', 'VO', 'ZC', 'ZU', 'ZV'))
    """)
    env.cr.execute("""
        CREATE UNIQUE INDEX ter_sigpac_id_index
        ON ter_sigpac (id)""")
    env.cr.execute("""
        CREATE INDEX ter_sigpac_name_index
        ON ter_sigpac (name)""")
    env.cr.execute("""
        CREATE MATERIALIZED VIEW ter_parcel_sigpaclink AS(
            SELECT row_number() OVER () AS id,
                p.name || '-' || s.name AS name,
                p.id AS parcel_id,
                s.id AS sigpac_id,
                c.id AS municipality_id,
                postgis.ST_AREA(gp.geom) AS parcel_area,
                postgis.ST_AREA(gs.geom) AS sigpac_area,
                postgis.ST_AREA(postgis.ST_INTERSECTION(gp.geom, gs.geom)) AS area,
                (postgis.ST_AREA(postgis.ST_INTERSECTION(gp.geom, gs.geom)) / 10000)
                AS area_ha, 100 * postgis.ST_AREA(postgis.ST_INTERSECTION(gp.geom, gs.geom))
                / postgis.ST_AREA(gp.geom) AS intersection_percentage,
                s.pend_media_porc,
                s.coef_admis,
                s.coef_rega,
                s.uso_sigpac,
                s.incidencia,
                s.region,
                postgis.ST_INTERSECTION(gp.geom, gs.geom) AS geom,
                gs.gid AS sigpac_gid
            FROM ter_gis_parcel gp
            INNER JOIN ter_parcel p ON p.name = gp.name
            INNER JOIN res_municipality c ON p.municipality_id = c.id,
                ter_gis_sigpac gs
            INNER JOIN ter_sigpac s ON s.dn_oid = gs.dn_oid
            WHERE p.active = true
            AND postgis.ST_ISVALID(gp.geom)
            AND postgis.ST_ISVALID(gs.geom)
            AND postgis.ST_INTERSECTS(gp.geom, gs.geom)
            AND postgis.ST_AREA(gp.geom) > 0
            AND (100 * postgis.ST_AREA(postgis.ST_INTERSECTION(gp.geom, gs.geom))
            / postgis.ST_AREA(gp.geom)) >= %s)""", (DEF_INT_PERC,))
    env.cr.execute("""
        CREATE UNIQUE INDEX ter_parcel_sigpaclink_id_index
        ON ter_parcel_sigpaclink (id)""")
    env.cr.execute("""
        CREATE INDEX ter_parcel_sigpaclink_name_index
        ON ter_parcel_sigpaclink (name)""")


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['ir.config_parameter'].set_param(
        'l10n_es_territory_sigpac.wms_sigpac_layer', 'recinto')
    env['ir.config_parameter'].set_param(
        'l10n_es_territory_sigpac.wms_sigpac_url',
        'https://wms.mapa.gob.es/sigpac/wms')
    env['ir.config_parameter'].set_param(
        'l10n_es_territory_sigpac.sigpac_minimum_intersection_percentage', 5.0)
    env['ir.config_parameter'].set_param(
        'l10n_es_territory_sigpac.sigpac_viewer_url',
        'https://sigpac.mapa.es/fega/visor/#&visible=Inicio-SigPac;'
        '1/2.000.000;1/200.000;Ortofotos;1/25.000;Recinto&provincia='
        '{{ object.provincia }}&municipio={{ object.municipio }}&poligono='
        '{{ object.poligono }}&parcela={{ object.parcela }}&recinto='
        '{{ object.recinto }}&agregado={{ object.agregado }}'
        '&zona={{ object.zona }}')
    env['ir.config_parameter'].set_param(
        'l10n_es_territory_sigpac.sigpac_minimum_intersection_percentage',
        '/home/odoo16/venv3.10/bin/python')


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
            DELETE FROM ir_config_parameter
            WHERE key LIKE 'l10n_es_territory_sigpac.%'
        """)
        env.cr.commit()
    except Exception:
        env.cr.rollback()
    env.cr.execute("""
        ALTER TABLE ter_parcel
            DROP COLUMN IF EXISTS number_of_sigpaclinks,
            DROP COLUMN IF EXISTS parcel_title_sigpac,
            DROP COLUMN IF EXISTS aerial_img_sigpac,
            DROP COLUMN IF EXISTS aerial_img_sigpac_shown,
            DROP COLUMN IF EXISTS aerial_img_sigpac_scale;
    """)
    env.cr.execute('DROP TABLE IF EXISTS public.ter_gis_sigpac CASCADE')
    env.cr.execute('DROP SEQUENCE IF EXISTS public.ter_gis_sigpac_gid_seq')
