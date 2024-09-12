# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import sys

from odoo import fields, models, api, exceptions, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'mail.thread']
    _order = 'partner_code, name'

    # Size of the "partner_code" field.
    _size_partner_code = 6

    # Threshold for valid partner codes.
    _partner_code_threshold = sys.maxsize

    def _default_partner_code(self):
        resp = 0
        context_ter = self.env.context.get('context_ter', False)
        if context_ter:
            self.env.cr.execute('SELECT max(partner_code) FROM res_partner')
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('max') is not None):
                resp = query_results[0].get('max') + 1
            else:
                resp = 1
        # Provisional
        print(resp)
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
        string='Managed Area (parcels)',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_area_official_parcels',)

    area_official_parcels_m2 = fields.Integer(
        string='Managed Area (m², parcels)',
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
        string='Managed Area (properties)',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_area_official_properties',)

    area_official_properties_m2 = fields.Integer(
        string='Managed Area (m², properties)',
        compute='_compute_area_official_properties_m2',)

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
            if record.partner_code:
                is_holder = True
            record.is_holder = is_holder

    @api.depends('parcel_ids')
    def _compute_number_of_parcels(self):
        for record in self:
            number_of_parcels = 0
            if record.parcel_ids:
                number_of_parcels = len(record.parcel_ids)
            record.number_of_parcels = number_of_parcels

    @api.depends('parcel_ids')
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

    @api.depends('property_ids')
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

    @api.constrains('partner_code')
    def _check_partner_code(self):
        for record in self:
            if record.partner_code > 0:
                self.env.cr.execute('SELECT count(*) FROM res_partner '
                                    'WHERE partner_code=%s',
                                    tuple((record.partner_code,)))
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                   query_results[0].get('count') is not None and
                   query_results[0].get('count') > 1):
                    raise exceptions.ValidationError(
                        _('Repeated partner code.'))
