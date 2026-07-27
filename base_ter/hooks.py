# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=line-too-long,protected-access

from __future__ import annotations

import logging

from odoo import api
from odoo.exceptions import ValidationError
from psycopg2 import sql

_logger = logging.getLogger(__name__)

POSTGIS_EXT = "postgis"
POSTGIS_SCHEMA = "postgis"

GIS_SCHEMA = "public"
PARCEL_TABLE = "ter_gis_parcel"
PROPERTY_TABLE = "ter_gis_property"
UNIT_TABLE = "ter_gis_unit"
PARCEL_VIEW = "ter_gis_parcel_model"

PARAM_PREFIX = "base_ter."
PARAM_DEFAULTS = {
    f"{PARAM_PREFIX}area_unit_is_ha": True,
    f"{PARAM_PREFIX}area_unit_name": "ha",
    f"{PARAM_PREFIX}area_unit_value_in_ha": 1,
    f"{PARAM_PREFIX}warning_diff_areas": 10,
    f"{PARAM_PREFIX}same_parcelmanager_propertyowner": False,
    f"{PARAM_PREFIX}aerial_image_wmsvec_url": "https://gis.moval.es/wms/my_client",
    f"{PARAM_PREFIX}aerial_image_wmsvec_parcel_name": "parcel_perimeter",
    f"{PARAM_PREFIX}aerial_image_wmsvec_parcel_filter": True,
    f"{PARAM_PREFIX}aerial_image_wmsvec_property_name": "property_perimeter",
    f"{PARAM_PREFIX}aerial_image_wmsvec_property_filter": True,
    f"{PARAM_PREFIX}aerial_image_wmsvec_unit_name": "unit_perimeter",
    f"{PARAM_PREFIX}aerial_image_wmsvec_unit_filter": True,
}


def _postgis_extension_exists(env: api.Environment) -> bool:
    env.cr.execute(
        "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = %s)",
        (POSTGIS_EXT,),
    )
    return bool(env.cr.fetchone()[0])


def _geometry_type_exists_any_schema(env: api.Environment) -> bool:
    env.cr.execute("SELECT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'geometry')")
    return bool(env.cr.fetchone()[0])


def _set_search_path(env: api.Environment) -> None:
    env.cr.execute(
        sql.SQL("ALTER DATABASE {} SET search_path = public, {}").format(
            sql.Identifier(env.cr.dbname),
            sql.Identifier(POSTGIS_SCHEMA),
        )
    )
    env.cr.execute(
        sql.SQL("SET search_path TO public, {}").format(sql.Identifier(POSTGIS_SCHEMA))
    )


def _grant_postgis_privileges(env: api.Environment) -> None:
    env.cr.execute(
        sql.SQL("GRANT USAGE ON SCHEMA {} TO public").format(
            sql.Identifier(POSTGIS_SCHEMA)
        )
    )
    env.cr.execute(
        sql.SQL(
            "GRANT SELECT, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA {} TO public"
        ).format(sql.Identifier(POSTGIS_SCHEMA))
    )
    env.cr.execute(
        sql.SQL("GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA {} TO public").format(
            sql.Identifier(POSTGIS_SCHEMA)
        )
    )


def _ensure_postgis(env: api.Environment) -> None:
    try:
        env.cr.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                sql.Identifier(POSTGIS_SCHEMA)
            )
        )
        env.cr.execute(
            sql.SQL("CREATE EXTENSION IF NOT EXISTS {}").format(
                sql.Identifier(POSTGIS_EXT)
            )
        )
        env.cr.execute(
            sql.SQL("ALTER EXTENSION {} SET SCHEMA {}").format(
                sql.Identifier(POSTGIS_EXT),
                sql.Identifier(POSTGIS_SCHEMA),
            )
        )
        _set_search_path(env)
        _grant_postgis_privileges(env)
    except Exception as exc:
        raise ValidationError(
            env._(
                "PostGIS could not be enabled in this database. "
                "Install PostGIS on PostgreSQL and ensure the DB user can run "
                "CREATE EXTENSION."
            )
        ) from exc

    if not _postgis_extension_exists(env) or not _geometry_type_exists_any_schema(env):
        raise ValidationError(
            env._(
                "PostGIS is not available in this database. "
                "Install/enable PostGIS and retry."
            )
        )


