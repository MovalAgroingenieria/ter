# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class TerParcel(models.Model):
    _name = 'ter.parcel'
    _description = 'Parcel'
    _inherit = ['simple.model', 'mail.thread', ]

    # Static variables inherited from "simple.model"
    _set_num_code = False
    _sequence_for_codes = ''
    _size_name = 20
    _minlength = 0
    _maxlength = 20
    _allowed_blanks_in_code = False
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = True
    _size_description = 75

    # Size of the aerial images
    _aerial_image_size_big = 512
    _aerial_image_size_medium = 256
    _aerial_image_size_small = 128

    alphanum_code = fields.Char(
        string='Parcel Code',
        required=True,)

    partner_id = fields.Many2one(
        string='Parcel Manager',
        comodel_name='res.partner',)

    municipality_id = fields.Many2one(
        string='Municipality',
        comodel_name='res.municipality',
        required=True,
        index=True,
        ondelete='restrict',)

    place_id = fields.Many2one(
        string='Place',
        comodel_name='res.place',
        index=True,
        ondelete='restrict',)

    aerial_image = fields.Image(
        string='Aerial Image',
        max_width=_aerial_image_size_big,
        max_height=_aerial_image_size_big,)

    aerial_image_medium = fields.Image(
        string='Aerial Image (medium size)',
        max_width=_aerial_image_size_medium,
        max_height=_aerial_image_size_medium,
        store=True,
        related='aerial_image', )

    aerial_image_small = fields.Image(
        string='Aerial Image (small size)',
        max_width=_aerial_image_size_small,
        max_height=_aerial_image_size_small,
        store=True,
        related='aerial_image', )

    image_1920 = fields.Image(
        string='Aerial Image (zoom)',
        related='aerial_image',)

    def action_gis_viewer(self):
        self.ensure_one()
        # TODO
        print('action_gis_viewer')
