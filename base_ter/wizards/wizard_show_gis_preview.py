# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class WizardShowGisPreview(models.TransientModel):
    _name = 'wizard.show.gis.preview'
    _description = 'GIS Preview'

    frame_view = fields.Html(
        string='Frame for the preview')

    @api.model
    def default_get(self, var_fields):
        frame_view = ''
        src_model = self.env.context['src_model']
        src_id = self.env.context['active_id']
        record = self.env[src_model].browse(src_id)
        if record:
            frame_view = \
                '<p style="text-align:center;margin-top:1px">' + \
                '<iframe id="iframe_view" scrolling="yes" ' + \
                'marginheight="0" marginwidth="0" src="' + \
                record.gis_link_minimal + '" ' + \
                'frameborder="1" height="200px" width="94%"' + \
                '</iframe></p>'
        return {
            'frame_view': frame_view,
        }