def _column_exists(
    env: api.Environment, schema: str, table_name: str, column_name: str
) -> bool:
    env.cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s AND column_name = %s
        """,
        (schema, table_name, column_name),
    )
    return bool(env.cr.fetchone())


def _geometry_udt_columns(
    env: api.Environment, schema: str, table_name: str
) -> list[str]:
    env.cr.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s AND udt_name = %s
        ORDER BY ordinal_position
        """,
        (schema, table_name, "geometry"),
    )
    return [row[0] for row in env.cr.fetchall()]


def _ensure_gis_table_geom_column(env: api.Environment, table_name: str) -> None:
    """Align legacy / restored GIS tables with the expected ``geom`` column.

    Restored databases (e.g. v16) may already have ``ter_gis_parcel`` without
    ``geom`` (older layout) or with PostGIS defaults like ``the_geom``.
    ``CREATE TABLE IF NOT EXISTS`` does not add missing columns.
    """
    if not _table_exists(env, GIS_SCHEMA, table_name):
        return
    if _column_exists(env, GIS_SCHEMA, table_name, "geom"):
        return
    geom_cols = _geometry_udt_columns(env, GIS_SCHEMA, table_name)
    legacy_priority = ("the_geom", "wkb_geometry", "shape")
    for legacy in legacy_priority:
        if legacy in geom_cols:
            env.cr.execute(
                sql.SQL("ALTER TABLE {}.{} RENAME COLUMN {} TO geom").format(
                    sql.Identifier(GIS_SCHEMA),
                    sql.Identifier(table_name),
                    sql.Identifier(legacy),
                )
            )
            return
    if len(geom_cols) == 1:
        only = geom_cols[0]
        env.cr.execute(
            sql.SQL("ALTER TABLE {}.{} RENAME COLUMN {} TO geom").format(
                sql.Identifier(GIS_SCHEMA),
                sql.Identifier(table_name),
                sql.Identifier(only),
            )
        )
        return
    if len(geom_cols) > 1:
        _logger.warning(
            "base_ter: table %s.%s has multiple geometry columns %s; "
            "adding empty geom column (merge geometries manually if needed)",
            GIS_SCHEMA,
            table_name,
            geom_cols,
        )
    env.cr.execute(
        sql.SQL(
            "ALTER TABLE {}.{} ADD COLUMN IF NOT EXISTS geom geometry(MultiPolygon, 25830)"
        ).format(sql.Identifier(GIS_SCHEMA), sql.Identifier(table_name))
    )


def _ensure_gis_geom_gist_index(env: api.Environment, table_name: str) -> None:
    if not _column_exists(env, GIS_SCHEMA, table_name, "geom"):
        return
    env.cr.execute(
        sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {}.{} USING gist (geom)").format(
            sql.Identifier(f"{table_name}_geom_gist"),
            sql.Identifier(GIS_SCHEMA),
            sql.Identifier(table_name),
        )
    )


def _create_gis_parcel_and_property_tables(env: api.Environment) -> None:
    """Create ter_gis_parcel and ter_gis_property tables (no FKs to Odoo tables).
    Used in pre_init_hook so the view can be created in model init().
    """
    _set_search_path(env)
    env.cr.execute(sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.{}
            (
                gid INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE CHECK (name <> ''),
                geom geometry(MultiPolygon, 25830)
            )
            """).format(sql.Identifier(GIS_SCHEMA), sql.Identifier(PARCEL_TABLE)))
    _ensure_gis_table_geom_column(env, PARCEL_TABLE)
    _ensure_gis_geom_gist_index(env, PARCEL_TABLE)
    env.cr.execute(
        sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.{}
            (
                gid INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL UNIQUE CHECK (name <> ''),
                geom geometry(MultiPolygon, 25830),
                CONSTRAINT {} PRIMARY KEY (gid)
            )
            """).format(
            sql.Identifier(GIS_SCHEMA),
            sql.Identifier(PROPERTY_TABLE),
            sql.Identifier(f"{PROPERTY_TABLE}_pkey"),
        )
    )
    _ensure_gis_table_geom_column(env, PROPERTY_TABLE)
    _ensure_gis_geom_gist_index(env, PROPERTY_TABLE)


