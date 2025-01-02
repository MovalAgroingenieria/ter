# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64

from odoo import fields, models, api, exceptions, _


class TerParcel(models.Model):
    _name = 'ter.parcel'
    _description = 'Parcel'
    _inherit = ['simple.model', 'polygon.model', 'gis.viewer', 'mail.thread']

    # Size of the "official_code" field in the model.
    MAX_SIZE_OFFICIAL_CODE = 50

    # Static variables inherited from "simple.model".
    _set_num_code = False
    _sequence_for_codes = ''
    _size_name = 20
    _minlength = 0
    _maxlength = 20
    _allowed_blanks_in_code = False
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = True
    _size_description = 75

    # Static variables inherited from "polygon.model".
    _gis_table = 'ter_gis_parcel'
    _geom_field = 'geom'
    _link_field = 'name'

    # Static variables inherited from "gis.viewer".
    _param_gis_selection = 'idparcela'

    # Size of the aerial images
    _aerial_image_size_big = 512
    _aerial_image_size_medium = 256
    _aerial_image_size_small = 128

    # Default value for the zoom of captured aerial images.
    _aerial_image_zoom = 1.2

    # Should aerial images be square?
    _force_square_shape = True

    # Area fields with unit of measure name, and "ha" name.
    _area_fields = [('area_official', _('Official Area'))]
    _ha_name = _('ha')

    alphanum_code = fields.Char(
        string='Parcel Code',
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

    official_code = fields.Char(
        string='Official Code',
        size=MAX_SIZE_OFFICIAL_CODE,
        index=True,)

    partner_id = fields.Many2one(
        string='Parcel Manager',
        comodel_name='res.partner',
        index=True,)

    property_id = fields.Many2one(
        string='Property',
        comodel_name='ter.property',
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
        comodel_name='ter.parceltag',
        relation='ter_parcel_parceltag_rel',
        column1='parcel_id', column2='parceltag_id')

    province_id = fields.Many2one(
        string='Province',
        comodel_name='res.province',
        store=True,
        index=True,
        compute='_compute_province_id',)

    region_id = fields.Many2one(
        string='Region',
        comodel_name='res.region',
        store=True,
        index=True,
        compute='_compute_region_id',)

    area_unit_name = fields.Char(
        string='Area unit name',
        compute='_compute_area_unit_name',)

    property_data = fields.Char(
        string='Property Data',
        compute='_compute_property_data',)

    address_data = fields.Char(
        string='Address Data',
        compute='_compute_address_data',)

    partnerlink_ids = fields.One2many(
        string='Contacts of parcel',
        comodel_name='ter.parcel.partnerlink',
        inverse_name='parcel_id',)

    partner_code = fields.Integer(
        string="Partner Code",
        compute='_compute_partner_code',)

    active = fields.Boolean(
        default=True,)

    _sql_constraints = [
        ('area_official_ok', 'CHECK (area_official >= 0)',
         'Incorrect value for "Official Area".'),
    ]

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
            if warning_diff_areas > 0 and record.mapped_to_polygon:
                area_gis = record.area_gis
                area_official = record.area_official_m2
                diff_areas = abs(area_official - area_gis)
                threshold = int(round(area_official * (warning_diff_areas / 100)))
                if diff_areas > threshold:
                    diff_areas_threshold_exceeded = True
            record.diff_areas_threshold_exceeded = diff_areas_threshold_exceeded

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
                            layers=aerial_image_wmsvec_parcel_name,
                            image_height=aerial_image_height,
                            format='png',
                            zoom=aerial_image_zoom,
                            get_raw=True,
                            filter=aerial_image_wmsvec_parcel_filter,
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
                            _('Aerial image OK. Parcel: %s', record.name),
                            source=self._name, message_type='INFO')
                    else:
                        self.env['common.log'].register_in_log(
                            _('Error getting aerial image '
                              '(is the WMS url correct?)'),
                            source=self._name, message_type='WARNING')
            record.aerial_image_shown = aerial_image_shown

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

    def _compute_property_data(self):
        for record in self:
            property_data = _('not assigned')
            if record.property_id:
                property_data = record.property_id.name
            record.property_data = property_data

    def _compute_address_data(self):
        for record in self:
            address_data = record.municipality_id.name + \
                ' (' + record.municipality_id.province_id.name + ')'
            if (record.place_id and
               record.place_id.name.lower() !=
               record.municipality_id.name.lower()):
                address_data = record.place_id.name + ' - ' + address_data
            record.address_data = address_data

    def _compute_partner_code(self):
        for record in self:
            partner_code = 0
            if record.partner_id and record.partner_id.partner_code > 0:
                partner_code = record.partner_id.partner_code
            record.partner_code = partner_code

    @api.constrains('municipality_id', 'place_id')
    def _check_place_id(self):
        for record in self:
            if (record.municipality_id and record.place_id and
               record.place_id.municipality_id != record.municipality_id):
                raise exceptions.ValidationError(_('The place is not in the '
                                                   'municipality.'))

    @api.constrains('partner_id', 'property_id')
    def _check_property_id(self):
        for record in self:
            if (record.partner_id and record.property_id and
               record.partner_id != record.property_id.partner_id):
                raise exceptions.ValidationError(
                    _('The parcel manager and the property manager must '
                      'be the same person.'))

    @api.constrains('partner_id')
    def _check_partner_id(self):
        for record in self:
            if record.partner_id:
                if not record.partner_id.is_holder:
                    raise exceptions.ValidationError(
                        _('The contact chosen as main is not a manager.'))
                if record.partnerlink_ids:
                    for partnerlink in record.partnerlink_ids:
                        if partnerlink.is_main:
                            if partnerlink.partner_id != record.partner_id:
                                raise exceptions.ValidationError(
                                    _('The parcel manager and the main '
                                      'contact must be the same person.'))
                            break
                else:
                    raise exceptions.ValidationError(
                        _('If a manager is assigned to the parcel, it is '
                          'mandatory to configure the contact list.'))

    @api.constrains('partner_id', 'partnerlink_ids')
    def _check_partnerlink_ids(self):
        for record in self:
            if record.partnerlink_ids:
                # Check #1: the partner_id is required.
                if not record.partner_id:
                    raise exceptions.ValidationError(
                        _('It is mandatory to enter the parcel manager.'))
                # Check #2: only one manager (mandatory).
                profile_ids = []
                number_of_managers = 0
                for partnerlink in record.partnerlink_ids:
                    if partnerlink.is_main == 1:
                        number_of_managers = number_of_managers + 1
                    if number_of_managers > 1:
                        break
                    if partnerlink.profile_id:
                        profile_ids.append(partnerlink.profile_id)
                if number_of_managers == 0 or number_of_managers > 1:
                    raise exceptions.ValidationError(
                        _('It is mandatory to enter the main contact of the '
                          'parcel (only one).'))
                # Check #3: sum of percentages equal to 100.
                if profile_ids:
                    profile_ids = list(set(profile_ids))
                    for profile in profile_ids:
                        if profile.requires_total:
                            partnerlinks_of_profile = \
                                self.env['ter.parcel.partnerlink'].search(
                                    [('parcel_id', '=', record.id),
                                     ('profile_id', '=', profile.id)])
                            if partnerlinks_of_profile:
                                total_percentage = \
                                    sum(partnerlink_of_profile.percentage
                                        for partnerlink_of_profile in
                                        partnerlinks_of_profile)
                                if total_percentage != 100:
                                    raise exceptions.ValidationError(
                                        _('Review the profile percentages: '
                                          'there is a percentage profile that '
                                          'does not add up to 100%.'))
            else:
                if record.partner_id:
                    raise exceptions.ValidationError(
                        _('The main contact exists, but the contact list of '
                          'the parcel is empty.'))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        partner_id = self.partner_id.id
        if partner_id:
            if (not self.partnerlink_ids) or len(self.partnerlink_ids) == 1:
                profile_id, percentage = self._get_default_profile()
                self.partnerlink_ids = [(5, ), (0, 0,
                                                {
                                                    'partner_id': partner_id,
                                                    'profile_id': profile_id,
                                                    'is_main': True,
                                                    'percentage': percentage,
                                                })]
            else:
                for partnerlink in self.partnerlink_ids:
                    if partnerlink.is_main:
                        partnerlink_id = partnerlink.id
                        self.partnerlink_ids = [(1, partnerlink_id,
                                                {
                                                    'partner_id': partner_id,
                                                })]
                        break

    def _get_default_profile(self):
        # Hook: get the default profile and % for a single partnerlink.
        profile_id = self.env.ref('base_ter.ter_profile_01').id
        percentage = 100
        return profile_id, percentage

    def name_get(self):
        show_archived_in_parcel_code = self.env.context.get(
            'show_archived_in_parcel_code', False)
        resp = []
        for record in self:
            name = record.name
            if show_archived_in_parcel_code:
                if record.active:
                    name = _('Available')
                else:
                    name = _('ARCHIVED')
            resp.append((record.id, name))
        return resp

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'partnerlink_ids' in vals:
                if len(vals['partnerlink_ids']) == 1:
                    partnerlink_data = vals['partnerlink_ids'][0][2]
                    if not partnerlink_data['is_main']:
                        partnerlink_data['is_main'] = True
                    if (not partnerlink_data['profile_id'] and
                       not partnerlink_data['percentage']):
                        profile_id, percentage = self._get_default_profile()
                        partnerlink_data['profile_id'] = profile_id
                        partnerlink_data['percentage'] = percentage
                for partnerlink in vals['partnerlink_ids']:
                    partnerlink_data = partnerlink[2]
                    if (partnerlink_data['is_main'] and
                       partnerlink_data['partner_id']):
                        vals['partner_id'] = partnerlink_data['partner_id']
                        break
        parcels = super(TerParcel, self).create(vals_list)
        return parcels

    def write(self, vals):
        if 'partnerlink_ids' in vals:
            for partnerlink in vals['partnerlink_ids']:
                operation = partnerlink[0]
                if operation == 0 or operation == 1:
                    partnerlink_data = partnerlink[2]
                    changed_partner = ('partner_id' in partnerlink_data and
                                       partnerlink_data['partner_id'])
                    changed_main = ('is_main' in partnerlink_data and
                                    partnerlink_data['is_main'])
                    if changed_partner or changed_main:
                        partner_id = 0
                        id_of_partnerlink = partnerlink[1]
                        if operation == 0:
                            if changed_partner and changed_main:
                                partner_id = partnerlink_data['partner_id']
                        elif operation == 1:
                            if changed_partner and changed_main:
                                partner_id = partnerlink_data['partner_id']
                            else:
                                partnerlink_original = \
                                    self.env['ter.parcel.partnerlink'].browse(
                                        id_of_partnerlink)
                                if changed_partner:
                                    if partnerlink_original.is_main:
                                        partner_id = partnerlink_data['partner_id']
                                else:
                                    partner_id = partnerlink_original.partner_id
                        if partner_id:
                            vals['partner_id'] = partner_id
                        break
        resp = super(TerParcel, self).write(vals)
        if 'active' in vals:
            partner_ids = []
            for record in self:
                if record.property_id:
                    record.property_id._refresh_computed_fields()
                for partnerlink in (record.partnerlink_ids or []):
                    if partnerlink.partner_id.is_holder:
                        partner_ids.append(partnerlink.partner_id.id)
            if partner_ids:
                partner_ids = list(set(partner_ids))
                partner_ids = self.env['res.partner'].browse(partner_ids)
                partner_ids._refresh_computed_fields()
        return resp

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
        if len(self) == 1:
            self.aerial_image = None
            self._compute_aerial_image_shown()
        else:
            for record in self.with_progress(_('Getting the aerial images...')):
                record.aerial_image = None
                record._compute_aerial_image_shown()

    @api.model
    def action_reset_all_aerial_images(self, from_backend=False):
        parcels = self.search([])
        parcels.reset_aerial_image()
        if from_backend:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def action_gis_preview(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Parcel on the map') + ' : ' + self.alphanum_code,
            'res_model': 'wizard.show.gis.preview',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'src_model': 'ter.parcel',
            },
        }
        return act_window

    def action_set_parcel_code(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Parcel') + ' : ' + self.alphanum_code,
            'res_model': 'wizard.set.parcel.code',
            'view_mode': 'form',
            'target': 'new',
        }
        return act_window

    @api.model
    def _add_area_fields(self):
        # Hook: new area fields to add suffix (name of unit of measure).
        area_fields = self._area_fields
        # Example:
        # area_fields.append(('area_gis', _('GIS Area')))
        return area_fields


