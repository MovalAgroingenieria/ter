# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class WizardSetPointCode(models.TransientModel):
    _name = "wizard.set.point.code"
    _inherit = ["wizard.active.record.mixin"]
    _description = "Dialog box to set a point code"

    point_code = fields.Char()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        point = self._get_active_record_or_empty("point.point")
        if point.exists():
            res["point_code"] = point.alphanum_code
        return res

    def set_point_code(self):
        self.ensure_one()
        point = self._get_active_record_or_empty("point.point")
        if not point.exists():
            return
        point_code = (self.point_code or "").strip().upper() or False
        point.write({"alphanum_code": point_code})
