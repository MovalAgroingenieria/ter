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

    def _get_default_first_partnerlink_vals(self, partner_id, profile_id, percentage):
        vals = super()._get_default_first_partnerlink_vals(
            partner_id, profile_id, percentage
        )
        vals["percentage_overhead"] = 100.0
        return vals

    def _add_area_fields(self):
        area_fields = super()._add_area_fields()
        area_fields.append(("area_ownership", self.env._("Ownership area")))
        area_fields.append(("area_overhead", self.env._("Overhead area")))
        return area_fields

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


class TerParcelPartnerlink(models.Model):
    """
    Extend parcel partner links adding overhead and billing-related helpers.
    """

    _name = "ter.parcel.partnerlink"
    _inherit = ["ter.parcel.partnerlink", "account.billable.item"]
    _description = "Parcel Partner Link"

    _billing_partner_id_name = "partner_id"
    _billing_quantity_name = ""

    area_ownership = fields.Float(
        digits=(32, 4),
        compute="_compute_area_ownership",
        store=True,
        index=True,
    )
    percentage_overhead = fields.Float(
        digits=(32, 2),
        default=0.0,
        required=True,
    )
    area_overhead = fields.Float(
        digits=(32, 4),
        compute="_compute_area_overhead",
        store=True,
        index=True,
    )
    is_owner = fields.Boolean(
        compute="_compute_is_owner",
        store=True,
    )

    parcel_code = fields.Char(
        related="parcel_id.alphanum_code",
        store=True,
    )
    parcel_area_official = fields.Float(
        digits=(32, 4),
        related="parcel_id.area_official",
        store=True,
    )
    parcel_official_code = fields.Char(
        related="parcel_id.official_code",
        store=True,
    )
    property_name = fields.Char(
        related="parcel_id.property_id.alphanum_code",
        store=True,
    )
    partner_is_company = fields.Boolean(
        related="partner_id.is_company",
        store=True,
    )

    @api.constrains("percentage_overhead")
    def _check_percentage_overhead_range(self):
        for record in self:
            if record.percentage_overhead < 0 or record.percentage_overhead > 100:
                raise exceptions.ValidationError(
                    record.env._(
                        "Incorrect value of overhead percentage. "
                        "It must be between 0 and 100."
                    )
                )

    @api.depends("parcel_id.area_official", "profile_id", "percentage")
    def _compute_area_ownership(self):
        owner_profile = self.env.ref(
            "base_ter.ter_profile_01", raise_if_not_found=False
        )
        for record in self:
            area = 0.0
            if (
                record.parcel_id
                and record.parcel_id.area_official > 0
                and record.percentage
                and owner_profile
                and record.profile_id == owner_profile
            ):
                area = record.parcel_id.area_official * record.percentage / 100.0
            record.area_ownership = area

    @api.depends("parcel_id.area_official", "percentage_overhead")
    def _compute_area_overhead(self):
        for record in self:
            area = 0.0
            if (
                record.parcel_id
                and record.parcel_id.area_official > 0
                and record.percentage_overhead
            ):
                area = record.parcel_id.area_official * record.percentage_overhead / 100
            record.area_overhead = area

    @api.depends("profile_id")
    def _compute_is_owner(self):
        owner_profile = self.env.ref(
            "base_ter.ter_profile_01", raise_if_not_found=False
        )
        for record in self:
            record.is_owner = bool(owner_profile and record.profile_id == owner_profile)
