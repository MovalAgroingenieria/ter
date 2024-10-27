# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import requests
import xml.etree.ElementTree as ET

from odoo import fields, models, api, exceptions, _


class TerParcel(models.Model):
    _inherit = ['ter.parcel']

    # Size of the "official_code_urban" field in the model.
    MAX_SIZE_OFFICIAL_CODE_URBAN = 50

    # Size of a cadastral field (sector, polygon or parcel), in the model.
    MAX_SIZE_CADASTRAL_FIELD = 10

    # Size of the "rc1" part of a cadastral reference.
    SIZE_RC1 = 7

    # Size of the "rc2" part of a cadastral reference.
    SIZE_RC2 = 7

    # Timeout for the cadastral-area request (sec).
    REQUEST_TIMEOUT = 5

    # Cadastral reference: size of the cadastral code of the municipality.
    _size_municipality_cadastral_code = 5

    # Cadastral reference: size of the cadastral sector.
    _size_cadastral_sector = 1

    # Cadastral reference: size of the cadastral polygon.
    _size_cadastral_polygon = 3

    # Cadastral reference: size of the cadastral parcel.
    _size_cadastral_parcel = 5

    # Cadastral URL to get the cadastral data of a parcel from its
    # cadastral reference.
    _url_cadastral_data = 'http://ovc.catastro.meh.es/ovcservweb/' + \
        'OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC?' + \
        'Provincia=&Municipio=&RC='

    # Cadastral URL to show the official form mapped to a cadastral
    # reference.
    _url_cadastral_form = 'https://www1.sedecatastro.gob.es/' + \
        'CYCBienInmueble/OVCListaBienes.aspx?del=&muni=&rc1=rc1val&rc2=rc2val'

    # Update cadastral area when entering cadastral reference?
    _automatic_update_cadastral_data = True

    parcel_type = fields.Selection(
        string='Parcel Type',
        selection=[
            ('01_R', 'Rustic'),
            ('02_U', 'Urban'),
        ],
        default='01_R',
        required=True,
        index=True,
    )

    official_code_urban = fields.Char(
        string='Urban official code',
        size=MAX_SIZE_OFFICIAL_CODE_URBAN,)

    cadastral_sector = fields.Char(
        string='Cadastral Sector',
        size=MAX_SIZE_CADASTRAL_FIELD,
        default='A',)

    cadastral_polygon = fields.Char(
        string='Cadastral Polygon',
        size=MAX_SIZE_CADASTRAL_FIELD, )

    cadastral_parcel = fields.Char(
        string='Cadastral Parcel',
        size=MAX_SIZE_CADASTRAL_FIELD, )

    official_code = fields.Char(
        store=True,
        compute='_compute_official_code',)

    cadastral_area = fields.Integer(
        string='Cadastral Area (m²)',
        default=0,)

    _sql_constraints = [
        ('official_code_unique',
         'UNIQUE (official_code)',
         'Repeated cadastral reference.'),
        ('cadastral_area_ok', 'CHECK (cadastral_area >= 0)',
         'Incorrect value for "Cadastral Area (m²)".'),
    ]

    @api.depends('parcel_type', 'municipality_id',
                 'municipality_id.cadastral_code', 'official_code_urban',
                 'cadastral_sector', 'cadastral_polygon', 'cadastral_parcel')
    def _compute_official_code(self):
        for record in self:
            official_code = None
            if record.parcel_type == '01_R':
                if (record.municipality_id and record.cadastral_sector and
                   record.cadastral_polygon and record.cadastral_parcel):
                    official_code = record.municipality_id.cadastral_code + \
                        record.cadastral_sector + \
                        record.cadastral_polygon.zfill(
                            self._size_cadastral_polygon) + \
                        record.cadastral_parcel.zfill(
                            self._size_cadastral_parcel)
            else:
                if record.official_code_urban:
                    official_code = record.official_code_urban.strip()
            record.official_code = official_code
            if official_code and record.cadastral_area == 0:
                record.cadastral_area = record._get_cadastral_area()

    @api.constrains('official_code')
    def _check_official_code(self):
        official_code_length = self._size_municipality_cadastral_code + \
            self._size_cadastral_sector + self._size_cadastral_polygon + \
            self._size_cadastral_parcel
        for record in self:
            if (record.official_code and
               len(record.official_code) != official_code_length):
                raise exceptions.ValidationError(_(
                    'The length of the cadastral reference is not correct.'))

    # Hook redefined.
    def _process_vals(self, vals):
        if 'cadastral_sector' in vals and vals['cadastral_sector']:
            vals['cadastral_sector'] = \
                vals['cadastral_sector'].strip().upper()
        if 'cadastral_polygon' in vals and vals['cadastral_polygon']:
            cadastral_polygon = 0
            try:
                cadastral_polygon = int(vals['cadastral_polygon'])
            except ValueError:
                cadastral_polygon = 0
            if cadastral_polygon <= 0:
                vals['cadastral_polygon'] = None
            else:
                vals['cadastral_polygon'] = vals['cadastral_polygon'].zfill(
                    self._size_cadastral_polygon)
        if 'cadastral_parcel' in vals and vals['cadastral_parcel']:
            cadastral_parcel = 0
            try:
                cadastral_parcel = int(vals['cadastral_parcel'])
            except ValueError:
                cadastral_parcel = 0
            if cadastral_parcel <= 0:
                vals['cadastral_parcel'] = None
            else:
                vals['cadastral_parcel'] = vals['cadastral_parcel'].zfill(
                    self._size_cadastral_parcel)
        if 'parcel_type' in vals:
            if vals['parcel_type'] == '01_R':
                vals['official_code_urban'] = None
            else:
                vals['cadastral_sector'] = None
                vals['cadastral_polygon'] = None
                vals['cadastral_parcel'] = None
        return None

    def _get_cadastral_area(self):
        self.ensure_one()
        cadastral_area = 0
        if self.official_code:
            # Add try for exceptions on Cadastre services
            try:
                resp_http_get = requests.get(
                    self._url_cadastral_data + self.official_code,
                    timeout=self.REQUEST_TIMEOUT)
                if resp_http_get.status_code == 200:
                    cadastral_data = ET.fromstring(resp_http_get.content)
                    prefix = ''
                    pos_closing = cadastral_data.tag.find('}')
                    if pos_closing != -1:
                        prefix = cadastral_data.tag[:pos_closing + 1]
                    number_of_items = int(cadastral_data[0][0].text)
                    if number_of_items == 1:
                        for item in cadastral_data.iter(prefix + 'ssp'):
                            area = int(item.text)
                            cadastral_area = cadastral_area + area
            except Exception:
                cadastral_area = 0
        return cadastral_area

    def action_show_cadastral_form(self):
        self.ensure_one()
        if self.official_code:
            length_cadastral_reference = self.SIZE_RC1 + self.SIZE_RC2
            if len(self.official_code) == length_cadastral_reference:
                rc1 = self.official_code[:self.SIZE_RC1]
                rc2 = self.official_code[self.SIZE_RC2:]
                cadastral_link = self._url_cadastral_form.replace(
                    'rc1val', rc1).replace('rc2val', rc2)
                return {
                    'type': 'ir.actions.act_url',
                    'url': cadastral_link,
                    'target': 'new',
                }
