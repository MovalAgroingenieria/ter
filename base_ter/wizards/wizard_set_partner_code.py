# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, fields, models


class WizardSetPartnerCode(models.TransientModel):
    _name = "wizard.set.partner.code"
    _description = "Dialog box to set a partner code"

    partner_code = fields.Integer()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        if not active_id:
            return res
        partner = self.env["res.partner"].browse(active_id)
        if partner:
            res["partner_code"] = partner.partner_code
        return res

    def set_partner_code(self):
        self.ensure_one()
        active_id = self.env.context.get("active_id")
        if not active_id:
            return

        partner = self.env["res.partner"].browse(active_id)
        if not partner:
            return

        # Reset requested (empty/0)
        if not self.partner_code:
            if partner.parcel_ids:
                raise exceptions.ValidationError(
                    self.env._(
                        "You cannot reset the code because the partner has parcels."
                    )
                )
            partner.partner_code = 0
            return

        partner.partner_code = self.partner_code
