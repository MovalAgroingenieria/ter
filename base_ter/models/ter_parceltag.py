# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class TerParceltag(models.Model):
    _name = 'ter.parceltag'
    _description = 'Parcel Tag'
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
        string='Parcel Tag',
        required=True,
        translate=True,)

    color = fields.Integer(
        string='Color Index',)

    parcel_ids = fields.Many2many('ter.parcel',
                                  column1='parcel_id', column2='parceltag_id',
                                  string='Parcels', copy=False)
