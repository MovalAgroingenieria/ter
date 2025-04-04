# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from jinja2 import Template


class TerSigpac(models.Model):
    _name = 'ter.sigpac'
    _auto = False
    _description = 'SIGPAC Enclosure'
    _order = 'name'

    # URL to show the official form mapped to a SIGPAC enclosure.

    name = fields.Char(
        string='SIGPAC Code',)

    dn_oid = fields.Integer(
        string='SIGPAC Original Identifier',)

    provincia = fields.Integer(
        string='Province',)

    municipio = fields.Integer(
        string='Municipality',)

    agregado = fields.Integer(
        string='Aggregate',)

    zona = fields.Integer(
        string='Zone',)

    poligono = fields.Integer(
        string='Polygon',)

    parcela = fields.Integer(
        string='Parcel',)

    recinto = fields.Integer(
        string='Enclosure',)

    dn_surface = fields.Float(
        string='Area (m²)',
        digits=(32, 2),)

    dn_surface_ha = fields.Float(
        string='Area (ha)',
        digits=(32, 4),)

    dn_perim = fields.Float(
        string='Perimeter (m)',
        digits=(32, 2),)

    pend_media = fields.Integer(
        string='Medium Slope (per thousand)',)

    pend_media_porc = fields.Float(
        string='Medium Slope (%)',
        digits=(32, 2),)

    coef_admis = fields.Integer(
        string='Coefficient of admissibility in pastures (0-100)',)

    coef_rega = fields.Integer(
        string='Irrigation Coefficient (0-100)',)

    uso_sigpac = fields.Selection(
        string='Land Use',
        selection=[
            ('AG', 'AG - CORRIENTES Y SUPERFICIES DE AGUA'),
            ('CA', 'CA - VIALES'),
            ('CF', 'CF - ASOCIACIÓN CÍTRICOS-FRUTALES'),
            ('CI', 'CI - CITRICOS'),
            ('CS', 'CS - ASOCIACIÓN CÍTRICOS-FRUTALES DE CÁSCARA'),
            ('CV', 'CV - ASOCIACIÓN CÍTRICOS-VIÑEDO'),
            ('ED', 'ED - EDIFICACIONES'),
            ('EP', 'EP - ELEMENTO DEL PAISAJE'),
            ('FF', 'FF - ASOCIACIÓN FRUTALES-FRUTALES DE CÁSCARA'),
            ('FL', 'FL - FRUTOS SECOS Y OLIVAR'),
            ('FO', 'FO - FORESTAL'),
            ('FS', 'FS - FRUTOS SECOS'),
            ('FV', 'FV - FRUTOS SECOS Y VIÑEDO'),
            ('FY', 'FY - FRUTALES'),
            ('IM', 'IM - IMPRODUCTIVOS'),
            ('IV', 'IV - INVERNADEROS Y CULTIVOS BAJO PLASTICO'),
            ('MT', 'MT - MATORRAL'),
            ('OC', 'OC - ASOCIACIÓN OLIVAR-CÍTRICOS'),
            ('OF', 'OF - OLIVAR - FRUTAL'),
            ('OV', 'OV - OLIVAR'),
            ('PA', 'PA - PASTO CON ARBOLADO'),
            ('PR', 'PR - PASTO ARBUSTIVO'),
            ('PS', 'PS - PASTIZAL'),
            ('TA', 'TA - TIERRAS ARABLES'),
            ('TH', 'TH - HUERTA'),
            ('VF', 'VF - VIÑEDO - FRUTAL'),
            ('VI', 'VI - VIÑEDO'),
            ('VO', 'VO - VIÑEDO - OLIVAR'),
            ('ZC', 'ZC - ZONA CONCENTRADA NO INCLUIDA EN LA ORTOFOTO'),
            ('ZU', 'ZU - ZONA URBANA'),
            ('ZV', 'ZV - ZONA CENSURADA'),
        ],)

    incidencia = fields.Char(
        string='Incidence Codes',)

    region = fields.Char(
        string='Region',)

    sigpac_link = fields.Char(
        string='SIGPAC Link',
        default='',
        compute='_compute_sigpac_link',)

    sigpaclink_ids = fields.One2many(
        string='Intersections parcel-SIGPAC enclosure',
        comodel_name='ter.parcel.sigpaclink',
        inverse_name='sigpac_id')

    number_of_sigpaclinks = fields.Integer(
        string='Number of associated parcels',
        compute='_compute_number_of_sigpaclinks',)

    def _compute_sigpac_link(self):
        for record in self:
            sigpac_link = ''
            context = {
                'object': record,
            }
            sigpac_link = self.env['ir.config_parameter'].get_param(
                'l10n_es_territory_sigpac.sigpac_viewer_url')
            if sigpac_link:
                try:
                    template = Template(sigpac_link)
                    rendered_url = template.render(context)
                except Exception:
                    rendered_url = sigpac_link
                record.sigpac_link = rendered_url
            else:
                record.sigpac_link = ''

    def _compute_number_of_sigpaclinks(self):
        for record in self:
            number_of_sigpaclinks = 0
            if record.sigpaclink_ids:
                number_of_sigpaclinks = len(record.sigpaclink_ids)
            record.number_of_sigpaclinks = number_of_sigpaclinks

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        fields_to_remove = ['dn_oid', 'pend_media_porc', 'coef_rega']
        for field in fields_to_remove:
            if field in fields:
                fields.remove(field)
        return super().read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    def action_sigpac_viewer(self):
        self.ensure_one()
        if self.sigpac_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.sigpac_link,
                'target': 'new',
            }

    def action_get_parcels(self):
        self.ensure_one()
        if self.sigpaclink_ids:
            id_tree_view = self.env.ref(
                'l10n_es_territory_sigpac.'
                'ter_parcel_sigpaclink_only_parcels_view_tree').id
            search_view = self.env.ref(
                'l10n_es_territory_sigpac.'
                'ter_parcel_sigpaclink_only_parcels_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Parcels of the enclosure'),
                'res_model': 'ter.parcel.sigpaclink',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.sigpaclink_ids.ids)],
                }
            return act_window
