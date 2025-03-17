# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import io
import base64
import logging
from xml.etree import ElementTree
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from odoo import models, fields, api, _, exceptions


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

    aerial_img_nonpersistent = fields.Binary(
        string='Aerial image, non-persistent',
        compute='_compute_aerial_img_nonpersistent')

    aerial_img_sigpac = fields.Binary(
        string='Aerial image SIGPAC',
        attachment=True,
    )

    aerial_img_sigpac_scale = fields.Integer(
        string='Scale',
        readonly=True)

    aerial_img_sigpac_nonpersistent = fields.Binary(
        string='Aerial image SIGPAC, non-persistent',
        compute='_compute_aerial_img_sigpac_nonpersistent',
    )

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

    def _compute_aerial_img_nonpersistent(self):
        for record in self:
            aerial_img_nonpersistent = None
            if record.aerial_img:
                aerial_img_nonpersistent = record.aerial_img
            else:
                try:
                    record.regenerate_aerial_img()
                    aerial_img_nonpersistent = record.aerial_img
                except Exception:
                    aerial_img_nonpersistent = None
            record.aerial_img_nonpersistent = aerial_img_nonpersistent

    def _compute_aerial_img_sigpac_nonpersistent(self):
        for record in self:
            aerial_img_sigpac_nonpersistent = None
            if record.aerial_img_sigpac:
                aerial_img_sigpac_nonpersistent = record.aerial_img_sigpac
            else:
                try:
                    record.regenerate_aerial_img_sigpac()
                    aerial_img_sigpac_nonpersistent = record.aerial_img_sigpac
                except Exception:
                    aerial_img_sigpac_nonpersistent = None
            record.aerial_img_sigpac_nonpersistent = \
                aerial_img_sigpac_nonpersistent

    def _get_aerial_image_sigpac_layers(self, parcel):
        return self._aerial_img_sigpac_layers

    def _get_aerial_image_sigpac_layers_styles(self, parcel):
        return self._aerial_img_sigpac_layers_styles

    def get_sld_sigpac_body(self):
        body = ''
        body = body + '<?xml version="1.0" encoding="UTF-8"?>' + \
            '<StyledLayerDescriptor version="1.0.0" ' + \
            'xmlns="http://www.opengis.net/sld" xmlns:ogc="' + \
            'http://www.opengis.net/ogc" xmlns:xlink="' + \
            'http://www.w3.org/1999/xlink" xmlns:xsi="' + \
            'http://www.w3.org/2001/XMLSchema-instance"' + \
            'xsi:schemaLocation="http://www.opengis.net/sld ' + \
            'http://schemas.opengis.net/sld/1.0.0/StyledLaye' + \
            'rDescriptor.xsd">' + \
            '<NamedLayer><Name>parcel</Name>' + \
            '<UserStyle><Title>xxx</Title><FeatureTypeStyle>' + \
            '<Rule><Filter><PropertyIsLike ' + \
            'wildCard="*" singleChar="." escape="!"><Property' + \
            'Name>name</PropertyName><Literal>' + self.name + \
            '</Literal></PropertyIsLike></Filter>' + \
            '<PolygonSymbolizer>' + \
            '<Stroke>' + \
            '<CssParameter name="stroke">#ffffff</CssParameter>' + \
            '<CssParameter name="stroke-width">3</CssParameter>' + \
            '<CssParameter name="stroke-linecap">round</CssParameter>' + \
            '</Stroke>' + \
            '<Fill>' + \
            '<CssParameter name="fill">#02f2ff</CssParameter>' + \
            '<CssParameter name="fill-opacity">0.6</CssParameter>' + \
            '</Fill>' + \
            '</PolygonSymbolizer>' + \
            '<TextSymbolizer>' + \
            '<Label>' + \
            '<ogc:PropertyName>' + \
            'name' + \
            '</ogc:PropertyName>' + \
            '</Label>' + \
            '<Font>' + \
            '<CssParameter name="font-family">Arial</CssParameter>' + \
            '<CssParameter name="font-size">14</CssParameter>' + \
            '<CssParameter name="font-style">normal</CssParameter>' + \
            '<CssParameter name="font-weight">bold</CssParameter>' + \
            '</Font>' + \
            '<Halo>' + \
            '<Radius>3</Radius>' + \
            '<Fill>' + \
            '<CssParameter name="fill">#00ff00</CssParameter>' + \
            '</Fill>' + \
            '</Halo>' + \
            '<Fill>' + \
            '<CssParameter name="fill">#000000</CssParameter>' + \
            '</Fill>' + \
            '</TextSymbolizer>' + \
            '</Rule></FeatureTypeStyle>' + \
            '</UserStyle></NamedLayer>' + \
            '<NamedLayer><Name>sigpac</Name>' + \
            '<UserStyle><Title>xxx2</Title><FeatureTypeStyle>' + \
            '<Rule>' + \
            '<PolygonSymbolizer>' + \
            '<Stroke>' + \
            '<CssParameter name="stroke">#c006c9</CssParameter>' + \
            '<CssParameter name="stroke-width">1</CssParameter>' + \
            '<CssParameter name="stroke-linecap">round</CssParameter>' + \
            '</Stroke>' + \
            '</PolygonSymbolizer>' + \
            '</Rule></FeatureTypeStyle>' + \
            '</UserStyle></NamedLayer>' + \
            '</StyledLayerDescriptor>'
        return body

    def regenerate_aerial_img_sigpac(self):
        url_gis_viewer_wms = self.env['ir.default'].get(
            'res.config.settings', 'url_gis_viewer_wms')
        url_gis_viewer_wfs = self.env['ir.default'].get(
            'res.config.settings', 'url_gis_viewer_wfs')
        if (not url_gis_viewer_wms or not url_gis_viewer_wfs):
            raise exceptions.UserError(_('The "URL GIS Viewer WMS" parameter '
                                         'or "URL GIS Viewer WFS" are not '
                                         'populated.'))
        else:
            mapserver_dpi = 90
            wms = WebMapService(
                url=url_gis_viewer_wms, version='1.1.1',
                timeout=self.OWS_SERVICES_TIMEOUT)
            wfs = WebFeatureService(
                url=url_gis_viewer_wfs, version='1.1.0',
                timeout=self.OWS_SERVICES_TIMEOUT)
            for record in self:
                if record.with_gis_parcel:
                    sld_sigpac_body = record.get_sld_sigpac_body()
                    try:
                        response = record._get_wfs_response(wfs, record)
                        parsed_response = ElementTree.fromstring(
                            response.getvalue())
                        ns = parsed_response[0].tag.split('}')[0] + '}'
                        parcel_member = parsed_response.find(ns +
                                                             'boundedBy')
                        parcel_envelop = parcel_member[0]
                        crs = parcel_envelop.attrib['srsName']
                        lowerCorner = [float(n) for n in (parcel_envelop.find(
                            ns + 'lowerCorner').text).split(' ')]
                        upperCorner = [float(n) for n in (parcel_envelop.find(
                            ns + 'upperCorner').text).split(' ')]
                        width = int(upperCorner[0] - lowerCorner[0])
                        height = int(upperCorner[1] - lowerCorner[1])
                        max_width = record._aerial_image_width
                        max_height = record._aerial_image_height
                        if (width > max_width or height > max_height):
                            increment = (int(self.getClosestMul(
                                max_width, max(height, width))))
                            incrementX = (increment - width)/2
                            incrementY = (increment - height)/2
                            lowerCorner[0] = int(lowerCorner[0] - incrementX)
                            upperCorner[0] = int(round(
                                upperCorner[0] + incrementX))
                            lowerCorner[1] = int(
                                round(lowerCorner[1] - incrementY))
                            upperCorner[1] = int(upperCorner[1] + incrementY)
                        elif (width < max_width or height < max_height):
                            increment = int(self.getClosestDiv(
                                max_width, max(height, width)))
                            incrementX = (increment - width)/2
                            incrementY = (increment - height)/2
                            lowerCorner[0] = int(lowerCorner[0] - incrementX)
                            upperCorner[0] = int(round(
                                upperCorner[0] + incrementX))
                            lowerCorner[1] = int(
                                round(lowerCorner[1] - incrementY))
                            upperCorner[1] = int(upperCorner[1] + incrementY)
                        width = max_width
                        height = max_height
                        bbox = ((int(lowerCorner[0])), (int(lowerCorner[1])),
                                (int(upperCorner[0])), (int(upperCorner[1])))
                        img = wms.getmap(
                            layers=record._get_aerial_image_sigpac_layers(
                                record),
                            styles=record.
                            _get_aerial_image_sigpac_layers_styles(
                                record),
                            srs=crs, bbox=bbox, size=(width, height),
                            format=self._aerial_img_format, transparent=True,
                            SLD_BODY=sld_sigpac_body)
                        image = io.BytesIO(img.read())
                        base64_img = base64.b64encode(image.getvalue())
                        # GET SCALE:
                        # With BBOX get meters in the real world
                        width_in_real_meters = bbox[2] - bbox[0]
                        # With pixels Width and dpi get the size of the image
                        width_in_image_meters = (width / mapserver_dpi) * \
                            0.0254
                        aerial_img_scale = width_in_real_meters /\
                            width_in_image_meters
                        record.write({
                            'aerial_img_sigpac': base64_img,
                            'aerial_img_sigpac_scale': aerial_img_scale,
                        })
                    except Exception:
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.exception('SIGPAC Aerial IMG')
                        pass

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
            }
        return act_window

    def action_regenerate_aerial_img_sigpac(self, limit=0):
        parcels = self.env['ter.parcel'].search(
            [('with_gis_parcel', '=', True)],
            order='aerial_img_last_import_date',
            limit=limit)
        for parcel in parcels:
            parcel.regenerate_aerial_img_sigpac()
            self.env.cr.commit()


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

    grp_cult = fields.Selection(
        string='Crop Group',
        selection=[
            ('CP', 'CP - Cultivos permanentes'),
            ('PT', 'PT - Pastos'),
            ('TCR', 'TCR - Tierras de cultivo de regadío'),
            ('TCS', 'TCS - Tierras de cultivo de secano'),
            ('', 'No asignado'),
        ],)

    gis_link_public = fields.Char(
        string='GIS Viewer',
        related='parcel_id.gis_link_public',)

    gis_link_minimal = fields.Char(
        string='GIS Viewer',
        related='parcel_id.gis_link_minimal',)

    gis_link_technical = fields.Char(
        string='GIS Viewer',
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
