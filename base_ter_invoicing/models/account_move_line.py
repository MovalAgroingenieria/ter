# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = ["account.move.line"]

    parcel_id = fields.Many2one(
        string="Parcel",
        comodel_name="ter.parcel",
        readonly=True,
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "billable_item_model" in vals and "billable_item_res_id" in vals:
                billable_item_model = vals["billable_item_model"]
                billable_item_res_id = vals["billable_item_res_id"]
                if billable_item_model == "ter.parcel.partnerlink":
                    vals["parcel_id"] = (
                        self.env[billable_item_model]
                        .browse(billable_item_res_id)
                        .parcel_id.id
                    )
        move_lines = super(AccountMoveLine, self).create(vals_list)
        return move_lines
