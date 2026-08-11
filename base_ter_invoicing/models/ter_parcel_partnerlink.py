# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, fields, models


class TerParcelPartnerlink(models.Model):
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
