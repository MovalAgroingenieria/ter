# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    area_unit_is_ha = fields.Boolean(
        string='Standard area unit: ha (y/n)',
        config_parameter='base_ter.area_unit_is_ha',)

    area_unit_name = fields.Char(
        string='Standard area unit: Name',
        size=255,
        config_parameter='base_ter.area_unit_name',)

    area_unit_value_in_ha = fields.Float(
        string='Standard area unit: Equivalence in ha',
        digits=(32, 4),
        config_parameter='base_ter.area_unit_value_in_ha',)

    warning_diff_areas = fields.Integer(
        string='Alert threshold due to the difference between the official '
               'area and the GIS area',
        config_parameter='base_ter.warning_diff_areas',)

    aerial_image_wmsbase_url = fields.Char(
        string='WMS of the base image: URL',
        size=255,
        config_parameter='base_ter.aerial_image_wmsbase_url',)

    aerial_image_wmsbase_layers = fields.Char(
        string='WMS of the base image: Layers',
        size=255,
        config_parameter='base_ter.aerial_image_wmsbase_layers',)

    aerial_image_wmsvec_url = fields.Char(
        string='WMS of the vectorial image: URL',
        size=255,
        config_parameter='base_ter.aerial_image_wmsvec_url',)

    aerial_image_wmsvec_parcel_name = fields.Char(
        string='WMS of the vectorial image: Name of the parcels layer',
        size=255,
        config_parameter='base_ter.aerial_image_wmsvec_parcel_name',)

    aerial_image_wmsvec_parcel_filter = fields.Boolean(
        string='WMS of the vectorial image: Filtered parcels (y/n)',
        config_parameter='base_ter.aerial_image_wmsvec_parcel_filter',)

    aerial_image_wmsvec_property_name = fields.Char(
        string='WMS of the vectorial image: Name of the properties layer',
        size=255,
        config_parameter='base_ter.aerial_image_wmsvec_property_name',)

    aerial_image_wmsvec_property_filter = fields.Boolean(
        string='WMS of the vectorial image: Filtered properties (y/n)',
        config_parameter='base_ter.aerial_image_wmsvec_property_filter',)

    aerial_image_height = fields.Integer(
        string='WMS Services: Height of the images',
        config_parameter='base_ter.aerial_image_height',)

    aerial_image_zoom = fields.Float(
        string='WMS Services: Zoom',
        digits=(32, 4),
        config_parameter='base_ter.aerial_image_zoom',)

    gis_viewer_url = fields.Char(
        string='GIS Viewer: URL',
        size=255,
        config_parameter='base_ter.gis_viewer_url',)

    gis_viewer_username = fields.Char(
        string='GIS Viewer: User name for the technical mode',
        size=255,
        config_parameter='base_ter.gis_viewer_username',)

    gis_viewer_password = fields.Char(
        string='GIS Viewer: Password for the technical mode',
        size=255,
        config_parameter='base_ter.gis_viewer_password',)

    gis_viewer_cipherkey = fields.Char(
        string='GIS Viewer: Cipher key for the technical mode',
        size=255,
        config_parameter='base_ter.gis_viewer_cipherkey',)

    gis_viewer_shpcreation_program = fields.Char(
        string='GIS Viewer: Program to create the SHP files',
        size=255,
        config_parameter='base_ter.gis_viewer_shpcreation_program',)

    gis_viewer_epsg = fields.Integer(
        string='GIS Viewer: Spatial Reference',
        config_parameter='base_ter.gis_viewer_epsg',)

    gis_viewer_previs_additional_args = fields.Char(
        string='GIS Preview: Additional URL arguments',
        size=255,
        config_parameter='base_ter.gis_viewer_previs_additional_args',)

    gis_viewer_previs_height = fields.Integer(
        string='GIS Preview: Frame height',
        config_parameter='base_ter.gis_viewer_previs_height',)

    gis_viewer_previs_width_percentage = fields.Integer(
        string='GIS Preview: Width percentage',
        config_parameter='base_ter.gis_viewer_previs_width_percentage',)

    _sql_constraints = [
        ('area_unit_value_in_ha_ok',
         'CHECK (area_unit_value_in_ha > 0)',
         'Incorrect value of "Standard area unit: Equivalence in ha".'),
        ('warning_diff_areas_ok',
         'CHECK (warning_diff_areas >= 0 AND warning_diff_areas <= 100)',
         'Incorrect value of "Alert threshold due to the difference '
         'between the official area and the GIS area".'),
        ('aerial_image_height_ok',
         'CHECK (aerial_image_height > 0)',
         'Incorrect value of "WMS Services: Height of the images".'),
        ('aerial_image_zoom_ok',
         'CHECK (aerial_image_zoom > 0)',
         'Incorrect value of "WMS Services: Zoom".'),
        ('gis_viewer_epsg_ok',
         'CHECK (gis_viewer_epsg > 0)',
         'Incorrect value of "GIS Viewer: Spatial Reference".'),
        ('gis_viewer_previs_height_ok',
         'CHECK (gis_viewer_previs_height > 0)',
         'Incorrect value of "GIS Preview: Frame height".'),
        ('gis_viewer_previs_width_percentage_ok',
         'CHECK (gis_viewer_previs_width_percentage > 0 AND '
         'gis_viewer_previs_width_percentage <= 100)',
         'Incorrect value of "GIS Preview: Width percentage".'),
    ]

    def set_values(self):
        prev_gis_viewer_epsg = int(self.env['ir.config_parameter'].sudo(
            ).get_param('base_ter.gis_viewer_epsg'))
        super(ResConfigSettings, self).set_values()
        # If necessary, update the geometry of the GIS tables
        new_gis_viewer_epsg = self['gis_viewer_epsg']
        if (prev_gis_viewer_epsg and
           (prev_gis_viewer_epsg != new_gis_viewer_epsg)):
            (update_geometry_ok, failed_layer) = self.update_geometry(
                new_gis_viewer_epsg)
            if not update_geometry_ok:
                error_message = _('Unable to update geometry of the '
                                  'layer...') + ' ' + failed_layer
                raise exceptions.UserError(error_message + '.')

    @api.model
    def update_geometry(self, new_epsg):
        resp = (True, '')
        layers = self._set_layers_to_update_geometry()
        for layer in (layers or []):
            update_geometry_ok = True
            self.env.cr.execute(
                'SELECT UpdateGeometrySRID(%s, \'geom\', %s)',
                tuple((layer, new_epsg)))
            if not update_geometry_ok:
                resp = (False, layer)
        return resp

    @api.model
    def _set_layers_to_update_geometry(self):
        # Hook: redefine in child classes to add more layers
        layers = ['ter_gis_parcel', 'ter_gis_property', ]
        return layers
