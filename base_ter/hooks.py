# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, SUPERUSER_ID, _


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Precondition: PostGis must be installed
    resp = False
    env.cr.execute("""
        SELECT EXISTS(SELECT * FROM pg_extension WHERE extname='postgis')
        AND EXISTS(SELECT * FROM information_schema.schemata  WHERE
        schema_name='postgis')
        """)
    result = env.cr.fetchone()[0]
    if result and result != 'f':
        resp = True
    if not resp:
        raise exceptions.ValidationError(_(
            'PostGIS not installed. Please contact your administrator to '
            'install it before proceeding.'))
    # Update the variable "search_path" of PostgreSQL
    env.cr.execute('ALTER DATABASE ' + env.cr.dbname +
                   ' SET search_path = public, postgis')


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Creation of the GIS tables (ter_gis_parcel and ter_gis_property)
    env.cr.execute("""
        CREATE SEQUENCE IF NOT EXISTS public.ter_gis_parcel_gid_seq
            INCREMENT 1
            START 1
            MINVALUE 1
            MAXVALUE 2147483647
            CACHE 1
        """)
    env.cr.execute("""
        CREATE TABLE IF NOT EXISTS public.ter_gis_parcel(
            gid INTEGER NOT NULL DEFAULT NEXTVAL(
                'ter_gis_parcel_gid_seq'::regclass),
            name CHARACTER VARYING(255) NOT NULL,
            geom postgis.geometry(MultiPolygon, 25830),
            UNIQUE(name),
            CHECK (name <> ''),
            CONSTRAINT ter_gis_parcel_pkey PRIMARY KEY (gid))
        """)
    env.cr.execute("""
        CREATE INDEX IF NOT EXISTS ter_gis_parcel_idx
        ON public.ter_gis_parcel USING gist (geom)
        """)
    env.cr.execute("""
        CREATE TABLE IF NOT EXISTS public.ter_gis_property(
            gid INTEGER NOT NULL,
            name CHARACTER VARYING(255) NOT NULL,
            geom postgis.geometry(MultiPolygon, 25830),
            UNIQUE(name),
            CHECK (name <> ''),
            CONSTRAINT ter_gis_property_pkey PRIMARY KEY (gid))
        """)
    env.cr.execute("""
        CREATE INDEX IF NOT EXISTS ter_gis_property_idx
        ON public.ter_gis_property USING gist (geom)
        """)
    # Creation of SQL views.
    env.cr.execute("""
        CREATE VIEW ter_gis_parcel_model AS (
        SELECT ROW_NUMBER() OVER() AS id, tgp.name,
        postgis.st_asgeojson(tgp.geom) AS geom_geojson,
        tp.id AS parcel_id,
        tp.partner_id as partner_id, tp.active as is_active
        FROM ter_gis_parcel tgp LEFT JOIN ter_parcel tp
        ON tgp.name = tp.name
        WHERE tp.partner_id IS NOT NULL OR tp.partner_id IS NULL
        ORDER BY tgp.name)
        """)
    # Parameter initialization.
    env['ir.config_parameter'].set_param(
        'base_ter.area_unit_is_ha', True)
    env['ir.config_parameter'].set_param(
        'base_ter.area_unit_name', 'ha')
    env['ir.config_parameter'].set_param(
        'base_ter.area_unit_value_in_ha', 1)
    env['ir.config_parameter'].set_param(
        'base_ter.warning_diff_areas', 10)
    env['ir.config_parameter'].set_param(
        'base_ter.same_parcelmanager_propertyowner', False)
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_wmsbase_url',
        'https://www.ign.es/wms-inspire/pnoa-ma')
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_wmsbase_layers', 'OI.OrthoimageCoverage')
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_wmsvec_url',
        'https://gis.moval.es/wms/my_client')
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_wmsvec_parcel_name', 'parcel_perimeter')
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_wmsvec_parcel_filter', True)
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_wmsvec_property_name', 'property_perimeter')
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_wmsvec_property_filter', True)
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_height', 512)
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_zoom', 1.2)
    env['ir.config_parameter'].set_param(
        'base_ter.gis_viewer_url', 'https://gis.moval.es/my_client/visor')
    env['ir.config_parameter'].set_param(
        'base_ter.gis_viewer_username', 'tecnico')
    env['ir.config_parameter'].set_param(
        'base_ter.gis_viewer_password', 'my_password')
    env['ir.config_parameter'].set_param(
        'base_ter.gis_viewer_epsg', 25830)
    env['ir.config_parameter'].set_param(
        'base_ter.gis_viewer_previs_additional_args', 'mode=min')
    # Load i18n_extra.
    env.ref('base.module_base_ter')._update_translations(
        overwrite=True)


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Delete the views
    env.cr.execute("""
        DROP VIEW IF EXISTS ter_gis_parcel_model
        """)
    # Delete the GIS tables
    env.cr.execute("""
        DROP TABLE IF EXISTS ter_gis_parcel
        """)
    env.cr.execute("""
        DROP TABLE IF EXISTS ter_gis_property
        """)
    # Delete parameters of module to uninstall.
    try:
        env.cr.savepoint()
        env.cr.execute("DELETE FROM ir_config_parameter "
                       "WHERE key LIKE 'base_ter.%'")
        env.cr.commit()
    except Exception:
        env.cr.rollback()
