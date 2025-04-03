# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from odoo import models, fields, api, _


class TerParcel(models.Model):
    _inherit = 'ter.parcel'

    _aerial_img_sigpac_layers = [
        'pnoa',
        'sigpac_name',
        'parcel',
        'sigpac',
        'n_arrow',
    ]
    _aerial_img_sigpac_layers_styles = [
        'default',
        'default',
        'default',
        'default',
        'default',
    ]

    sigpaclink_ids = fields.One2many(
        string='SIGPAC links',
        comodel_name='ter.parcel.sigpaclink',
        inverse_name='parcel_id')

    number_of_sigpaclinks = fields.Integer(
        string='Intersections parcel-SIGPAC enclosure',
        compute='_compute_number_of_sigpaclinks',)

    parcel_title_sigpac = fields.Char(
        string='Parcel Title for SIGPAC table',
        compute='_compute_parcel_title_sigpac')

    aerial_img_sigpac = fields.Binary(
        string='Aerial image SIGPAC',
        attachment=True,
    )

    aerial_img_sigpac_shown = fields.Binary(
        string='Aerial image SIGPAC, non-persistent',
        compute='_compute_aerial_img_sigpac_shown',
    )

    aerial_img_sigpac_scale = fields.Integer(
        string='Scale',
        readonly=True)

    def _compute_number_of_sigpaclinks(self):
        for record in self:
            number_of_sigpaclinks = 0
            if record.sigpaclink_ids:
                number_of_sigpaclinks = len(record.sigpaclink_ids)
            record.number_of_sigpaclinks = number_of_sigpaclinks

    def _compute_parcel_title_sigpac(self):
        for record in self:
            parcel_title_sigpac = \
                _('PARCEL') + ': ' + record.name + ', ' + \
                _('SIGPAC ENCLOSURES')
            record.parcel_title_sigpac = parcel_title_sigpac

    def name_get(self):
        res = super().name_get()
        if self.env.context.get('sigpac'):
            res = [(record_id, f"{name} (Sigpac)") for record_id, name in res]
        return res

    def _compute_aerial_img_sigpac_shown(self):
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
        aerial_image_wmssigpac_url = config.get_param(
            'l10n_es_territory_sigpac.wms_sigpac_url', False)
        aerial_image_wmssigpac_layers = config.get_param(
            'l10n_es_territory_sigpac.wms_sigpac_layer', False)
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
            aerial_img_sigpac_shown = None
            if record.aerial_img_sigpac:
                aerial_img_sigpac_shown = record.aerial_img_sigpac
            else:
                if ogc_data_ok and record.mapped_to_polygon:
                    if not ogc_vec_layer:
                        aerial_img_sigpac_shown = record.get_aerial_image(
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
                        aerial_image_sigpac_raw = record.get_aerial_image(
                            wms=aerial_image_wmssigpac_url,
                            layers=aerial_image_wmssigpac_layers,
                            image_height=aerial_image_height,
                            format='png',
                            zoom=aerial_image_zoom,
                            get_raw=True,
                            filter=False,
                            styles="recinto",
                            force_square_shape=self._force_square_shape,)
                        print(aerial_image_sigpac_raw)
                        if aerial_image_base_raw and aerial_image_vec_raw and \
                           aerial_image_sigpac_raw:
                            aerial_image_raw = \
                                self.env['common.image'].merge_img(
                                    aerial_image_base_raw,
                                    aerial_image_sigpac_raw)
                            aerial_image_raw = \
                                self.env['common.image'].merge_img(
                                    aerial_image_raw,
                                    aerial_image_vec_raw
                                    )
                            if aerial_image_raw:
                                aerial_img_sigpac_shown = base64.b64encode(
                                    aerial_image_raw.getvalue())
                    if aerial_img_sigpac_shown:
                        record.aerial_img_sigpac = aerial_img_sigpac_shown
                        self.env['common.log'].register_in_log(
                            _('Aerial image OK. Parcel: %s', record.name),
                            source=self._name, message_type='INFO')
                    else:
                        self.env['common.log'].register_in_log(
                            _('Error getting aerial image '
                              '(is the WMS url correct?)'),
                            source=self._name, message_type='WARNING')
            record.aerial_img_sigpac_shown = aerial_img_sigpac_shown

    def _get_aerial_image_sigpac_layers(self, parcel):
        return self._aerial_img_sigpac_layers

    def _get_aerial_image_sigpac_layers_styles(self, parcel):
        return self._aerial_img_sigpac_layers_styles

    def action_get_enclosures(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'l10n_es_territory_sigpac.'
            'ter_parcel_sigpac_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('SIGPAC enclosures of the parcel'),
            'res_model': 'ter.parcel',
            'view_mode': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'res_id': self.id,
            'context': {'sigpac': True},
            }
        return act_window

    def action_regenerate_aerial_img_sigpac(self):
        parcels = self.env['ter.parcel'].search(
            [('mapped_to_polygon', '=', True)])
        for parcel in parcels:
            parcel._compute_aerial_img_sigpac_shown()


class TerParcelSigpaclink(models.Model):
    _name = 'ter.parcel.sigpaclink'
    _auto = False
    _description = 'SIGPAC link of a parcel'
    _order = 'name'

    name = fields.Char(
        string='Code of SIGPAC link',)

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='ter.parcel',)

    sigpac_id = fields.Many2one(
        string='SIGPAC Enclosure',
        comodel_name='ter.sigpac',)

    enclosure_number = fields.Integer(
        string='Enclosure Number',
        compute='_compute_enclosure_number',)

    municipality_id = fields.Many2one(
        string='Municipality',
        comodel_name='res.municipality',)

    parcel_area = fields.Float(
        string='GIS Area of parcel (m²)',
        digits=(32, 2),)

    sigpac_area = fields.Float(
        string='Area of SIGPAC enclosure (m²)',
        digits=(32, 2),)

    area_ha = fields.Float(
        string='Area (ha)',
        digits=(32, 4),)

    parcel_area_ha = fields.Float(
        string='GIS Area of parcel (ha)',
        digits=(32, 4),
        compute='_compute_parcel_area_ha',)

    intersection_percentage = fields.Float(
        string='% in parcel',
        digits=(32, 2),)

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

    gis_link_public = fields.Char(
        string='GIS Viewer Public',
        related='parcel_id.gis_link_public',)

    gis_link_minimal = fields.Char(
        string='GIS Viewer Minimal',
        related='parcel_id.gis_link_minimal',)

    gis_link_technical = fields.Char(
        string='GIS Viewer Technical',
        related='parcel_id.gis_link_technical',)

    sigpac_link = fields.Char(
        string='SIGPAC Link',
        related='sigpac_id.sigpac_link',)

    number_of_sigpaclinks = fields.Integer(
        string='Number of associated SIGPAC enclosures of the parcel',
        related='parcel_id.number_of_sigpaclinks',)

    irrigation_model_type = fields.Integer(
        string='Irrigation Type (parameter)',
        compute='_compute_irrigation_model_type',)

    def _compute_enclosure_number(self):
        for record in self:
            enclosure_number = 0
            if record.name and len(record.name) > 3:
                enclosure_number_as_str = record.name[-3:]
                if enclosure_number_as_str.isdigit():
                    enclosure_number = int(enclosure_number_as_str)
            record.enclosure_number = enclosure_number

    def _compute_parcel_area_ha(self):
        for record in self:
            record.parcel_area_ha = record.parcel_area / 10000

    def _compute_irrigation_model_type(self):
        irrigation_model_type = self.env['ir.default'].get(
            'ter.infrastructure.configuration', 'irrigation_model_type')
        for record in self:
            record.irrigation_model_type = irrigation_model_type

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        fields_to_remove = ['intersection_percentage', 'pend_media_porc',
                            'coef_rega']
        for field in fields_to_remove:
            if field in fields:
                fields.remove(field)
        return super().read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    def action_gis_viewer(self):
        self.ensure_one()
        if self.gis_link_public:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_link_public,
                'target': 'new',
            }

    def action_sigpac_viewer(self):
        self.ensure_one()
        if self.sigpac_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.sigpac_link,
                'target': 'new',
            }

    @api.model
    def action_refresh_sigpac_intersections(self):
        self.sudo().env.cr.execute(
            'REFRESH MATERIALIZED VIEW CONCURRENTLY ter_parcel_sigpaclink')
