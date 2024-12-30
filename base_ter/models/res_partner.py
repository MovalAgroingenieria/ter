# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api, exceptions, _


class ResPartner(models.Model):
    _inherit = ['res.partner']
    _order = 'partner_code, name'

    # Size of the "partner_code" field.
    _size_partner_code = 6

    # Area fields with unit of measure name, and "ha" name.
    _area_fields = [('area_official_parcels', _('Parcel Area')),
                    ('area_official_properties', _('Property Area'))]
    _ha_name = _('ha')

    def _default_partner_code(self):
        resp = 0
        if self.env.context.get('context_ter', False):
            self.env.cr.execute('SELECT max(partner_code) FROM res_partner')
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('max') is not None):
                resp = query_results[0].get('max') + 1
            else:
                resp = 1
        return resp

    partner_code = fields.Integer(
        string="Partner Code",
        default=_default_partner_code,
        required=True,
        index=True,)

    partner_code_asstr = fields.Char(
        string='Partner Code (as string)',
        store=True,
        compute='_compute_partner_code_asstr',)

    is_holder = fields.Boolean(
        string='Parcel Holder',
        default=False,
        store=True,
        compute='_compute_is_holder',)

    parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='ter.parcel',
        inverse_name='partner_id',)

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

    property_ids = fields.One2many(
        string='Properties',
        comodel_name='ter.property',
        inverse_name='partner_id',)

    number_of_properties = fields.Integer(
        string='Number of properties',
        store=True,
        index=True,
        compute='_compute_number_of_properties',)

    area_official_properties = fields.Float(
        string='Property Area',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_area_official_properties',)

    area_official_properties_m2 = fields.Integer(
        string='Property Area (m²)',
        compute='_compute_area_official_properties_m2',)

    area_unit_name = fields.Char(
        string='Area unit name',
        compute='_compute_area_unit_name',)

    _sql_constraints = [
        ('partner_code_ok', 'CHECK (partner_code >= 0)',
         'Wrong partner code.'),
    ]

    @api.depends('partner_code')
    def _compute_partner_code_asstr(self):
        for record in self:
            partner_code_asstr = ''
            if record.partner_code:
                partner_code_asstr = str(record.partner_code).zfill(
                    self._size_partner_code)
            record.partner_code_asstr = partner_code_asstr

    @api.depends('partner_code')
    def _compute_is_holder(self):
        for record in self:
            is_holder = False
            if record.partner_code > 0:
                is_holder = True
            record.is_holder = is_holder

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

    @api.depends('property_ids')
    def _compute_number_of_properties(self):
        for record in self:
            number_of_properties = 0
            if record.property_ids:
                number_of_properties = len(record.property_ids)
            record.number_of_properties = number_of_properties

    @api.depends('property_ids', 'property_ids.area_official_parcels')
    def _compute_area_official_properties(self):
        for record in self:
            area_official_properties = 0
            if record.property_ids:
                area_official_properties = sum(property.area_official_parcels
                                               for property in record.property_ids)
            record.area_official_properties = area_official_properties

    def _compute_area_official_properties_m2(self):
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
            record.area_official_properties_m2 = round(
                record.area_official_properties * factor)

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

    @api.depends('is_company', 'name', 'parent_id.display_name', 'type',
                 'company_name', 'commercial_company_name', 'partner_code')
    def _compute_display_name(self):
        super(ResPartner, self)._compute_display_name()

    @api.constrains('partner_code')
    def _check_partner_code(self):
        for record in self:
            if record.partner_code > 0:
                partners_mapped_to_partner_code = \
                    self.env['res.partner'].search(
                        [('partner_code', '=', record.partner_code)])
                if (partners_mapped_to_partner_code and
                   len(partners_mapped_to_partner_code) > 1):
                    raise exceptions.ValidationError(
                        _('Repeated partner code.'))
            elif self.env.context.get('context_ter', False):
                raise exceptions.ValidationError(
                    _('The code must be a positive value.'))

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

    def name_get(self):
        resp = []
        for record in self:
            name = record.name
            if record.partner_code > 0:
                name = name + ' [' + str(record.partner_code) + ']'
            resp.append((record.id, name))
        return resp

    @api.model_create_multi
    def create(self, vals_list):
        # A "child contact" cannot have a code.
        for vals in vals_list:
            if 'parent_id' in vals and vals['parent_id']:
                vals['partner_code'] = 0
        partners = super(ResPartner, self).create(vals_list)
        return partners

    def action_gis_viewer_parcel(self):
        parcel_ids = []
        for record in self:
            parcel_ids.extend(record.parcel_ids.ids)
        if parcel_ids:
            return self.env['ter.parcel'].browse(parcel_ids).action_gis_viewer()

    def action_gis_viewer_property(self):
        property_ids = []
        for record in self:
            property_ids.extend(record.property_ids.ids)
        if property_ids:
            return self.env['ter.property'].browse(property_ids).action_gis_viewer()

    def action_set_partner_code(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'wizard.set.partner.code',
            'view_mode': 'form',
            'target': 'new',
        }
        return act_window

    def action_show_parcels(self):
        self.ensure_one()
        current_partner = self
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
            'domain': [('partner_id', '=', current_partner.id)],
            'context': {'default_partner_id': current_partner.id, }
            }
        return act_window

    def action_show_properties(self):
        self.ensure_one()
        current_partner = self
        id_tree_view = self.sudo().env.ref(
            'base_ter.ter_property_view_tree').id
        id_form_view = self.sudo().env.ref(
            'base_ter.ter_property_view_form').id
        id_kanban_view = self.sudo().env.ref(
            'base_ter.ter_property_view_kanban').id
        search_view = self.sudo().env.ref(
            'base_ter.ter_property_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Properties'),
            'res_model': 'ter.property',
            'view_mode': 'tree,form,kanban',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form'),
                      (id_kanban_view, 'kanban')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('partner_id', '=', current_partner.id)],
            'context': {'default_partner_id': current_partner.id, }
            }
        return act_window

    @api.model
    def _add_area_fields(self):
        # Hook: new area fields to add suffix (name of unit of measure)
        area_fields = self._area_fields
        # Example:
        # area_fields.append(('area_gis', _('GIS Area')))
        return area_fields

    def _refresh_computed_fields(self):
        # Hook: Refresh of all computed fields.
        self._compute_number_of_parcels()
        self._compute_area_official_parcels()
