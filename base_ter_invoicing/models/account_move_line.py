# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    parcel_id = fields.Many2one(
        comodel_name="ter.parcel",
        string="Parcel",
        readonly=True,
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        partnerlinks = self.env["ter.parcel.partnerlink"]
        for vals in vals_list:
            if (
                vals.get("billable_item_model") != "ter.parcel.partnerlink"
                or not vals.get("billable_item_res_id")
                or vals.get("parcel_id")
            ):
                continue
            partnerlink = partnerlinks.browse(vals["billable_item_res_id"])
            if partnerlink.exists() and partnerlink.parcel_id:
                vals["parcel_id"] = partnerlink.parcel_id.id
        return super().create(vals_list)
