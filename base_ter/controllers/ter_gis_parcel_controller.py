# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import _, http
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class TerGisParcelController(http.Controller):
    def _format_parcel_data(self, parcel, source):
        user_lang = request.env.user.lang

        if isinstance(parcel, dict):
            name = parcel.get("name") or ""
            geom_geojson = parcel.get("geom_geojson")
            parcel_id = None
            municipality = ""
            area = 0.0
            area_gis = 0.0
            area_official = False
            area_unit = ""
            place_name = ""
            partnerlinks = []
            off_code = ""
        else:
            if source in ("ter", "combined"):
                parcel = parcel.with_context(lang=user_lang)

            name = parcel.name or ""
            geom_geojson = getattr(parcel, "geom_geojson", None)
            parcel_id = parcel.id
            municipality = parcel.municipality_id.display_name if parcel.municipality_id else ""
            area = parcel.area_official_m2 or 0.0
            area_gis = parcel.area_gis or 0.0
            area_official = parcel.area_official
            area_unit = parcel.area_unit_name
            place_name = parcel.place_id.display_name if parcel.place_id else ""
            off_code = parcel.official_code or ""

            partnerlinks = [
                {
                    "partner_name": pl.partner_id.display_name,
                    "partner_id": pl.partner_id.id,
                    "partner_code": pl.partner_id.partner_code,
                    "profile_name": pl.profile_id.display_name,
                    "percentage": pl.percentage,
                }
                for pl in parcel.partnerlink_ids
            ]

        data = {"name": name}

        if source in ("gis", "combined"):
            data["geometry"] = geom_geojson

        if source in ("ter", "combined"):
            data.update(
                {
                    "parcel_id": parcel_id,
                    "munici": municipality,
                    "area": area,
                    "area_gis": area_gis,
                    "area_official": area_official,
                    "area_unit": area_unit,
                    "place_name": place_name,
                    "partnerlinks": partnerlinks,
                    "off_code": off_code,
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
        except Exception:
            cr.rollback()
            _logger.exception("Error fetching GIS parcels")
            return []

        return cr.dictfetchall()

    @http.route("/get_parcels", type="json", auth="user", methods=["POST"], csrf=False)
    def get_parcels(self, **kwargs):
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
            gis_parcels = self._get_gis_parcels(name_values, operator)
            ter_parcels = request.env["ter.parcel"].search(domain)

            gis_parcel_map = {p["name"]: p for p in gis_parcels if p.get("name")}
            ter_parcel_map = {p.name: p for p in ter_parcels if p.name}

            all_names = set(gis_parcel_map) | set(ter_parcel_map)

            combined_data = []
            for parcel_name in sorted(all_names):
                gis_parcel = gis_parcel_map.get(parcel_name)
                ter_parcel = ter_parcel_map.get(parcel_name)

                if gis_parcel and ter_parcel:
                    combined_data.append(self._format_parcel_data(ter_parcel, source="combined"))
                elif gis_parcel:
                    combined_data.append(self._format_parcel_data(gis_parcel, source="gis"))
                else:
                    combined_data.append(self._format_parcel_data(ter_parcel, source="ter"))

            return {"status": "success", "data": combined_data}
        except Exception:
            _logger.exception("Unexpected error in /get_parcels")
            return {"status": "error", "error": _("Unexpected error while processing the request.")}
