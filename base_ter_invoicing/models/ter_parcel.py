# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, exceptions, fields, models
from odoo.tools.float_utils import float_compare


class TerParcel(models.Model):
    _inherit = "ter.parcel"

    total_invoiced = fields.Monetary(
        string="Total Invoiced",
        compute="_compute_total_invoiced",
        currency_field="currency_id",
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        compute="_compute_currency_id",
    )

    def _compute_total_invoiced(self):
        aml = self.env["account.move.line"]
        for record in self:
            record.total_invoiced = 0.0

        if not self:
            return

        domain = [
            ("parcel_id", "in", self.ids),
            ("parent_state", "not in", ("draft", "cancel")),
            ("quantity", ">", 0),
        ]
        grouped = aml.read_group(domain, ["price_subtotal:sum"], ["parcel_id"])
        totals = {g["parcel_id"][0]: g["price_subtotal_sum"] for g in grouped if g.get("parcel_id")}
        for record in self:
            record.total_invoiced = totals.get(record.id, 0.0)

    def _compute_currency_id(self):
        currency = self.env.company.currency_id
        for record in self:
            record.currency_id = currency

    @api.constrains("partner_id", "partnerlink_ids")
    def _check_partnerlink_ids(self):
        super()._check_partnerlink_ids()
        for record in self:
            if not record.partnerlink_ids:
                continue
            total = sum(record.partnerlink_ids.mapped("percentage_overhead"))
            if float_compare(total, 100.0, precision_digits=2) != 0:
                raise exceptions.ValidationError(
                    _("Review the overhead percentages: the total must be 100%.")
                )

    def _get_default_first_partnerlink_vals(self, partner_id, profile_id, percentage):
        vals = super()._get_default_first_partnerlink_vals(partner_id, profile_id, percentage)
        vals["percentage_overhead"] = 100.0
        return vals

    def _add_area_fields(self):
        area_fields = super()._add_area_fields()
        area_fields.append(("area_ownership", _("🡸 Area")))
        area_fields.append(("area_overhead", _("🡸 Area")))
        return area_fields

    def action_show_move_lines(self):
        self.ensure_one()
        tree_view = self.env.ref("base_ter_invoicing.account_move_line_view_tree")
        search_view = self.env.ref("base_ter_invoicing.account_move_line_view_search")
        return {
            "type": "ir.actions.act_window",
            "name": _("Invoice Lines"),
            "res_model": "account.move.line",
            "view_mode": "list",
            "views": [(tree_view.id, "list")],
            "search_view_id": search_view.id,
            "target": "current",
            "domain": [("parcel_id", "=", self.id)],
        }


class TerParcelPartnerlink(models.Model):
    _inherit = ["ter.parcel.partnerlink", "account.billable.item"]

    _billing_partner_id_name = "partner_id"
    _billing_quantity_name = ""

    area_ownership = fields.Float(
        string="Area (ownership)",
        digits=(32, 4),
        compute="_compute_area_ownership",
        store=True,
        index=True,
    )

    percentage_overhead = fields.Float(
        string="% Overhead",
        digits=(32, 2),
        default=0.0,
        required=True,
    )

    area_overhead = fields.Float(
        string="Area (overhead)",
        digits=(32, 4),
        compute="_compute_area_overhead",
        store=True,
        index=True,
    )

    is_owner = fields.Boolean(
        string="Owner (y/n)",
        compute="_compute_is_owner",
        store=True,
    )

    parcel_code = fields.Char(
        string="Parcel Code",
        related="parcel_id.alphanum_code",
        store=True,
    )

    parcel_area_official = fields.Float(
        string="Total Area",
        digits=(32, 4),
        related="parcel_id.area_official",
        store=True,
    )

    parcel_official_code = fields.Char(
        string="Official Code",
        related="parcel_id.official_code",
        store=True,
    )

    property_name = fields.Char(
        string="Property",
        related="parcel_id.property_id.alphanum_code",
        store=True,
    )

    partner_is_company = fields.Boolean(
        string="Company (y/n)",
        related="partner_id.is_company",
        store=True,
    )

    _sql_constraints = [
        (
            "overhead_percentage",
            "CHECK (percentage_overhead >= 0 AND percentage_overhead <= 100)",
            'Incorrect value of "Overhead Percentage".',
        ),
    ]

    @api.depends("parcel_id.area_official", "profile_id", "percentage")
    def _compute_area_ownership(self):
        owner_profile = self.env.ref("base_ter.ter_profile_01", raise_if_not_found=False)
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
            if record.parcel_id and record.parcel_id.area_official > 0 and record.percentage_overhead:
                area = record.parcel_id.area_official * record.percentage_overhead / 100.0
            record.area_overhead = area

    @api.depends("profile_id")
    def _compute_is_owner(self):
        owner_profile = self.env.ref("base_ter.ter_profile_01", raise_if_not_found=False)
        for record in self:
            record.is_owner = bool(owner_profile and record.profile_id == owner_profile)
