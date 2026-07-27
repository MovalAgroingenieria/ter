# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

import psycopg2
from odoo import http
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class TerGisUnitUseController(http.Controller):
    @http.route(
        "/get_unit_uses", type="json", auth="user", methods=["POST"], csrf=False
    )
    def get_unit_uses(self, **kwargs):
        """Get unit uses from GIS and TER sources."""
        lang = self._get_lang_from_kwargs(kwargs)
        name_values, operator, error_response = self._validate_unit_use_request(kwargs)
        if error_response:
            return error_response
        name_domain = self._build_name_domain(name_values, operator)
        try:
            gis_unit_uses = self._get_gis_unit_uses(name_values, operator)
            ter_unit_uses = (
                request.env["ter.use_unit"].with_context(lang=lang).search(name_domain)
            )
            combined_data = self._combine_unit_use_data(gis_unit_uses, ter_unit_uses)
            return {"data": combined_data}
        except (psycopg2.Error, ValueError, KeyError):
            _logger.exception("Unexpected error in /get_unit_uses")
            return {
                "error": request.env._(
                    "Unexpected error while processing the request."
                ),
            }

    def _get_lang_from_kwargs(self, kwargs):
        """Return request language from JSON-RPC context or default es_ES."""
        context = kwargs.get("context")
        if isinstance(context, dict):
            return context.get("lang") or "es_ES"
        return "es_ES"

    def _validate_unit_use_request(self, kwargs):
        """Validate unit use request parameters.

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
                    "error": request.env._('Invalid operator. Use "=" or "ilike".'),
                },
            )

        if not name:
            return (
                None,
                None,
                {
                    "error": request.env._("Name field is mandatory."),
                },
            )

        name_values = [value.strip() for value in name.split(",") if value.strip()]
        if not name_values:
            return (
                None,
                None,
                {
                    "error": request.env._("Name field is mandatory."),
                },
            )

        return name_values, operator, None

    def _build_name_domain(self, name_values, operator):
        domains = [[("name", operator, value)] for value in name_values]
        return expression.OR(domains) if len(domains) > 1 else domains[0]

    def _get_gis_unit_uses(self, name_values, operator):
        """Fetch GIS unit uses by unit-use name."""
        cr = request.env.cr

        if operator == "ilike":
            where_clause = " OR ".join(["tu.name ILIKE %s" for _ in name_values])
            params = [f"%{value}%" for value in name_values]
        else:
            where_clause = " OR ".join(["tu.name = %s" for _ in name_values])
            params = list(name_values)

        query = f"""
            SELECT tu.name, ST_AsGeoJSON(tgu.geom) AS geom_geojson, tgu.gid
            FROM ter_gis_unit tgu
            JOIN ter_use_unit tu ON tu.id = tgu.unit_id
            WHERE {where_clause}
        """

        try:
            cr.execute(query, params)
        except psycopg2.Error:
            cr.rollback()
            _logger.exception("Error fetching GIS unit uses")
            return []

        return cr.dictfetchall()

    def _combine_unit_use_data(self, gis_unit_uses, ter_unit_uses):
        """Combine GIS and TER unit use data.

        Returns:
            list: Combined unit use data
        """
        gis_unit_use_map = {u["name"]: u for u in gis_unit_uses if u.get("name")}
        ter_unit_use_map = {u.name: u for u in ter_unit_uses if u.name}
        all_names = set(gis_unit_use_map) | set(ter_unit_use_map)

        combined_data = []
        for unit_use_name in sorted(all_names):
            gis_unit_use = gis_unit_use_map.get(unit_use_name)
            ter_unit_use = ter_unit_use_map.get(unit_use_name)

            if gis_unit_use and ter_unit_use:
                combined_data.append(
                    self._format_combined_unit_use(ter_unit_use, gis_unit_use)
                )
            elif gis_unit_use:
                combined_data.append(self._format_gis_unit_use(gis_unit_use))
            else:
                combined_data.append(self._format_private_unit_use(ter_unit_use))

        return combined_data

    def _format_gis_unit_use(self, gis_unit_use):
        """Format GIS-only unit use (public information)."""
        return {
            "name": gis_unit_use.get("name") or "",
            "gid": gis_unit_use.get("gid"),
            "geometry": gis_unit_use.get("geom_geojson"),
            "unit_use_id": None,
        }

    def _format_private_unit_use(self, ter_unit_use):
        """Format private unit use when no GIS record is available."""
        return {
            "name": ter_unit_use.name or "",
            "gid": None,
            "geometry": getattr(ter_unit_use, "geom_geojson", None),
            "unit_use_id": ter_unit_use.id,
        }

    def _format_combined_unit_use(self, ter_unit_use, gis_unit_use):
        """Format combined unit use with GIS geometry and private identifier."""
        return {
            "name": ter_unit_use.name or "",
            "gid": gis_unit_use.get("gid"),
            "geometry": gis_unit_use.get("geom_geojson"),
            "unit_use_id": ter_unit_use.id,
        }
