# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# pylint:disable=protected-access

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResMunicipality(models.Model):
    _inherit = "res.municipality"

    # Size of the cadastral code of province in the "cadastral_code" field.
    _SIZE_CADASTRALCODE_PROVINCE = 2

    # Size of the municipality number in the "cadastral_code" field.
    _SIZE_MUNICIPALITY_NUMBER = 3

    # Size of the "cadastral_code" field, in the model.
    MAX_SIZE_CADASTRAL_CODE = 20

    municipality_number = fields.Integer(
        required=True,
    )

    cadastral_code = fields.Char(
        size=_SIZE_CADASTRALCODE_PROVINCE + _SIZE_MUNICIPALITY_NUMBER,
        store=True,
        index=True,
        compute="_compute_cadastral_code",
        readonly=True,
    )

    @api.depends("province_id", "province_id.cadastral_code", "municipality_number")
    def _compute_cadastral_code(self):
        for record in self:
            record.cadastral_code = record._get_cadastral_code()

    def _get_cadastral_code(self):
        self.ensure_one()
        if (
            not self.province_id
            or not self.province_id.cadastral_code
            or not self.municipality_number
        ):
            return ""
        province_code = str(self.province_id.cadastral_code).zfill(
            self._SIZE_CADASTRALCODE_PROVINCE
        )
        municipality_number = str(self.municipality_number).zfill(
            self._SIZE_MUNICIPALITY_NUMBER
        )
        return f"{province_code}{municipality_number}"

    @api.constrains("municipality_number")
    def _check_municipality_number_positive(self):
        for record in self:
            if (
                record.municipality_number is not None
                and record.municipality_number <= 0
            ):
                raise ValidationError(
                    self.env._("A valid municipality number is required.")
                )

    @api.constrains("cadastral_code")
    def _check_cadastral_code_unique(self):
        for record in self:
            if not record.cadastral_code:
                continue
            existing = self.search_count(
                [
                    ("id", "!=", record.id),
                    ("cadastral_code", "=", record.cadastral_code),
                ]
            )
            if existing:
                raise ValidationError(self.env._("Repeated municipality code."))
