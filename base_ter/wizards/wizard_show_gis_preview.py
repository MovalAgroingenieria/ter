# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=duplicate-code

from markupsafe import escape
from odoo import api, fields, models


class WizardShowGisPreview(models.TransientModel):
    _name = "wizard.show.gis.preview"
    _description = "GIS Preview"

    frame_view = fields.Html(string="Frame for the preview", sanitize=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        src_model = self.env.context.get("src_model")
        src_id = self.env.context.get("active_id")
        if not src_model or not src_id:
            res["frame_view"] = ""
            return res

        record = self.env[src_model].browse(src_id)
        url = record.gis_link_minimal or ""
        if not url:
            res["frame_view"] = ""
            return res

        safe_url = escape(url)
        res["frame_view"] = (
            '<iframe class="embed-responsive-item" '
            'src="%s" '
            'style="width: 100%%; height: 100%%; border: 0;" '
            'referrerpolicy="no-referrer-when-downgrade" '
            'loading="lazy" '
            'allowfullscreen="allowfullscreen">'
            "</iframe>"
        ) % safe_url
        return res
