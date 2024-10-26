# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api, exceptions, _


class ResProvince(models.Model):
    _inherit = ['res.province']

    cadastral_code = fields.Integer(
        string='Cadastral Code',
        required=True,
        index=True,)

    _sql_constraints = [
        ('cadastral_code_positive',
         'CHECK (cadastral_code > 0)',
         'A valid cadastral code of province is required.'),
    ]

    @api.constrains('cadastral_code')
    def _check_cadastral_code(self):
        for record in self:
            if record.cadastral_code:
                other_province = self.env['res.province'].search(
                    [('id', '!=', record.id),
                     ('cadastral_code', '=', record.cadastral_code)])
                if other_province:
                    raise exceptions.ValidationError(_(
                        'Repeated province code.'))
