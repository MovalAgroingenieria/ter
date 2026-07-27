# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    aerial_image_wmsvec_point_url = fields.Char(
        related="company_id.aerial_image_wmsvec_point_url", readonly=False
    )
    aerial_image_wmsvec_point_layer = fields.Char(
        related="company_id.aerial_image_wmsvec_point_layer", readonly=False
    )
    aerial_image_wmsvec_point_filter = fields.Boolean(
        related="company_id.aerial_image_wmsvec_point_filter", readonly=False
    )