def _create_gis_structures(env: api.Environment) -> None:
    _set_search_path(env)

    env.cr.execute(sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.{}
            (
                gid INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE CHECK (name <> ''),
                geom geometry(MultiPolygon, 25830)
            )
            """).format(sql.Identifier(GIS_SCHEMA), sql.Identifier(PARCEL_TABLE)))
    _ensure_gis_table_geom_column(env, PARCEL_TABLE)
    _ensure_gis_geom_gist_index(env, PARCEL_TABLE)

    env.cr.execute(
        sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.{}
            (
                gid INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL UNIQUE CHECK (name <> ''),
                geom geometry(MultiPolygon, 25830),
                CONSTRAINT {} PRIMARY KEY (gid)
            )
            """).format(
            sql.Identifier(GIS_SCHEMA),
            sql.Identifier(PROPERTY_TABLE),
            sql.Identifier(f"{PROPERTY_TABLE}_pkey"),
        )
    )
    _ensure_gis_table_geom_column(env, PROPERTY_TABLE)
    _ensure_gis_geom_gist_index(env, PROPERTY_TABLE)

    env.cr.execute(sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.{}
            (
                gid INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                unit_id INTEGER NOT NULL UNIQUE
                REFERENCES ter_use_unit(id) ON DELETE CASCADE,
                name VARCHAR(255),
                geom geometry(MultiPolygon, 25830)
            )
            """).format(sql.Identifier(GIS_SCHEMA), sql.Identifier(UNIT_TABLE)))
    _ensure_gis_table_geom_column(env, UNIT_TABLE)
    _ensure_gis_unit_name_column(env)
    _ensure_gis_geom_gist_index(env, UNIT_TABLE)

    env.cr.execute(
        sql.SQL("""
            CREATE OR REPLACE VIEW {} AS (
                SELECT
                    row_number() OVER (ORDER BY tgp.name) AS id,
                    tgp.name,
                    ST_AsGeoJSON(tgp.geom) AS geom_geojson,
                    tp.id AS parcel_id,
                    tp.partner_id AS partner_id,
                    tp.active AS is_active,

                    -- log_access fields required by Odoo when _log_access=True
                    NULL::integer AS create_uid,
                    NOW() AT TIME ZONE 'UTC' AS create_date,
                    NULL::integer AS write_uid,
                    NOW() AT TIME ZONE 'UTC' AS write_date
                FROM {}.{} tgp
                LEFT JOIN ter_parcel tp ON tgp.name = tp.name
            )
            """).format(
            sql.Identifier(PARCEL_VIEW),
            sql.Identifier(GIS_SCHEMA),
            sql.Identifier(PARCEL_TABLE),
        )
    )


def _ensure_gis_unit_name_column(env: api.Environment) -> None:
    """Ensure ``ter_gis_unit`` has the denormalized ``name`` column.

    The unit geometry table is keyed by ``unit_id``, but WMS layers (see the
    MapServer mapfile) and the ``gis.base.model`` computes filter by ``name``.
    So the unit's ``name`` is denormalized onto this real table (no view) and
    kept in sync by ``ter.use_unit._sync_geom_to_gis_unit``. Using the real
    table (with its ``gid`` primary key) avoids the feature-id / consistency
    issues a PostGIS view can cause in MapServer.
    """
    env.cr.execute(
        sql.SQL("ALTER TABLE {}.{} ADD COLUMN IF NOT EXISTS name VARCHAR(255)").format(
            sql.Identifier(GIS_SCHEMA), sql.Identifier(UNIT_TABLE)
        )
    )
    env.cr.execute(
        sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {}.{} (name)").format(
            sql.Identifier(f"{UNIT_TABLE}_name_idx"),
            sql.Identifier(GIS_SCHEMA),
            sql.Identifier(UNIT_TABLE),
        )
    )


def _ensure_gis_unit_table(env: api.Environment) -> None:
    """Create ter_gis_unit table if missing (e.g. after restore or partial init)."""
    _set_search_path(env)
    env.cr.execute(sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.{}
            (
                gid INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                unit_id INTEGER NOT NULL UNIQUE
                REFERENCES ter_use_unit(id) ON DELETE CASCADE,
                name VARCHAR(255),
                geom geometry(MultiPolygon, 25830)
            )
            """).format(sql.Identifier(GIS_SCHEMA), sql.Identifier(UNIT_TABLE)))
    env.cr.execute(
        sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {}.{} USING gist (geom)").format(
            sql.Identifier(f"{UNIT_TABLE}_geom_gist"),
            sql.Identifier(GIS_SCHEMA),
            sql.Identifier(UNIT_TABLE),
        )
    )
    _ensure_gis_unit_name_column(env)


