# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class TerPropertytag(models.Model):
    _name = 'ter.propertytag'
    _description = 'Property Tag'
    _inherit = ['simple.model']
    _rec_name = 'alphanum_code'

    # Static variables inherited from "simple.model"
    _set_num_code = False
    _sequence_for_codes = ''
    _size_name = 30
    _minlength = 0
    _maxlength = 30
    _allowed_blanks_in_code = True
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = False
    _size_description = 75

    alphanum_code = fields.Char(
        string='Property Tag',
        required=True,
        translate=True,)

    color = fields.Integer(
        string='Color Index',)

    property_ids = fields.Many2many('ter.property',
                                  column1='property_id', column2='propertytag_id',
                                  string='Properties', copy=False)
