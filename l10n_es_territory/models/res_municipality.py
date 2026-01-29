# Copyright 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# pylint:disable=protected-access

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResMunicipality(models.Model):
    _inherit = "res.municipality"

    _SIZE_CADASTRALCODE_PROVINCE = 2
    _SIZE_MUNICIPALITY_NUMBER = 3

    municipality_number = fields.Integer(required=True)

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
        if not (
            self.province_id
            and self.province_id.cadastral_code
            and self.municipality_number
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
            if record.municipality_number <= 0:
                raise ValidationError(
                    self.env._("A valid municipality number is required.")
                )

    @api.constrains("cadastral_code")
    def _check_cadastral_code_unique(self):
        for record in self:
            if not record.cadastral_code:
                continue
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    ("cadastral_code", "=", record.cadastral_code),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(
                    self.env._("Repeated municipality code.")
                )