def _init_params(env: api.Environment) -> None:
    params = env["ir.config_parameter"].sudo()
    for key, value in PARAM_DEFAULTS.items():
        params.set_param(key, value)


def pre_init_hook(env: api.Environment) -> None:
    _ensure_postgis(env)
    _create_gis_parcel_and_property_tables(env)


def _ensure_ter_unit_sequences(env: api.Environment) -> None:
    """Create default ter.use_unit sequence for each company that lacks one."""
    # oca-review: this unbounded search runs once at module init/upgrade and must
    # cover every company so each gets its default ter.use_unit sequence.
    env["res.company"].search([])._get_or_create_ter_unit_sequence()


def _table_exists(env: api.Environment, schema: str, table_name: str) -> bool:
    """Return True if the given table exists in the given schema."""
    env.cr.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """,
        (schema, table_name),
    )
    return bool(env.cr.fetchone())


def _migrate_ter_unit_parcel_ids(env: api.Environment) -> None:
    """Populate parcel_ids from parcel_id for existing ter.use_unit records."""
    if not _table_exists(env, "public", "ter_unit_parcel_rel"):
        return
    env.cr.execute("""
        INSERT INTO ter_unit_parcel_rel (unit_id, parcel_id)
        SELECT u.id, u.parcel_id
        FROM ter_use_unit u
        WHERE u.parcel_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM ter_unit_parcel_rel r
            WHERE r.unit_id = u.id AND r.parcel_id = u.parcel_id
        )
        """)


def _ensure_ter_profile_01(env: api.Environment) -> None:
    """Ensure default profile ter_profile_01 exists (e.g. noupdate skip or migration)."""
    env["ter.profile"]._ensure_ter_profile_01()


def post_init_hook(env: api.Environment) -> None:
    _ensure_postgis(env)
    _create_gis_structures(env)
    _init_params(env)
    _ensure_ter_profile_01(env)
    _ensure_ter_unit_sequences(env)
    _migrate_ter_unit_parcel_ids(env)


def uninstall_hook(env: api.Environment) -> None:
    env.cr.execute(
        sql.SQL("DROP VIEW IF EXISTS {}").format(sql.Identifier(PARCEL_VIEW))
    )
    env.cr.execute(
        sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
            sql.Identifier(GIS_SCHEMA),
            sql.Identifier(UNIT_TABLE),
        )
    )
    env.cr.execute(
        sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
            sql.Identifier(GIS_SCHEMA),
            sql.Identifier(PARCEL_TABLE),
        )
    )
    env.cr.execute(
        sql.SQL("DROP TABLE IF EXISTS {}.{}").format(
            sql.Identifier(GIS_SCHEMA),
            sql.Identifier(PROPERTY_TABLE),
        )
    )

    with env.cr.savepoint():
        env.cr.execute(
            "DELETE FROM ir_config_parameter WHERE key LIKE %s",
            (f"{PARAM_PREFIX}%",),
        )
    # Clean up ir_model_data entries remapped by the use-type wizard
    # (module = '__base_ter_data__') so no orphans remain after uninstall.
    with env.cr.savepoint():
        env.cr.execute("DELETE FROM ir_model_data WHERE module = '__base_ter_data__'")
