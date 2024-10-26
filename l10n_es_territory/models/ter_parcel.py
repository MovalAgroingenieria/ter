# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api, exceptions, _


class TerParcel(models.Model):
    _inherit = ['ter.parcel']

    # Size of the "official_code_urban" field in the model.
    MAX_SIZE_OFFICIAL_CODE_URBAN = 50

    # Size of a cadastral field (sector, polygon or parcel), in the model.
    MAX_SIZE_CADASTRAL_FIELD = 10

    # Cadastral reference: size of the cadastral code of the municipality.
    _size_municipality_cadastral_code = 5

    # Cadastral reference: size of the cadastral sector.
    _size_cadastral_sector = 1

    # Cadastral reference: size of the cadastral polygon.
    _size_cadastral_polygon = 3

    # Cadastral reference: size of the cadastral parcel.
    _size_cadastral_parcel = 5

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

    municipality_cadastral_code = fields.Char(
        string='Cadastral code of the municipality',
        related='municipality_id.cadastral_code',)

    cadastral_sector = fields.Char(
        string='Cadastral Sector',
        size=MAX_SIZE_CADASTRAL_FIELD,)

    cadastral_polygon = fields.Char(
        string='Cadastral Polygon',
        size=MAX_SIZE_CADASTRAL_FIELD, )

    cadastral_parcel = fields.Char(
        string='Cadastral Parcel',
        size=MAX_SIZE_CADASTRAL_FIELD, )

    official_code = fields.Char(
        store=True,
        compute='_compute_official_code',)

    _sql_constraints = [
        ('official_code_unique',
         'UNIQUE (official_code)',
         'Repeated cadastral reference.'),
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
                        record.cadastral_polygon + \
                        record.cadastral_parcel
            else:
                if record.official_code_urban:
                    official_code = record.official_code_urban.strip()
            record.official_code = official_code

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
