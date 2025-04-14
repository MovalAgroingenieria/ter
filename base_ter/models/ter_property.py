# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64

from odoo import fields, models, api, exceptions, _


class TerProperty(models.Model):
    _name = 'ter.property'
    _description = 'Property'
    _inherit = ['simple.model', 'polygon.model', 'gis.viewer', 'mail.thread']
    _rec_name = 'alphanum_code'

    # Static variables inherited from "simple.model"
    _set_num_code = False
    _sequence_for_codes = ''
    _size_name = 100
    _minlength = 0
    _maxlength = 100
    _allowed_blanks_in_code = True
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = False
    _size_description = 175

    # Static variables inherited from "polygon.model"
    _gis_table = 'ter_gis_property'
    _geom_field = 'geom'
    _link_field = 'name'

    # Static variables inherited from "gis.viewer".
    _param_gis_selection = 'idfinca'

    # Size of the aerial images
    _aerial_image_size_big = 512
    _aerial_image_size_medium = 256
    _aerial_image_size_small = 128

    # Default value for the zoom of captured aerial images.
    _aerial_image_zoom = 1.2

    # Should aerial images be square?
    _force_square_shape = True

    # Area fields with unit of measure name, and "ha" name.
    _area_fields = [('area_official_parcels', _('Official Area'))]
    _ha_name = _('ha')

    alphanum_code = fields.Char(
        string='Property Name',
        required=True,)

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

    partner_id = fields.Many2one(
        string='Property Manager',
        comodel_name='res.partner',
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

    aerial_image_shown_256 = fields.Image(
        string='Aerial Image (medium size, non-persistent)',
        max_width=_aerial_image_size_medium,
        max_height=_aerial_image_size_medium,
        related='aerial_image_shown',)

    image_1920 = fields.Image(
        string='Aerial Image (zoom)',
        related='aerial_image_shown',)

    tag_id = fields.Many2many(
        string='Tags',
        comodel_name='ter.propertytag',
        relation='ter_property_propertytag_rel',
        column1='property_id', column2='propertytag_id')

    parcel_ids = fields.One2many(
        string='Parcels of the property',
        comodel_name='ter.parcel',
        inverse_name='property_id',)

    number_of_parcels = fields.Integer(
        string='Number of parcels',
        store=True,
        index=True,
        compute='_compute_number_of_parcels',)

    area_official_parcels = fields.Float(
        string='Parcel Area',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_area_official_parcels',)

    area_official_parcels_m2 = fields.Integer(
        string='Parcel Area (m²)',
        compute='_compute_area_official_parcels_m2',)

    diff_areas_threshold_exceeded = fields.Boolean(
        string='Threshold exceeded (difference between official and GIS areas)',
        compute='_compute_diff_areas_threshold_exceeded',)

    province_id = fields.Many2one(
        string='Province',
        comodel_name='res.province',
        store=True,
        index=True,
        compute='_compute_province_id',)

    region_id = fields.Many2one(
        string='Region',
        comodel_name='res.admregion',
        store=True,
        index=True,
        compute='_compute_region_id',)

    area_unit_name = fields.Char(
        string='Area unit name',
        compute='_compute_area_unit_name',)

    address_data = fields.Char(
        string='Address Data',
        compute='_compute_address_data',)

    def _compute_aerial_image_shown(self):
        config = self.env['ir.config_parameter'].sudo()
        aerial_image_wmsbase_url = config.get_param(
            'base_ter.aerial_image_wmsbase_url', False)
        aerial_image_wmsbase_layers = config.get_param(
            'base_ter.aerial_image_wmsbase_layers', False)
        aerial_image_wmsvec_url = config.get_param(
            'base_ter.aerial_image_wmsvec_url', False)
        aerial_image_wmsvec_property_name = config.get_param(
            'base_ter.aerial_image_wmsvec_property_name', False)
        aerial_image_wmsvec_property_filter = config.get_param(
            'base_ter.aerial_image_wmsvec_property_filter', False)
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
            if aerial_image_wmsvec_url and aerial_image_wmsvec_property_name:
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
                            zoom=aerial_image_zoom,
                            force_square_shape=self._force_square_shape,)
                    else:
                        aerial_image_base_raw = record.get_aerial_image(
                            wms=aerial_image_wmsbase_url,
                            layers=aerial_image_wmsbase_layers,
                            image_height=aerial_image_height,
                            format='png',
                            zoom=aerial_image_zoom,
                            get_raw=True,
                            filter=False,
                            force_square_shape=self._force_square_shape,)
                        aerial_image_vec_raw = record.get_aerial_image(
                            wms=aerial_image_wmsvec_url,
                            layers=aerial_image_wmsvec_property_name,
                            image_height=aerial_image_height,
                            format='png',
                            zoom=aerial_image_zoom,
                            get_raw=True,
                            filter=aerial_image_wmsvec_property_filter,
                            force_square_shape=self._force_square_shape,)
                        if aerial_image_base_raw and aerial_image_vec_raw:
                            aerial_image_raw = \
                                self.env['common.image'].merge_img(
                                    aerial_image_base_raw,
                                    aerial_image_vec_raw)
                            if aerial_image_raw:
                                aerial_image_shown = base64.b64encode(
                                    aerial_image_raw.getvalue())
                    if aerial_image_shown:
                        record.aerial_image = aerial_image_shown
                        self.env['common.log'].register_in_log(
                            _('Aerial image OK. Property: %s', record.name),
                            source=self._name, message_type='INFO')
                    else:
                        self.env['common.log'].register_in_log(
                            _('Error getting aerial image '
                              '(is the WMS url correct?)'),
                            source=self._name, message_type='WARNING')
            record.aerial_image_shown = aerial_image_shown

    @api.depends('parcel_ids')
    def _compute_number_of_parcels(self):
        for record in self:
            number_of_parcels = 0
            if record.parcel_ids:
                number_of_parcels = len(record.parcel_ids)
            record.number_of_parcels = number_of_parcels

    @api.depends('parcel_ids', 'parcel_ids.area_official')
    def _compute_area_official_parcels(self):
        for record in self:
            area_official_parcels = 0
            if record.parcel_ids:
                area_official_parcels = sum(parcel.area_official
                                            for parcel in record.parcel_ids)
            record.area_official_parcels = area_official_parcels

    def _compute_area_official_parcels_m2(self):
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
            record.area_official_parcels_m2 = round(
                record.area_official_parcels * factor)

    def _compute_diff_areas_threshold_exceeded(self):
        config = self.env['ir.config_parameter'].sudo()
        warning_diff_areas = int(config.get_param(
            'base_ter.warning_diff_areas', 0))
        for record in self:
            diff_areas_threshold_exceeded = False
            if (warning_diff_areas > 0 and record.area_official_parcels > 0 and
               record.mapped_to_polygon):
                area_gis = record.area_gis
                area_official = record.area_official_parcels_m2
                diff_areas = abs(area_official - area_gis)
                threshold = int(round(area_official * (warning_diff_areas / 100)))
                if diff_areas > threshold:
                    diff_areas_threshold_exceeded = True
            record.diff_areas_threshold_exceeded = diff_areas_threshold_exceeded

    @api.depends('municipality_id', 'municipality_id.province_id')
    def _compute_province_id(self):
        for record in self:
            province_id = None
            if record.municipality_id and record.municipality_id.province_id:
                province_id = record.municipality_id.province_id
            record.province_id = province_id

    @api.depends('province_id', 'province_id.region_id')
    def _compute_region_id(self):
        for record in self:
            region_id = None
            if record.province_id and record.province_id.region_id:
                region_id = record.province_id.region_id
            record.region_id = region_id

    def _compute_area_unit_name(self):
        area_unit_name = _('ha')
        config = self.env['ir.config_parameter'].sudo()
        area_unit_is_ha = config.get_param(
            'base_ter.area_unit_is_ha', False)
        if not area_unit_is_ha:
            area_unit_name = config.get_param(
                'base_ter.area_unit_name', '')
        for record in self:
            record.area_unit_name = area_unit_name

    def _compute_address_data(self):
        for record in self:
            address_data = record.municipality_id.name + \
                ' (' + record.municipality_id.province_id.name + ')'
            if (record.place_id and
               record.place_id.name.lower() !=
               record.municipality_id.name.lower()):
                address_data = record.place_id.name + ' - ' + address_data
            record.address_data = address_data

    @api.constrains('municipality_id', 'place_id')
    def _check_place_id(self):
        for record in self:
            if (record.municipality_id and record.place_id and
               record.place_id.municipality_id != record.municipality_id):
                raise exceptions.ValidationError(_('The place is not in the '
                                                   'municipality.'))

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

    def write(self, vals):
        old_partner_id = None
        if len(self) == 1:
            old_partner_id = self.partner_id
        resp = super(TerProperty, self).write(vals)
        if old_partner_id and 'partner_id' in vals and vals['partner_id']:
            new_partner_id = self.env['res.partner'].browse(vals['partner_id'])
            for parcel in (self.parcel_ids or []):
                for partnerlink in (parcel.partnerlink_ids or []):
                    if partnerlink.partner_id == old_partner_id:
                        partnerlink.partner_id = new_partner_id
                    break
                parcel.partner_id = new_partner_id
        return resp

    @api.model
    def action_refresh_properties_layer(self, from_backend=False):
        config = self.env['ir.config_parameter'].sudo()
        gis_viewer_epsg = config.get_param(
            'base_ter.gis_viewer_epsg', False)
        if not gis_viewer_epsg:
            gis_viewer_epsg = 25830
        message_type = 'INFO'
        message = _('ter_gis_property layer recreated.')
        module = ''
        model = ''
        method = ''
        try:
            self.env.cr.execute(
                'DROP TABLE IF EXISTS ter_gis_property')
            self.env.cr.execute(
                'CREATE TABLE ter_gis_property AS '
                'SELECT ROW_NUMBER() OVER (ORDER BY terpro.name) AS gid, terpro.name, '
                'ST_UNION(tergispar.geom)::postgis.geometry(MultiPolygon,%s) AS geom '
                'FROM ter_gis_parcel tergispar '
                'INNER JOIN ter_parcel terpar ON tergispar.name = terpar.name '
                'INNER JOIN ter_property terpro ON terpro.id = terpar.property_id '
                'WHERE terpar.active = TRUE '
                'GROUP BY terpro.name', tuple((gis_viewer_epsg,)))
            self.env.cr.execute(
                'ALTER TABLE ter_gis_property '
                'ADD PRIMARY KEY (gid)')
            self.env.cr.execute(
                'ALTER TABLE ter_gis_property '
                'ALTER COLUMN name SET NOT NULL')
            self.env.cr.execute(
                'ALTER TABLE ter_gis_property '
                'ADD CONSTRAINT ter_gis_property_name_key UNIQUE(name)')
            self.env.cr.execute(
                'ALTER TABLE ter_gis_property '
                'ADD CONSTRAINT ter_gis_property_name_check CHECK (name <> \'\')')
            self.env.cr.execute(
                'CREATE INDEX IF NOT EXISTS ter_gis_property_idx '
                'ON public.ter_gis_property USING gist (geom)')
        except Exception as error:
            message_type = 'ERROR'
            message = str(error)
            module = 'base_ter'
            model = 'ter.property'
            method = 'action_refresh_properties_layer'
        self.env['common.log'].register_in_log(
            message, source=self._name, module=module, model=model,
            method=method, message_type=message_type)
        if from_backend:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def reset_aerial_image(self):
        if len(self) == 1:
            self.aerial_image = None
            self._compute_aerial_image_shown()
        else:
            for record in self.with_progress(_('Getting the aerial images...')):
                record.aerial_image = None
                record._compute_aerial_image_shown()

    @api.model
    def action_reset_all_aerial_images(self, from_backend=False):
        properties = self.search([])
        properties.reset_aerial_image()
        if from_backend:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def action_gis_preview(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Property on the map') + ' : ' + self.alphanum_code,
            'res_model': 'wizard.show.gis.preview',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'src_model': 'ter.property',
            },
        }
        return act_window

    def action_show_parcels(self):
        self.ensure_one()
        current_property = self
        id_tree_view = self.sudo().env.ref(
            'base_ter.ter_parcel_view_tree').id
        id_form_view = self.sudo().env.ref(
            'base_ter.ter_parcel_view_form').id
        id_kanban_view = self.sudo().env.ref(
            'base_ter.ter_parcel_view_kanban').id
        search_view = self.sudo().env.ref(
            'base_ter.ter_parcel_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Parcels'),
            'res_model': 'ter.parcel',
            'view_mode': 'tree,form,kanban',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form'),
                      (id_kanban_view, 'kanban')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('property_id', '=', current_property.id)],
            'context': {'default_partner_id': current_property.partner_id.id,
                        'default_property_id': current_property.id, }
            }
        return act_window

    def _refresh_computed_fields(self):
        # Hook: Refresh of all computed fields.
        self._compute_number_of_parcels()
        self._compute_area_official_parcels()

    @api.model
    def _add_area_fields(self):
        # Hook: new area fields to add suffix (name of unit of measure).
        area_fields = self._area_fields
        # Example:
        # area_fields.append(('area_gis', _('GIS Area')))
        return area_fields
