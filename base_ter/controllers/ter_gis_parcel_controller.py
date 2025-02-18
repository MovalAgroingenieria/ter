# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import http, _
from odoo.http import request


class TerGisParcelController(http.Controller):

    def _format_parcel_data(self, parcel, source):
        data = {'name': parcel.name}
        if source in ['gis', 'combined']:
            data['geometry'] = parcel.geom_geojson
        if source in ['ter', 'combined']:
            data.update({
                'parcel_id': parcel.id,
                'munici': (parcel.municipality_id.name
                           if parcel.municipality_id else ''),
                'area': (parcel.area_official_m2
                         if parcel.area_official_m2 else 0.0),
                'area_official': parcel.area_official,
                'area_unit': parcel.area_unit_name,
                'place_name': (parcel.place_id.name
                               if parcel.place_id else ''),
                'partnerlinks': parcel.partnerlink_ids.mapped(
                    lambda pl: {
                        'partner_name': pl.partner_id.name,
                        'partner_id': pl.partner_id.id,
                        'partner_code': pl.partner_id.partner_code,
                        'profile_name': pl.profile_id.name,
                        'percentage': pl.percentage,
                    }
                ),
                'off_code': (parcel.official_code
                             if parcel.official_code else ''),
            })
        if source == 'gis':
            data.update({
                'parcel_id': None,
                'munici': '',
                'area': 0.0,
                'off_code': '',
            })
        return data

    def _get_gis_parcels(self, name_values, operator):
        cr = request.env.cr
        gis_parcels = []
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
                FROM ter_gis_parcel
                WHERE {where_clause}
            """
            cr.execute(query, params)
            results = cr.dictfetchall()
            for result in results:
                gis_parcels.append({
                    'name': result['name'],
                    'geom_geojson': result['geom_geojson'],
                    'gid': result['gid'],
                })
        except Exception as e:
            http.request._cr.rollback()
        return gis_parcels

    @http.route(
        '/get_parcels', type='json', auth='user', methods=['POST'], csrf=False)
    def get_parcels(self, **kwargs):
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
            if len(name_values) == 1:
                domain = [('name', operator, name)]
            else:
                domain = ['|'] * (len(name_values) - 1) + [
                    ('name', operator, value) for value in name_values]
            # gis_parcels = request.env['ter.gis.parcel.model'].search(domain)
            gis_parcels = self._get_gis_parcels(name_values, operator)
            ter_parcels = request.env['ter.parcel'].search(domain)
            gis_parcel_map = {p['name']: p for p in gis_parcels}
            ter_parcel_map = {p.name: p for p in ter_parcels}
            gis_parcel_names = set(gis_parcel_map.keys())
            ter_parcel_names = set(ter_parcel_map.keys())
            all_names = gis_parcel_names.union(ter_parcel_names)
            combined_data = []
            for name in all_names:
                gis_parcel = gis_parcel_map.get(name)
                ter_parcel = ter_parcel_map.get(name)
                if gis_parcel and ter_parcel:
                    combined_data.append(
                        self._format_parcel_data(
                            ter_parcel, source='combined'))
                elif gis_parcel:
                    combined_data.append(
                        self._format_parcel_data(gis_parcel, source='gis'))
                elif ter_parcel:
                    combined_data.append(
                        self._format_parcel_data(
                            ter_parcel, source='ter'))
            return {
                'status': 'success',
                'data': combined_data,
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': _(f'Unexpected error: {str(e)}'),
            }
