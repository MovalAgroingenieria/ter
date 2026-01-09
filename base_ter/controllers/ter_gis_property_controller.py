# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import _, http
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class TerGisPropertyController(http.Controller):
    def _format_property_data(self, prop, source):
        user_lang = request.env.user.lang

        if isinstance(prop, dict):
            name = prop.get("name") or ""
            geom_geojson = prop.get("geom_geojson")
            prop_id = None
            municipality = ""
            area = 0.0
            area_official_parcels = False
            area_unit = ""
            partner_name = ""
            partner_code = ""
            partner_id = None
            parcels = []
        else:
            if source in ("ter", "combined"):
                prop = prop.with_context(lang=user_lang)

            name = prop.name or ""
            geom_geojson = getattr(prop, "geom_geojson", None)
            prop_id = prop.id
            municipality = prop.municipality_id.display_name if prop.municipality_id else ""
            area = prop.area_official_parcels_m2 or 0.0
            area_official_parcels = prop.area_official_parcels
            area_unit = prop.area_unit_name

            partner = prop.partner_id
            partner_name = partner.display_name if partner else ""
            partner_code = partner.partner_code if partner else ""
            partner_id = partner.id if partner else None

            parcels = [{"parcel_name": p.name, "parcel_id": p.id} for p in prop.parcel_ids]

        data = {"name": name}

        if source in ("gis", "combined"):
            data["geometry"] = geom_geojson

        if source in ("ter", "combined"):
            data.update(
                {
                    "property_id": prop_id,
                    "munici": municipality,
                    "area": area,
                    "area_official_parcels": area_official_parcels,
                    "area_unit": area_unit,
                    "partner_name": partner_name,
                    "partner_code": partner_code,
                    "partner_id": partner_id,
                    "parcels": parcels,
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
        except Exception:
            cr.rollback()
            _logger.exception("Error fetching GIS properties")
            return []

        return cr.dictfetchall()

    @http.route("/get_properties", type="json", auth="user", methods=["POST"], csrf=False)
    def get_properties(self, **kwargs):
        name = (kwargs.get("name") or "").strip()
        operator = kwargs.get("operator") or "="

        if operator not in ("=", "ilike"):
            return {
                "status": "error",
                "error": _('Invalid operator. Use "=" or "ilike".'),
            }

        if not name:
            return {"status": "error", "error": _("Name field is mandatory.")}

        name_values = [value.strip() for value in name.split(",") if value.strip()]
        if not name_values:
            return {"status": "error", "error": _("Name field is mandatory.")}

        domains = [[("name", operator, value)] for value in name_values]
        domain = expression.OR(domains) if len(domains) > 1 else domains[0]

        try:
            gis_properties = self._get_gis_properties(name_values, operator)
            ter_properties = request.env["ter.property"].search(domain)

            gis_property_map = {p["name"]: p for p in gis_properties if p.get("name")}
            ter_property_map = {p.name: p for p in ter_properties if p.name}

            all_names = set(gis_property_map) | set(ter_property_map)

            combined_data = []
            for prop_name in sorted(all_names):
                gis_prop = gis_property_map.get(prop_name)
                ter_prop = ter_property_map.get(prop_name)

                if gis_prop and ter_prop:
                    combined_data.append(self._format_property_data(ter_prop, source="combined"))
                elif gis_prop:
                    combined_data.append(self._format_property_data(gis_prop, source="gis"))
                else:
                    combined_data.append(self._format_property_data(ter_prop, source="ter"))

            return {"status": "success", "data": combined_data}
        except Exception:
            _logger.exception("Unexpected error in /get_properties")
            return {"status": "error", "error": _("Unexpected error while processing the request.")}
