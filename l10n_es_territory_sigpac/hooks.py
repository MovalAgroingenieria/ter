# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import exceptions
from odoo.tools import drop_view_if_exists

DEF_INT_PERC = 5.0


def _table_exists(cr, table_name):
    cr.execute("SELECT to_regclass(%s) AS regclass", (table_name,))
    row = cr.fetchone()
    return bool(row and row[0])


def _sql_epsg_for_geom(env):
    """EPSG for POSTGIS.GEOMETRY(Polygon, srid); read from config when present."""
    epsg = 25830
    env.cr.execute("""
        SELECT value
        FROM ir_config_parameter
        WHERE key = 'base_ter.gis_viewer_epsg'
        """)
    row = env.cr.fetchone()
    if row and row[0]:
        raw_epsg = str(row[0]).splitlines()[0]
        if raw_epsg.startswith("I") and len(raw_epsg) > 1:
            raw_epsg = raw_epsg[1:]
        if raw_epsg.isdigit():
            epsg = int(raw_epsg)
    return epsg


def ensure_l10n_es_territory_sigpac_schema(env):
    """Build sequence, table, and materialized views. Idempotent: safe to run from
    pre_init_hook (first install) and from ter.sigpac.init() (install and -u).

    Odoo's pre_init runs only on first install, not on module update; without
    init(), the backing relations never appear after -u. Using public search_path
    so drop_view_if_exists / pg matviews and Odoo's check_tables_exist agree.
    """
    cr = env.cr
    if getattr(cr, "_l10n_es_territory_sigpac_schema_ensured", None):
        return
    cr.execute("SET LOCAL search_path TO public, pg_temp")

    if not _table_exists(cr, "public.ter_gis_parcel"):
        raise exceptions.MissingError(
            env._(
                "ATTENTION: it is not possible to install this module, because "
                'the table "ter_gis_parcel" does not exist (the parcels do not '
                "have GIS links)."
            )
        )

    epsg = _sql_epsg_for_geom(env)

    cr.execute("""
        CREATE SEQUENCE IF NOT EXISTS public.ter_gis_sigpac_gid_seq
            INCREMENT 1
            START 1
            MINVALUE 1
            MAXVALUE 2147483647
            CACHE 1
        """)

    cr.execute(
        """
        CREATE TABLE IF NOT EXISTS public.ter_gis_sigpac(
            gid INTEGER NOT NULL DEFAULT NEXTVAL('ter_gis_sigpac_gid_seq'::regclass),
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
            CONSTRAINT ter_gis_sigpac_pkey PRIMARY KEY (gid)
        )
        """,
        (epsg,),
    )

    cr.execute("""
        CREATE INDEX IF NOT EXISTS ter_gis_sigpac_idx
        ON public.ter_gis_sigpac USING gist (geom)
        """)

    # Dependent MV first, then base MV (same order as uninstall & deps).
    drop_view_if_exists(cr, "ter_parcel_sigpaclink")
    drop_view_if_exists(cr, "ter_sigpac")

    cr.execute("""
        CREATE MATERIALIZED VIEW public.ter_sigpac AS
        (
            SELECT row_number() OVER () AS id,
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
            FROM public.ter_gis_sigpac
            WHERE uso_sigpac IN ('AG', 'CA', 'CF', 'CI', 'CS', 'CV', 'ED',
                                'EP', 'FF', 'FL', 'FO', 'FS', 'FV', 'FY', 'IM',
                                'IV','MT', 'OC',
                                'OF', 'OV', 'PA', 'PR', 'PS', 'TA', 'TH', 'VF',
                                'VI', 'VO', 'ZC', 'ZU', 'ZV')
        )
        """)

    cr.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ter_sigpac_id_index
        ON public.ter_sigpac (id)
        """)
    cr.execute("""
        CREATE INDEX IF NOT EXISTS ter_sigpac_name_index
        ON public.ter_sigpac (name)
        """)

    cr.execute(
        """
        CREATE MATERIALIZED VIEW public.ter_parcel_sigpaclink AS(
            SELECT row_number() OVER () AS id,
                p.name || '-' || s.name AS name,
                p.id AS parcel_id,
                s.id AS sigpac_id,
                c.id AS municipality_id,
                postgis.ST_AREA(gp.geom) AS parcel_area,
                postgis.ST_AREA(gs.geom) AS sigpac_area,
                postgis.ST_AREA(postgis.ST_INTERSECTION(gp.geom, gs.geom)) AS area,
                (postgis.ST_AREA(postgis.ST_INTERSECTION(gp.geom, gs.geom)) / 10000)
                    AS area_ha,
                100 * postgis.ST_AREA(postgis.ST_INTERSECTION(gp.geom, gs.geom))
                    / postgis.ST_AREA(gp.geom) AS intersection_percentage,
                s.pend_media_porc,
                s.coef_admis,
                s.coef_rega,
                s.uso_sigpac,
                s.incidencia,
                s.region,
                postgis.ST_INTERSECTION(gp.geom, gs.geom) AS geom,
                gs.gid AS sigpac_gid
            FROM public.ter_gis_parcel gp
            INNER JOIN public.ter_parcel p ON p.name = gp.name
            INNER JOIN public.res_municipality c ON p.municipality_id = c.id,
                public.ter_gis_sigpac gs
            INNER JOIN public.ter_sigpac s ON s.dn_oid = gs.dn_oid
            WHERE p.active = true
            AND postgis.ST_ISVALID(gp.geom)
            AND postgis.ST_ISVALID(gs.geom)
            AND postgis.ST_INTERSECTS(gp.geom, gs.geom)
            AND postgis.ST_AREA(gp.geom) > 0
            AND (100 * postgis.ST_AREA(postgis.ST_INTERSECTION(gp.geom, gs.geom))
                / postgis.ST_AREA(gp.geom)) >= %s
        )
        """,
        (DEF_INT_PERC,),
    )

    cr.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ter_parcel_sigpaclink_id_index
        ON public.ter_parcel_sigpaclink (id)
        """)
    cr.execute("""
        CREATE INDEX IF NOT EXISTS ter_parcel_sigpaclink_name_index
        ON public.ter_parcel_sigpaclink (name)
        """)

    cr._l10n_es_territory_sigpac_schema_ensured = (  # pylint: disable=protected-access
        True
    )  # type: ignore[attr-defined]


