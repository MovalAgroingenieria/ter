# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import http, _
from odoo.http import request

class TerGisParcelController(http.Controller):

    def _format_parcel_data(self, parcel):
        return {
            'name': parcel.name,
            'geom': parcel.geom_geojson,
            'parcel_id': parcel.parcel_id.id if parcel.parcel_id else False,
            'munici': parcel.parcel_id.municipality_id.name if
                parcel.parcel_id else '',
            'area': parcel.parcel_id.area_official_m2 if
                parcel.parcel_id else 0.0,
            'off_code': parcel.parcel_id.official_code if
                parcel.parcel_id else '',
        }

    @http.route(
        '/get_parcels', type='json', auth='user', methods=['POST'], csrf=False)
    def get_parcels(self, **kwargs):
        try:
            name = kwargs.get('name', '')
            operator = kwargs.get('operator', '=')
            if operator not in ['=', 'ilike']:
                return {
                    'status': 'error',
                    'error': _('Invalid operators Use "=" or "ilike".')
                }
            if not name:
                return {
                    'status': 'error',
                    'error': _('Name field is mandatory.')
                }
            parcel_data = []
            name_values = [value.strip() for value in name.split(',')]
            if (len(name_values) == 1):
                domain = [('name', operator, name)]
            else:
                domain = ['|'] * (len(name_values) - 1) + [
                    ('name', operator, value) for value in name_values]
            parcels = request.env['ter.gis.parcel.model'].search(domain)
            parcel_data = [
                self._format_parcel_data(parcel) for parcel in parcels]
            return {
                'status': 'success',
                'data': parcel_data
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': _(f'Unexpected error: {str(e)}')
            }
