# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
import datetime
import pytz
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from odoo.http import request
from odoo import api, fields, models


class GisViewer(models.AbstractModel):
    _name = 'gis.viewer'
    _description = 'Use of Gis Viewers'

    DEFAULT_GIS_VIEWER = 'https://gis.moval.es'

    # 16, 24 or 32 byts (consider changing this key for each custom module)
    _cipher_key = 'z%C*F-JaNdRgUkXp'

    # Param to select the items to be displayed in the viewer URL.
    _param_gis_selection = 'idparcela'

    gis_code = fields.Char(
        string='GIS Code',
        compute='_compute_gis_code',)

    gis_link_public = fields.Char(
        string='GIS Link (public)',
        compute='_compute_gis_link_public',)

    gis_link_technical = fields.Char(
        string='GIS Link (technical)',
        compute='_compute_gis_link_technical',)

    gis_link_minimal = fields.Char(
        string='GIS Link (minimal version)',
        compute='_compute_gis_link_minimal',)

    # This method may need to be redefined in other models
    def _compute_gis_code(self):
        for record in self:
            gis_code = ''
            if record.name:
                gis_code = record.name
            record.gis_code = gis_code

    def _compute_gis_link_public(self):
        for record in self:
            record.gis_link_public = record._get_gis_link(public=True)

    def _compute_gis_link_technical(self):
        for record in self:
            record.gis_link_technical = record._get_gis_link(public=False)

    def _compute_gis_link_minimal(self):
        for record in self:
            record.gis_link_minimal = record._get_gis_link(minimal=True)

    def action_gis_viewer(self):
        config = self.env['ir.config_parameter'].sudo()
        gis_viewer_url = config.get_param(
            'base_ter.gis_viewer_url', False)
        if not gis_viewer_url:
            gis_viewer_url = self.DEFAULT_GIS_VIEWER
        gis_viewer_url = gis_viewer_url + '?arg=' + \
            self._get_encrypted_credentials() + \
            '&' + self._param_gis_selection + '='
        for record in self:
            gis_viewer_url = gis_viewer_url + record.gis_code + ','
        gis_viewer_url = gis_viewer_url[:-1]
        xmin, ymin, xmax, ymax = self._get_bounding_box()
        if (xmin >= 0 and ymin >= 0 and xmax >= 0 and ymax >= 0 and
           xmin < xmax and ymin < ymax):
            bbox = f"{xmin},{ymin},{xmax},{ymax}"
            gis_viewer_url = gis_viewer_url + '&bbox=' + bbox
        return {
            'type': 'ir.actions.act_url',
            'url': gis_viewer_url,
            'target': 'new',
        }

    @api.model
    def action_gis_viewer_global(self):
        config = self.env['ir.config_parameter'].sudo()
        gis_viewer_url = config.get_param(
            'base_ter.gis_viewer_url', False)
        if not gis_viewer_url:
            gis_viewer_url = self.DEFAULT_GIS_VIEWER
        gis_viewer_url = gis_viewer_url + '?arg=' + \
            self._get_encrypted_credentials()
        return {
                'type': 'ir.actions.act_url',
                'url': gis_viewer_url,
                'target': 'new',
            }

    def _get_encrypted_credentials(self):
        config = self.env['ir.config_parameter'].sudo()
        gis_viewer_username = config.get_param(
            'base_ter.gis_viewer_username', False)
        gis_viewer_password = config.get_param(
            'base_ter.gis_viewer_password', False)
        resp = ''
        if gis_viewer_username and gis_viewer_password:
            plain_text = gis_viewer_username + '-' + gis_viewer_password + \
                '-' + str(request.session.sid)
            # Provisional (TEST)
            # print(plain_text)
            block_size = len(self._cipher_key)
            current_datetime = pytz.utc.localize(datetime.datetime.now())
            current_datetime = current_datetime.astimezone(
                pytz.timezone('Europe/Madrid'))
            current_datetime = str(current_datetime)[:16].replace(' ', 'T')
            minimum = int(current_datetime[14:])
            if minimum < 30:
                minimum = '00'
            else:
                minimum = '30'
            iv = (current_datetime[:14] + minimum).encode('utf-8')[:16]
            cipher_key = self._cipher_key.encode('utf-8')
            cipher = AES.new(cipher_key, AES.MODE_CBC, iv)
            plain_text = pad(plain_text.encode('utf-8'), block_size)
            encrypted_data = cipher.encrypt(plain_text)
            resp = base64.b64encode(encrypted_data).decode('utf-8')
            # Provisional (TEST)
            # print(resp)
            # cipher2 = AES.new(cipher_key, AES.MODE_CBC, iv)
            # encrypted_data2 = base64.urlsafe_b64decode(resp)
            # decrypted_data2 = cipher2.decrypt(encrypted_data2)
            # decrypted_data2 = unpad(decrypted_data2, block_size)
            # plain_text2 = decrypted_data2.decode('utf-8')
            # print(plain_text2)
        return resp

    def _get_bounding_box(self):
        xmin = 0
        ymin = 0
        xmax = 0
        ymax = 0
        first_iteration = True
        for record in self:
            if record.mapped_to_polygon:
                srid, bounding_box = record.extract_bounding_box(
                    record.geom_ewkt, force_square_shape=True)
                if first_iteration:
                    first_iteration = False
                    xmin = bounding_box[0]
                    ymin = bounding_box[1]
                    xmax = bounding_box[2]
                    ymax = bounding_box[3]
                else:
                    if bounding_box[0] < xmin:
                        xmin = bounding_box[0]
                    if bounding_box[1] < ymin:
                        ymin = bounding_box[1]
                    if bounding_box[2] > xmax:
                        xmax = bounding_box[2]
                    if bounding_box[3] > ymax:
                        ymax = bounding_box[3]
        return xmin, ymin, xmax, ymax

    def _get_gis_link(self, public=True, minimal=False):
        self.ensure_one()
        gis_link = ''
        if self.mapped_to_polygon:
            config = self.env['ir.config_parameter'].sudo()
            gis_link = config.get_param(
                'base_ter.gis_viewer_url', False)
            additional_args = config.get_param(
                'base_ter.gis_viewer_previs_additional_args', False)
            if not additional_args:
                additional_args = 'mode=min'
            if not gis_link:
                gis_link = self.DEFAULT_GIS_VIEWER
            gis_link = gis_link + '?' + \
                self.__class__._param_gis_selection + '=' + self.gis_code
            xmin, ymin, xmax, ymax = self._get_bounding_box()
            if (xmin >= 0 and ymin >= 0 and xmax >= 0 and ymax >= 0 and
               xmin < xmax and ymin < ymax):
                bbox = f"{xmin},{ymin},{xmax},{ymax}"
                gis_link = gis_link + '&bbox=' + bbox
            if minimal:
                gis_link = gis_link + '&' + additional_args
            elif not public:
                gis_link = gis_link + '&arg=' + self._get_encrypted_credentials()
        return gis_link
