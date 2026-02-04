# Copyright 2024-2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResPlace(models.Model):
    _inherit = "res.place"

    image_128 = fields.Image(
        string="Image",
        max_width=128,
        max_height=128,
    )
