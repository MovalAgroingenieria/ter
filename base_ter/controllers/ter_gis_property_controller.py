# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

import psycopg2

from odoo import http
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class TerGisPropertyController(http.Controller):
    def _extract_property_object_data(self, prop, source):
        """Extract data from a ter.property recordset."""
        user_lang = request.env.user.lang
        if source in ("ter", "combined"):
            prop = prop.with_context(lang=user_lang)

        partner = prop.partner_id
        return {
            "name": prop.name or "",
            "geom_geojson": getattr(prop, "geom_geojson", None),
            "prop_id": prop.id,
            "municipality": (
                prop.municipality_id.display_name if prop.municipality_id else ""
            ),
            "area": prop.area_official_parcels_m2 or 0.0,
            "area_official_parcels": prop.area_official_parcels,
            "area_unit": prop.area_unit_name,
            "partner_name": partner.display_name if partner else "",
            "partner_code": partner.partner_code if partner else "",
            "partner_id": partner.id if partner else None,
            "parcels": [
                {"parcel_name": p.name, "parcel_id": p.id} for p in prop.parcel_ids
            ],
        }

    def _format_property_data(self, prop, source):
        """Format property data for JSON response."""
        if isinstance(prop, dict):
            # GIS property from database query
            prop_data = {
                "name": prop.get("name") or "",
                "geom_geojson": prop.get("geom_geojson"),
                "prop_id": None,
                "municipality": "",
                "area": 0.0,
                "area_official_parcels": False,
                "area_unit": "",
                "partner_name": "",
                "partner_code": "",
                "partner_id": None,
                "parcels": [],
            }
        else:
            # ter.property recordset
            prop_data = self._extract_property_object_data(prop, source)

        data = {"name": prop_data["name"]}

        if source in ("gis", "combined"):
            data["geometry"] = prop_data["geom_geojson"]

        if source in ("ter", "combined"):
            data.update(
                {
                    "property_id": prop_data["prop_id"],
                    "munici": prop_data["municipality"],
                    "area": prop_data["area"],
                    "area_official_parcels": prop_data["area_official_parcels"],
                    "area_unit": prop_data["area_unit"],
                    "partner_name": prop_data["partner_name"],
                    "partner_code": prop_data["partner_code"],
                    "partner_id": prop_data["partner_id"],
                    "parcels": prop_data["parcels"],
                }
            )
        elif source == "gis":
            data.update({"property_id": None, "munici": "", "area": 0.0})

        return data

    def _get_gis_properties(self, name_values, operator):
        cr = request.env.cr

        if operator == "ilike":
            where_clause = " OR ".join(["name ILIKE %s" for _ in name_values])
            params = [f"%{value}%" for value in name_values]
        else:
            where_clause = " OR ".join(["name = %s" for _ in name_values])
            params = list(name_values)

        query = f"""
            SELECT name, ST_AsGeoJSON(geom) AS geom_geojson, gid
            FROM ter_gis_property
            WHERE {where_clause}
        """

        try:
            cr.execute(query, params)
        except psycopg2.Error:
            cr.rollback()
            _logger.exception("Error fetching GIS properties")
            return []

        return cr.dictfetchall()

    def _validate_property_request(self, kwargs):
        """Validate property request parameters.

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

    def _combine_property_data(self, gis_properties, ter_properties):
        """Combine GIS and TER property data.

        Returns:
            list: Combined property data
        """
        gis_property_map = {p["name"]: p for p in gis_properties if p.get("name")}
        ter_property_map = {p.name: p for p in ter_properties if p.name}
        all_names = set(gis_property_map) | set(ter_property_map)

        combined_data = []
        for prop_name in sorted(all_names):
            gis_prop = gis_property_map.get(prop_name)
            ter_prop = ter_property_map.get(prop_name)

            if gis_prop and ter_prop:
                combined_data.append(
                    self._format_property_data(ter_prop, source="combined")
                )
            elif gis_prop:
                combined_data.append(self._format_property_data(gis_prop, source="gis"))
            else:
                combined_data.append(self._format_property_data(ter_prop, source="ter"))

        return combined_data

    @http.route(
        "/get_properties", type="json", auth="user", methods=["POST"], csrf=False
    )
    def get_properties(self, **kwargs):
        """Get properties from GIS and TER sources."""
        name_values, operator, error_response = self._validate_property_request(kwargs)
        if error_response:
            return error_response

        domains = [[("name", operator, value)] for value in name_values]
        domain = expression.OR(domains) if len(domains) > 1 else domains[0]

        try:
            gis_properties = self._get_gis_properties(name_values, operator)
            ter_properties = request.env["ter.property"].search(domain)
            combined_data = self._combine_property_data(gis_properties, ter_properties)
            return {"status": "success", "data": combined_data}
        except (psycopg2.Error, ValueError, KeyError):
            _logger.exception("Unexpected error in /get_properties")
            return {
                "status": "error",
                "error": request.env._(
                    "Unexpected error while processing the request."
                ),
            }
