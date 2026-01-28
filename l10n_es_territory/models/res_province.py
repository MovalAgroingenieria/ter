# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResProvince(models.Model):
    _inherit = "res.province"

    cadastral_code = fields.Integer(
        required=True,
        index=True,
    )

    @api.constrains("cadastral_code")
    def _check_cadastral_code_positive(self):
        for record in self:
            if record.cadastral_code is not None and record.cadastral_code <= 0:
                raise ValidationError(
                    self.env._("A valid cadastral code of province is required.")
                )

    @api.constrains("cadastral_code")
    def _check_cadastral_code_unique(self):
        for record in self:
            if not record.cadastral_code:
                continue
            if self.search_count(
                [
                    ("id", "!=", record.id),
                    ("cadastral_code", "=", record.cadastral_code),
                ]
            ):
                raise ValidationError(self.env._("Repeated province code."))
