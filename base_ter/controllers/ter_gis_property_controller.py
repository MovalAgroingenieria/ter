# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import http, _
from odoo.http import request


class TerGisPropertyController(http.Controller):

    def _format_property_data(self, property, source):
        data = {'name': property.name}
        if source in ['gis', 'combined']:
            data['geometry'] = property.geom_geojson
        if source in ['ter', 'combined']:
            data.update({
                'property_id': property.id,
                'munici': (property.municipality_id.name
                           if property.municipality_id else ''),
                'area': (property.area_official_parcels_m2
                         if property.area_official_parcels_m2 else 0.0),
                'area_official_parcels': property.area_official_parcels,
                'area_unit': property.area_unit_name,
                'partner_name': property.partner_id.name,
                'partner_code': property.partner_id.partner_code,
                'partner_id': property.partner_id.id,
                'parcels': property.parcel_ids.mapped(
                    lambda p: {
                        'parcel_name': p.name,
                        'parcel_id': p.id,
                    }
                ),
            })
        if source == 'gis':
            data.update({
                'property_id': None,
                'munici': '',
                'area': 0.0,
            })
        return data

    def _get_gis_properties(self, name_values, operator):
        cr = request.env.cr
        gis_properties = []
        try:
            if operator == 'ilike':
                where_clause = " OR ".join(
                    ["name ILIKE %s" for _ in name_values]
                )
                params = [f"%{value}%" for value in name_values]
            else:
                where_clause = " OR ".join(
                    ["name = %s" for _ in name_values]
                )
                params = name_values
            query = f"""
                SELECT name, ST_AsGeoJSON(geom) as geom_geojson, gid
                FROM ter_gis_property
                WHERE {where_clause}
            """
            cr.execute(query, params)
            results = cr.dictfetchall()
            for result in results:
                gis_properties.append({
                    'name': result['name'],
                    'geom_geojson': result['geom_geojson'],
                    'gid': result['gid'],
                })
        except Exception as e:
            http.request._cr.rollback()
        return gis_properties

    @http.route(
        '/get_properties', type='json', auth='user', methods=['POST'],
        csrf=False)
    def get_properties(self, **kwargs):
        try:
            name = kwargs.get('name', '')
            operator = kwargs.get('operator', '=')
            if operator not in ['=', 'ilike']:
                return {
                    'status': 'error',
                    'error': _('Invalid operators. Use "=" or "ilike".')
                }
            if not name:
                return {
                    'status': 'error',
                    'error': _('Name field is mandatory.')
                }
            name_values = [value.strip() for value in name.split(',')]
            gis_properties = self._get_gis_properties(name_values, operator)
            domain = ['|'] * (len(name_values) - 1) + [
                ('name', operator, value) for value in name_values]
            ter_properties = request.env['ter.property'].search(domain)
            gis_property_map = {p['name']: p for p in gis_properties}
            ter_property_map = {p.name: p for p in ter_properties}
            gis_property_names = set(gis_property_map.keys())
            ter_property_names = set(ter_property_map.keys())
            all_names = gis_property_names.union(ter_property_names)
            combined_data = []
            for name in all_names:
                gis_property = gis_property_map.get(name)
                ter_property = ter_property_map.get(name)
                if gis_property and ter_property:
                    combined_data.append(
                        self._format_property_data(
                            ter_property, source='combined'))
                elif gis_property:
                    combined_data.append({
                        'name': gis_property['name'],
                        'geometry': gis_property['geom_geojson'],
                        'property_id': None,
                        'munici': '',
                        'area': 0.0,
                    })
                elif ter_property:
                    combined_data.append(
                        self._format_property_data(
                            ter_property, source='ter'))
            return {
                'status': 'success',
                'data': combined_data,
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': _(f'Unexpected error: {e}'),
            }