class TerParcelPartnerlink(models.Model):
    _name = 'ter.parcel.partnerlink'
    _description = 'Partner of parcel'

    # Size of the "official_code" field in the model.
    MAX_SIZE_PARTNERLINK_CODE = 75

    # It is possible to choose any contact as a partner-link: no
    # (parcel managers only).
    _allow_all_contacts = False

    def _default_profile_id(self):
        return self.env.ref('base_ter.ter_profile_01').id

    def _set_domain_partner_id(self):
        resp = []
        if not self._allow_all_contacts:
            resp = [('is_holder', '=', True)]
        return resp

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='ter.parcel',
        index=True,
        ondelete='cascade',)

    partner_id = fields.Many2one(
        string='Contact',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict',
        domain=_set_domain_partner_id,)

    name = fields.Char(
        string='Identifier of partnerlink',
        size=MAX_SIZE_PARTNERLINK_CODE,
        store=True,
        index=True,
        compute='_compute_name',)

    profile_id = fields.Many2one(
        string='Profile',
        comodel_name='ter.profile',
        default=_default_profile_id,
        required=True,
        index=True,
        ondelete='restrict',)

    is_main = fields.Boolean(
        default=False,)

    percentage = fields.Integer(
        string='Percentage',
        default=0,
        required=True,)

    _sql_constraints = [
        ('owner_percentage',
         'CHECK (percentage >= 0 and percentage <= 100)',
         'Incorrect value of "Percentage".'),
        ]

    @api.depends('parcel_id', 'parcel_id.alphanum_code',
                 'partner_id', 'partner_id.partner_code')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.parcel_id:
                partner_code_asstr = '0'.zfill(
                    self.env['res.partner']._size_partner_code)
                if record.partner_id and record.partner_id.partner_code:
                    partner_code_asstr = record.partner_id.partner_code_asstr
                name = record.parcel_id.alphanum_code + '-' + \
                    partner_code_asstr
            record.name = name

    @api.constrains('partner_id')
    def _check_partner_id(self):
        for record in self:
            if record.parcel_id and record.partner_id:
                partners_mapped_to_partnerlink = \
                    self.env['ter.parcel.partnerlink'].search(
                        [('parcel_id', '=', record.parcel_id.id),
                         ('partner_id', '=', record.partner_id.id)])
                if (partners_mapped_to_partnerlink and
                   len(partners_mapped_to_partnerlink)) > 1:
                    raise exceptions.ValidationError(
                        _('Repeated line.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'profile_id' in vals:
                profile_id = vals['profile_id']
                profile = self.env['ter.profile'].browse(profile_id)
                if profile and (not profile.requires_total):
                    vals['percentage'] = 0
        partnerlinks = super(TerParcelPartnerlink, self).create(vals_list)
        return partnerlinks

    def write(self, vals):
        if len(self) == 1:
            partnerlink = self
            if 'profile_id' in vals or 'percentage' in vals:
                profile = None
                if 'profile_id' in vals:
                    profile = self.env['ter.profile'].browse(
                        vals['profile_id'])
                else:
                    profile = partnerlink.profile_id
                if profile and (not profile.requires_total):
                    vals['percentage'] = 0
        resp = super(TerParcelPartnerlink, self).write(vals)
        return resp
