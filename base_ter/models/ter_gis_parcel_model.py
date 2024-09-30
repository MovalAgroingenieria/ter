# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, tools


class TerGisParcelModel(models.Model):
    _name = 'ter.gis.parcel.model'
    _description = 'GIS Parcel'
    _inherit = ['polygon.model']
    _auto = False

    # Size of the aerial images
    _aerial_image_size_small = 128

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'ter_gis_parcel_model')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW ter_gis_parcel_model AS (
            SELECT ROW_NUMBER() OVER() AS id, tgp.name, tp.id as parcel_id
            FROM ter_gis_parcel tgp INNER JOIN ter_parcel tp
            ON tgp.name = tp.name WHERE tp.active = TRUE)
            """)

    name = fields.Char(
        string='Parcel Code', )

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='ter.parcel',)

    aerial_image_small = fields.Image(
        string='Aerial Image (small size)',
        max_width=_aerial_image_size_small,
        max_height=_aerial_image_size_small,
        related='parcel_id.aerial_image_small',)
