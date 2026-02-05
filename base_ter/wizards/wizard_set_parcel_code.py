# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class WizardSetParcelCode(models.TransientModel):
    _name = "wizard.set.parcel.code"
    _description = "Dialog box to set a parcel code"

    parcel_code = fields.Char()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        if not active_id:
            return res

        parcel = self.env["ter.parcel"].browse(active_id)
        if parcel.exists():
            res["parcel_code"] = parcel.alphanum_code
        return res

    def set_parcel_code(self):
        self.ensure_one()
        active_id = self.env.context.get("active_id")
        if not active_id:
            return

        parcel = self.env["ter.parcel"].browse(active_id)
        if not parcel.exists():
            return

        parcel_code = (self.parcel_code or "").strip().upper() or False
        parcel.write({"alphanum_code": parcel_code})
