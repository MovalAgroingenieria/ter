# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

import psycopg2
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)


def validate_name_request(kwargs):
    """Validate name/operator from request kwargs.

    Returns:
        tuple: (name_values, operator, error_response)
            error_response is None if validation passed
    """
    name = (kwargs.get("name") or "").strip()
    operator = kwargs.get("operator") or "="

    if operator not in ("=", "ilike"):
        return (
            None,
            None,
            {
                "status": "error",
                "error": request.env._('Invalid operator. Use "=" or "ilike".'),
            },
        )

    if not name:
        return (
            None,
            None,
            {
                "status": "error",
                "error": request.env._("Name field is mandatory."),
            },
        )

    name_values = [value.strip() for value in name.split(",") if value.strip()]
    if not name_values:
        return (
            None,
            None,
            {
                "status": "error",
                "error": request.env._("Name field is mandatory."),
            },
        )

    return name_values, operator, None


def build_name_domain(name_values, operator):
    """Build OR domain for name field from values and operator."""
    domains = [[("name", operator, value)] for value in name_values]
    return expression.OR(domains) if len(domains) > 1 else domains[0]


def build_where_clause_and_params(name_values, operator):
    """Build SQL WHERE clause and params for name filter (parcels/properties)."""
    if operator == "ilike":
        where_clause = " OR ".join(["name ILIKE %s" for _ in name_values])
        params = [f"%{value}%" for value in name_values]
    else:
        where_clause = " OR ".join(["name = %s" for _ in name_values])
        params = list(name_values)
    return where_clause, params


def fetch_gis_layer(name_values, operator, table_name, log_prefix):
    """Fetch GIS layer data (parcels or properties) by name filter."""
    cr = request.env.cr
    where_clause, params = build_where_clause_and_params(name_values, operator)
    query = f"""
        SELECT name, ST_AsGeoJSON(geom) AS geom_geojson, gid
        FROM {table_name}
        WHERE {where_clause}
    """
    try:
        cr.execute(query, params)
    except psycopg2.Error:
        cr.rollback()
        _logger.exception("Error fetching GIS %s", log_prefix)
        return []
    return cr.dictfetchall()
