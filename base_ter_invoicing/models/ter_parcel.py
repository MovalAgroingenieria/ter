# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, fields, models
from odoo.tools.float_utils import float_compare


class TerParcel(models.Model):
    _inherit = "ter.parcel"

    total_invoiced = fields.Monetary(
        compute="_compute_total_invoiced",
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        compute="_compute_currency_id",
    )

    def _compute_total_invoiced(self):
        if not self:
            return

        aml = self.env["account.move.line"]
        domain = [
            ("parcel_id", "in", self.ids),
            ("parent_state", "not in", ("draft", "cancel")),
            ("quantity", ">", 0),
        ]
        grouped = aml.read_group(domain, ["price_subtotal:sum"], ["parcel_id"])
        totals = {
            g["parcel_id"][0]: g["price_subtotal"]
            for g in grouped
            if g.get("parcel_id")
        }
        for record in self:
            record.total_invoiced = totals.get(record.id, 0.0)

    def _compute_currency_id(self):
        currency = self.env.company.currency_id
        for record in self:
            record.currency_id = currency

    @api.constrains("partner_id", "partnerlink_ids")
    def _check_partnerlink_ids(self):
        result = super()._check_partnerlink_ids()
        for record in self:
            if not record.partnerlink_ids:
                continue

            total = sum(record.partnerlink_ids.mapped("percentage_overhead"))
            if float_compare(total, 100.0, precision_digits=2) != 0:
                raise exceptions.ValidationError(
                    record.env._(
                        "Review the overhead percentages: the total must be 100%."
                    )
                )
        return result

    def action_show_move_lines(self):
        self.ensure_one()
        list_view = self.env.ref("base_ter_invoicing.account_move_line_view_list")
        search_view = self.env.ref("base_ter_invoicing.account_move_line_view_search")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Invoice Lines"),
            "res_model": "account.move.line",
            "view_mode": "list",
            "views": [(list_view.id, "list")],
            "search_view_id": search_view.id,
            "target": "current",
            "domain": [("parcel_id", "=", self.id)],
        }

    def _get_default_first_partnerlink_vals(self, partner_id, profile_id, percentage):
        vals = super()._get_default_first_partnerlink_vals(
            partner_id, profile_id, percentage
        )
        vals["percentage_overhead"] = 100.0
        return vals

    def _add_area_fields(self):
        area_fields = super()._add_area_fields()
        area_fields.append(("area_ownership", self.env._("Area in property")))
        area_fields.append(("area_overhead", self.env._("Assigned area")))
        return area_fields