def pre_init_hook(env):
    ensure_l10n_es_territory_sigpac_schema(env)


def post_init_hook(env):
    default_sigpac_viewer_url = (
        "https://sigpac.mapa.es/fega/visor/#&visible=Inicio-SigPac;"
        "1/2.000.000;1/200.000;Ortofotos;1/25.000;Recinto&provincia="
        "{{ object.provincia }}&municipio={{ object.municipio }}&poligono="
        "{{ object.poligono }}&parcela={{ object.parcela }}&recinto="
        "{{ object.recinto }}&agregado={{ object.agregado }}"
        "&zona={{ object.zona }}"
    )

    companies = env["res.company"].sudo().search([])
    for company in companies:
        values = {}
        if not company.wms_sigpac_layer:
            values["wms_sigpac_layer"] = "recinto"
        if not company.wms_sigpac_url:
            values["wms_sigpac_url"] = "https://wms.mapa.gob.es/sigpac/wms"
        if not company.sigpac_minimum_intersection_percentage:
            values["sigpac_minimum_intersection_percentage"] = DEF_INT_PERC
        if not company.sigpac_viewer_url:
            values["sigpac_viewer_url"] = default_sigpac_viewer_url
        if not company.python_venv_url:
            values["python_venv_url"] = "python3"
        if values:
            company.write(values)


def uninstall_hook(env):
    with env.cr.savepoint():
        env.cr.execute("SET LOCAL search_path TO public, pg_temp")
        env.cr.execute(
            "DROP MATERIALIZED VIEW IF EXISTS public.ter_parcel_sigpaclink CASCADE"
        )
        env.cr.execute("DROP MATERIALIZED VIEW IF EXISTS public.ter_sigpac CASCADE")
        env.cr.execute("DROP TABLE IF EXISTS public.ter_gis_sigpac CASCADE")
        env.cr.execute("DROP SEQUENCE IF EXISTS public.ter_gis_sigpac_gid_seq CASCADE")
