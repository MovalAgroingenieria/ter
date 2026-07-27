# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    aerial_image_wmsvec_point_url = fields.Char(
        string="WMS of the vectorial image (points): URL", size=255
    )
    aerial_image_wmsvec_point_layer = fields.Char(
        string="WMS of the vectorial image: Name of the points layer", size=255
    )
    aerial_image_wmsvec_point_filter = fields.Boolean(
        string="WMS of the vectorial image: Filtered points (y/n)"
    )
