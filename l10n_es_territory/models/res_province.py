# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResProvince(models.Model):
    _inherit = ['res.province']

    cadastral_code = fields.Integer(
        string='Cadastral Code',
        default=1,
        required=True,
        index=True,)

    _sql_constraints = [
        ('cadastral_code_unique',
         'UNIQUE (cadastral_code)',
         'Repeated province code.'),
        ('cadastral_code_positive',
         'CHECK (cadastral_code > 0)',
         'A valid cadastral code of province is required.'),
        ]
