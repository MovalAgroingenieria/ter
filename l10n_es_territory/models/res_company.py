# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    base_ter_aerial_image_wmsbase_url = fields.Char()
    base_ter_aerial_image_wmsbase_layers = fields.Char()
