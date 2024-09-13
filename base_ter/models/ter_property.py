# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class TerProperty(models.Model):
    _name = 'ter.property'
    _description = 'Property'
    _inherit = ['simple.model', 'polygon.model', 'mail.thread']
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

    # Static variables inherited from "polygon.model"
    _gis_table = 'ter_gis_property'
    _geom_field = 'geom'
    _link_field = 'name'

    alphanum_code = fields.Char(
        string='Property Name',
        required=True,)

    partner_id = fields.Many2one(
        string='Property Manager',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict',)

    parcel_ids = fields.One2many(
        string='Parcels of the property',
        comodel_name='ter.parcel',
        inverse_name='property_id',)

    area_official_parcels = fields.Float(
        string='Managed Area (parcels)',
        digits=(32, 4),
        default=0,
        index=True,)
