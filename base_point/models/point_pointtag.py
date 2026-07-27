# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class PointPointTag(models.Model):
    _name = "point.pointtag"
    _description = "Point Tag"
    _inherit = "simple.model"

    size_name = 50
    maxlength = 50
    allowed_blanks_in_code = True

    alphanum_code = fields.Char(string="Tag", required=True, translate=True)
    color = fields.Integer(default=0)
    active = fields.Boolean(default=True)
