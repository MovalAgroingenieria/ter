# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class WizardSetParcelCode(models.TransientModel):
    _name = "wizard.set.parcel.code"
    _inherit = ["wizard.active.record.mixin"]
    _description = "Dialog box to set a parcel code"

    parcel_code = fields.Char()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        parcel = self._get_active_record_or_empty("ter.parcel")
        if parcel.exists():
            res["parcel_code"] = parcel.alphanum_code
        return res

    def set_parcel_code(self):
        self.ensure_one()
        parcel = self._get_active_record_or_empty("ter.parcel")
        if not parcel.exists():
            return

        parcel_code = (self.parcel_code or "").strip().upper() or False
        parcel.write({"alphanum_code": parcel_code})
