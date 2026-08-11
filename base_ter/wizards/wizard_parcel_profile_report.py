# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, fields, models


class WizardParcelProfileReport(models.TransientModel):
    _name = "wizard.parcel.profile.report"
    _description = "Parcels by Profile Report Wizard"

    profile_ids = fields.Many2many(
        comodel_name="ter.profile",
        string="Profiles",
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get("active_ids", [])
        if active_ids:
            partners = self.env["res.partner"].browse(active_ids)
            profiles = partners.mapped("partnerlink_ids.profile_id")
            if profiles:
                res["profile_ids"] = [(6, 0, profiles.ids)]
        return res

    def action_print(self):
        self.ensure_one()
        active_ids = self.env.context.get("active_ids", [])
        partners = self.env["res.partner"].browse(active_ids)
        if not partners:
            raise exceptions.UserError(
                self.env._("There are no selected partners to print.")
            )
        data = {"profile_ids": self.profile_ids.ids}
        return self.env.ref("base_ter.action_parcel_profile_report").report_action(
            partners, data=data
        )
