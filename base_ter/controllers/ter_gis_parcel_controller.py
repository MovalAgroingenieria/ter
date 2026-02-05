# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

import psycopg2

from odoo import http
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class TerGisParcelController(http.Controller):
    def _extract_parcel_object_data(self, parcel, source):
        """Extract data from a ter.parcel recordset."""
        user_lang = request.env.user.lang
        if source in ("ter", "combined"):
            parcel = parcel.with_context(lang=user_lang)

        return {
            "name": parcel.name or "",
            "geom_geojson": getattr(parcel, "geom_geojson", None),
            "parcel_id": parcel.id,
            "municipality": (
                parcel.municipality_id.display_name if parcel.municipality_id else ""
            ),
            "area": parcel.area_official_m2 or 0.0,
            "area_gis": parcel.area_gis or 0.0,
            "area_official": parcel.area_official,
            "area_unit": parcel.area_unit_name,
            "place_name": parcel.place_id.display_name if parcel.place_id else "",
            "off_code": parcel.official_code or "",
            "partnerlinks": [
                {
                    "partner_name": pl.partner_id.display_name,
                    "partner_id": pl.partner_id.id,
                    "partner_code": pl.partner_id.partner_code,
                    "profile_name": pl.profile_id.display_name,
                    "percentage": pl.percentage,
                }
                for pl in parcel.partnerlink_ids
            ],
        }

    def _format_parcel_data(self, parcel, source):
        """Format parcel data for JSON response."""
        if isinstance(parcel, dict):
            # GIS parcel from database query
            parcel_data = {
                "name": parcel.get("name") or "",
                "geom_geojson": parcel.get("geom_geojson"),
                "parcel_id": None,
                "municipality": "",
                "area": 0.0,
                "area_gis": 0.0,
                "area_official": False,
                "area_unit": "",
                "place_name": "",
                "partnerlinks": [],
                "off_code": "",
            }
        else:
            # ter.parcel recordset
            parcel_data = self._extract_parcel_object_data(parcel, source)

        data = {"name": parcel_data["name"]}

        if source in ("gis", "combined"):
            data["geometry"] = parcel_data["geom_geojson"]

        if source in ("ter", "combined"):
            data.update(
                {
                    "parcel_id": parcel_data["parcel_id"],
                    "munici": parcel_data["municipality"],
                    "area": parcel_data["area"],
                    "area_gis": parcel_data["area_gis"],
                    "area_official": parcel_data["area_official"],
                    "area_unit": parcel_data["area_unit"],
                    "place_name": parcel_data["place_name"],
                    "partnerlinks": parcel_data["partnerlinks"],
                    "off_code": parcel_data["off_code"],
                }
            )
        elif source == "gis":
            data.update(
                {
                    "parcel_id": None,
                    "munici": "",
                    "area": 0.0,
                    "off_code": "",
                }
            )

        return data

    def _get_gis_parcels(self, name_values, operator):
        cr = request.env.cr

        if operator == "ilike":
            where_clause = " OR ".join(["name ILIKE %s" for _ in name_values])
            params = [f"%{value}%" for value in name_values]
        else:
            where_clause = " OR ".join(["name = %s" for _ in name_values])
            params = list(name_values)

        query = f"""
            SELECT name, ST_AsGeoJSON(geom) AS geom_geojson, gid
            FROM ter_gis_parcel
            WHERE {where_clause}
        """

        try:
            cr.execute(query, params)
        except psycopg2.Error:
            cr.rollback()
            _logger.exception("Error fetching GIS parcels")
            return []

        return cr.dictfetchall()

    def _validate_parcel_request(self, kwargs):
        """Validate parcel request parameters.

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

    def _combine_parcel_data(self, gis_parcels, ter_parcels):
        """Combine GIS and TER parcel data.

        Returns:
            list: Combined parcel data
        """
        gis_parcel_map = {p["name"]: p for p in gis_parcels if p.get("name")}
        ter_parcel_map = {p.name: p for p in ter_parcels if p.name}
        all_names = set(gis_parcel_map) | set(ter_parcel_map)

        combined_data = []
        for parcel_name in sorted(all_names):
            gis_parcel = gis_parcel_map.get(parcel_name)
            ter_parcel = ter_parcel_map.get(parcel_name)

            if gis_parcel and ter_parcel:
                combined_data.append(
                    self._format_parcel_data(ter_parcel, source="combined")
                )
            elif gis_parcel:
                combined_data.append(self._format_parcel_data(gis_parcel, source="gis"))
            else:
                combined_data.append(self._format_parcel_data(ter_parcel, source="ter"))

        return combined_data

    @http.route("/get_parcels", type="json", auth="user", methods=["POST"], csrf=False)
    def get_parcels(self, **kwargs):
        """Get parcels from GIS and TER sources."""
        name_values, operator, error_response = self._validate_parcel_request(kwargs)
        if error_response:
            return error_response

        domains = [[("name", operator, value)] for value in name_values]
        domain = expression.OR(domains) if len(domains) > 1 else domains[0]

        try:
            gis_parcels = self._get_gis_parcels(name_values, operator)
            ter_parcels = request.env["ter.parcel"].search(domain)
            combined_data = self._combine_parcel_data(gis_parcels, ter_parcels)
            return {"status": "success", "data": combined_data}
        except (psycopg2.Error, ValueError, KeyError):
            _logger.exception("Unexpected error in /get_parcels")
            return {
                "status": "error",
                "error": request.env._(
                    "Unexpected error while processing the request."
                ),
            }
