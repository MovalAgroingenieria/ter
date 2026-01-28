# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    base_ter_aerial_image_wmsbase_url = fields.Char(
        related="company_id.base_ter_aerial_image_wmsbase_url",
        readonly=False,
    )
    base_ter_aerial_image_wmsbase_layers = fields.Char(
        related="company_id.base_ter_aerial_image_wmsbase_layers",
        readonly=False,
    )
