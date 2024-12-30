# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, _


class TerGisParcelModel(models.Model):
    _name = 'ter.gis.parcel.model'
    _description = 'GIS Parcel'
    _auto = False

    # Size of the aerial images
    _aerial_image_size_small = 128

    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, 'ter_gis_parcel_model')
    #     self.env.cr.execute("""
    #         CREATE OR REPLACE VIEW ter_gis_parcel_model AS (
    #         SELECT ROW_NUMBER() OVER() AS id, tgp.name,
    #         POSTGIS.ST_ASGEOJSON(tgp.geom) AS geom_geojson, tp.id as parcel_id,
    #         tp.partner_id as partner_id, tp.active as is_active
    #         FROM ter_gis_parcel tgp LEFT JOIN ter_parcel tp
    #         ON tgp.name = tp.name)
    #         """)

    name = fields.Char(
        string='Parcel Code', )

    geom_geojson = fields.Char(
        string='GeoJSON Geometry',)

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='ter.parcel',)

    partner_id = fields.Many2one(
        string='Parcel Partner',
        comodel_name='res.partner',)

    is_active = fields.Boolean(
        string='Active',)

    diff_areas_threshold_exceeded = fields.Boolean(
        string='Threshold exceeded (difference between official and GIS areas)',
        related='parcel_id.diff_areas_threshold_exceeded',)

    diff_areas_threshold_exceeded_str = fields.Char(
        string='Threshold exceeded (difference between official and GIS areas) -str-',
        compute='_compute_diff_areas_threshold_exceeded_str',)

    gis_data = fields.Text(
        string='GIS Data',
        compute='_compute_gis_data',)

    aerial_image_small = fields.Image(
        string='Aerial Image (small size)',
        max_width=_aerial_image_size_small,
        max_height=_aerial_image_size_small,
        related='parcel_id.aerial_image_small',)

    def _compute_diff_areas_threshold_exceeded_str(self):
        for record in self:
            diff_areas_threshold_exceeded_str = ''
            if record.parcel_id:
                diff_areas_threshold_exceeded_str = _('ok')
                if record.diff_areas_threshold_exceeded:
                    diff_areas_threshold_exceeded_str = _('CHECK')
            record.diff_areas_threshold_exceeded_str = \
                diff_areas_threshold_exceeded_str

    def _compute_gis_data(self):
        for record in self:
            gis_data = ''
            if record.parcel_id:
                area_official_m2 = record.parcel_id.area_official_m2
                area_gis = record.parcel_id.area_gis
                perimeter_gis = record.parcel_id.perimeter_gis
                bounding_box_str = record.parcel_id.bounding_box_str
                if bounding_box_str:
                    pos_bracket = bounding_box_str.find('(')
                    if pos_bracket != -1:
                        bounding_box_str = bounding_box_str[pos_bracket:]
                gis_data = \
                    '⸰ ' + _('Official Area (m²)') + ': ' + \
                    self.env['common.format'].transform_integer_to_locale(
                        area_official_m2) + '\n' + \
                    '⸰ ' + _('GIS Area (m²)') + ': ' + \
                    self.env['common.format'].transform_integer_to_locale(
                        area_gis) + '\n' + \
                    '⸰ ' + _('GIS Perimeter (m)') + ': ' + \
                    self.env['common.format'].transform_integer_to_locale(
                        perimeter_gis) + '\n' + \
                    '⸰ ' + bounding_box_str
            record.gis_data = gis_data
