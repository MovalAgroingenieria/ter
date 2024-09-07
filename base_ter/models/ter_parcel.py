# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64

from odoo import fields, models, api, _


class TerParcel(models.Model):
    _name = 'ter.parcel'
    _description = 'Parcel'
    _inherit = ['simple.model', 'polygon.model', 'common.image',
                'common.log', 'mail.thread']

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

    # Static variables inherited from "polygon.model"
    _gis_table = 'ter_gis_parcel'
    _geom_field = 'geom'
    _link_field = 'name'

    # Size of the aerial images
    _aerial_image_size_big = 512
    _aerial_image_size_medium = 256
    _aerial_image_size_small = 128

    # Default value for the zoom of captured aerial images
    _aerial_image_zoom = 1.2

    # Area fields with unit of measure name, and "ha" name.
    _area_fields = [('area_official', _('Official Area'))]
    _ha_name = _('ha')

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

    # aerial_image_calculated = fields.Image(
    #     string='Aerial Image (512 x  512)',
    #     max_width=512,
    #     max_height=512,
    #     compute='_compute_aerial_image_calculated',)

    aerial_image = fields.Image(
        string='Aerial Image',
        max_width=_aerial_image_size_big,
        max_height=_aerial_image_size_big,)

    aerial_image_medium = fields.Image(
        string='Aerial Image (medium size)',
        max_width=_aerial_image_size_medium,
        max_height=_aerial_image_size_medium,
        store=True,
        related='aerial_image',)

    aerial_image_small = fields.Image(
        string='Aerial Image (small size)',
        max_width=_aerial_image_size_small,
        max_height=_aerial_image_size_small,
        store=True,
        related='aerial_image',)

    aerial_image_shown = fields.Image(
        string='Aerial Image (non-persistent)',
        max_width=_aerial_image_size_big,
        max_height=_aerial_image_size_big,
        compute='_compute_aerial_image_shown',)

    image_1920 = fields.Image(
        string='Aerial Image (zoom)',
        related='aerial_image_shown',)

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        default=0,
        required=True,
        index=True,)

    area_official_m2 = fields.Integer(
        string='Official Area (m²)',
        compute='_compute_area_official_m2',)

    diff_areas_threshold_exceeded = fields.Boolean(
        string='Threshold exceeded (difference between official and GIS areas)',
        compute='_compute_diff_areas_threshold_exceeded',)

    active = fields.Boolean(
        default=True,)

    # def _compute_aerial_image_calculated(self):
    #     wms = self.env['ir.config_parameter'].sudo().get_param(
    #         'base_ter.aerial_image_wmsvec_url')
    #     layers = self.env['ir.config_parameter'].sudo().get_param(
    #         'base_ter.aerial_image_wmsvec_parcel_name')
    #     for record in self:
    #         record.aerial_image_calculated = record.get_aerial_image(
    #             wms=wms, layers=layers, format='png', zoom=2, filter=True)

    def _compute_aerial_image_shown(self):
        config = self.env['ir.config_parameter'].sudo()
        aerial_image_wmsbase_url = config.get_param(
            'base_ter.aerial_image_wmsbase_url', False)
        aerial_image_wmsbase_layers = config.get_param(
            'base_ter.aerial_image_wmsbase_layers', False)
        aerial_image_wmsvec_url = config.get_param(
            'base_ter.aerial_image_wmsvec_url', False)
        aerial_image_wmsvec_parcel_name = config.get_param(
            'base_ter.aerial_image_wmsvec_parcel_name', False)
        aerial_image_wmsvec_parcel_filter = config.get_param(
            'base_ter.aerial_image_wmsvec_parcel_filter', False)
        aerial_image_height = int(config.get_param(
            'base_ter.aerial_image_height', 0))
        aerial_image_zoom = float(config.get_param(
            'base_ter.aerial_image_zoom', 0))
        ogc_data_ok = True
        ogc_vec_layer = False
        if (aerial_image_wmsbase_url and aerial_image_wmsbase_layers and
           aerial_image_height >= 0 and aerial_image_zoom >= 0):
            if aerial_image_height == 0:
                aerial_image_height = self._aerial_image_size_big
            if aerial_image_zoom == 0:
                aerial_image_zoom = self._aerial_image_zoom
            if aerial_image_wmsvec_url and aerial_image_wmsvec_parcel_name:
                ogc_vec_layer = True
        else:
            ogc_data_ok = False
        for record in self:
            aerial_image_shown = None
            if record.aerial_image:
                aerial_image_shown = record.aerial_image
            else:
                if ogc_data_ok and record.mapped_to_polygon:
                    if not ogc_vec_layer:
                        aerial_image_shown = record.get_aerial_image(
                            wms=aerial_image_wmsbase_url,
                            layers=aerial_image_wmsbase_layers,
                            image_height=aerial_image_height,
                            format='png',
                            zoom=aerial_image_zoom)
                    else:
                        aerial_image_base_raw = record.get_aerial_image(
                            wms=aerial_image_wmsbase_url,
                            layers=aerial_image_wmsbase_layers,
                            image_height=aerial_image_height,
                            format='png',
                            zoom=aerial_image_zoom,
                            get_raw=True,
                            filter=False)
                        aerial_image_vec_raw = record.get_aerial_image(
                            wms=aerial_image_wmsvec_url,
                            layers=aerial_image_wmsvec_parcel_name,
                            image_height=aerial_image_height,
                            format='png',
                            zoom=aerial_image_zoom,
                            get_raw=True,
                            filter=aerial_image_wmsvec_parcel_filter)
                        if aerial_image_base_raw and aerial_image_vec_raw:
                            aerial_image_raw = self.merge_img(
                                aerial_image_base_raw, aerial_image_vec_raw)
                            if aerial_image_raw:
                                aerial_image_shown = base64.b64encode(
                                    aerial_image_raw.getvalue())
                    if aerial_image_shown:
                        record.aerial_image = aerial_image_shown
                    else:
                        record.register_in_log(_('Error getting aerial image '
                                                 '(is the WMS url correct?)'),
                                               message_type='WARNING')
            record.aerial_image_shown = aerial_image_shown

    def _compute_area_official_m2(self):
        config = self.env['ir.config_parameter'].sudo()
        area_unit_is_ha = config.get_param(
            'base_ter.area_unit_is_ha', False)
        factor = 10000
        if not area_unit_is_ha:
            area_unit_value_in_ha = float(config.get_param(
                'base_ter.area_unit_value_in_ha', 0))
            if area_unit_value_in_ha > 0 and area_unit_value_in_ha != 1:
                factor = area_unit_value_in_ha * 10000
        for record in self:
            record.area_official_m2 = round(record.area_official * factor)

    def _compute_diff_areas_threshold_exceeded(self):
        config = self.env['ir.config_parameter'].sudo()
        warning_diff_areas = int(config.get_param(
            'base_ter.warning_diff_areas', 0))
        for record in self:
            diff_areas_threshold_exceeded = False
            if (warning_diff_areas > 0 and record.area_official > 0 and
               record.mapped_to_polygon):
                area_gis = record.area_gis
                area_official = record.area_official_m2
                diff_areas = abs(area_official - area_gis)
                threshold = int(round(area_official * (warning_diff_areas / 100)))
                if diff_areas > threshold:
                    diff_areas_threshold_exceeded = True
            record.diff_areas_threshold_exceeded = diff_areas_threshold_exceeded

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ['form', 'tree']:
            area_fields = self._add_area_fields()
            if area_fields:
                tmp_dict = {elem[0]: elem for elem in area_fields}
                area_fields = list(tmp_dict.values())
                measure_name = self._ha_name
                config = self.env['ir.config_parameter'].sudo()
                area_unit_is_ha = config.get_param(
                    'base_ter.area_unit_is_ha', False)
                area_unit_name = config.get_param(
                    'base_ter.area_unit_name', '')
                area_unit_value_in_ha = float(config.get_param(
                    'base_ter.area_unit_value_in_ha', 0))
                if (not area_unit_is_ha
                   and area_unit_name != measure_name
                   and area_unit_value_in_ha > 0
                   and area_unit_value_in_ha != 1):
                    measure_name = area_unit_name
                for area_field in area_fields:
                    field_name = area_field[0]
                    label_name = area_field[1]
                    for node in arch.xpath("//field[@name='%s']" % field_name):
                        self.with_context(lang=self.env.user.lang)
                        initial_label = _(label_name)
                        final_label = initial_label + ' (' + measure_name + ')'
                        node.set('string', final_label)
        return arch, view

    def reset_aerial_image(self):
        for record in self:
            record.aerial_image = None
            record._compute_aerial_image_shown()

    @api.model
    def action_reset_all_aerial_images(self):
        parcels = self.search([])
        parcels.reset_aerial_image()

    def action_gis_viewer(self):
        self.ensure_one()
        # TODO
        print('action_gis_viewer')

    def action_gis_preview(self):
        self.ensure_one()
        # TODO
        print('action_gis_preview')

    @api.model
    def _add_area_fields(self):
        # Hook: new area fields to add suffix (name of unit of measure)
        area_fields = self._area_fields
        # Example:
        # area_fields.append(('area_gis', _('GIS Area')))
        return area_fields
