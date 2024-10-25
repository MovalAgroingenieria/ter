# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api, exceptions, _


class ResMunicipality(models.Model):
    _inherit = ['res.municipality']

    # Size of the cadastral code of province in the "cadastral_code" field.
    _size_cadastralcode_province = 2

    # Size of the municipality number in the "cadastral_code" field.
    _size_municipality_number = 3

    # Size of the "cadastral_code" field, in the model.
    MAX_SIZE_CADASTRAL_CODE = 20

    municipality_number = fields.Integer(
        string='Municipality Number',
        default=1,
        required=True,)

    cadastral_code = fields.Char(
        string='Cadastral Code',
        size=_size_cadastralcode_province + _size_municipality_number,
        store=True,
        index=True,
        compute='_compute_cadastral_code',)

    _sql_constraints = [
        ('municipality_number_positive',
         'CHECK (municipality_number > 0)',
         'A valid municipality number is required.'),
    ]

    @api.depends('province_id', 'province_id.cadastral_code',
                 'municipality_number')
    def _compute_cadastral_code(self):
        for record in self:
            cadastral_code = ''
            if (record.province_id and record.province_id.cadastral_code and
               record.municipality_number):
                cadastral_code = \
                    str(record.province_id.cadastral_code).zfill(
                        self._size_cadastralcode_province) + \
                    str(record.municipality_number).zfill(
                        self._size_municipality_number)
            record.cadastral_code = cadastral_code

    @api.constrains('cadastral_code')
    def _check_cadastral_code(self):
        for record in self:
            if record.cadastral_code:
                other_municipality = self.env['res.municipality'].search(
                    [('id', '!=', record.id),
                     ('cadastral_code', '=', record.cadastral_code)])
                if other_municipality:
                    raise exceptions.ValidationError(_(
                        'Repeated municipality code.'))
