# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, exceptions, _


class TerProfile(models.Model):
    _name = 'ter.profile'
    _description = 'Partner Profile'
    _inherit = ['simple.model', ]

    # Static variables inherited from "simple.model"
    _set_num_code = False
    _sequence_for_codes = ''
    _size_name = 25
    _minlength = 0
    _maxlength = 25
    _allowed_blanks_in_code = True
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = False
    _size_description = 75

    alphanum_code = fields.Char(
        string='Profile',
        required=True,
        translate=True,)

    requires_total = fields.Boolean(
        string='Required 100%',
        default=True,
        required=True,)

    is_standard = fields.Boolean(
        string='Standard Type (y/n)',
        default=False)

    active = fields.Boolean(
        default=True,)

    def unlink(self):
        for record in self:
            if record.is_standard:
                raise exceptions.UserError(_('It is not possible to remove a '
                                             '\'STANDARD\' partner profile.'))
        res = super(TerProfile, self).unlink()
        return res
