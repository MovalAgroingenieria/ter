# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class TerParcelPartnerlink(models.Model):
    _name = "ter.parcel.partnerlink"
    _description = "Partner of parcel"

    MAX_SIZE_PARTNERLINK_CODE = 75
    _allow_all_contacts = False

    def _default_profile_id(self):
        profile = self.env.ref("base_ter.ter_profile_01", raise_if_not_found=False)
        if profile:
            return profile.id
        return self.env["ter.profile"]._ensure_ter_profile_01().id

    def _domain_partner_id(self):
        return [] if self._allow_all_contacts else [("is_holder", "=", True)]

    parcel_id = fields.Many2one(
        comodel_name="ter.parcel",
        index=True,
        ondelete="cascade",
    )
    partner_id = fields.Many2one(
        string="Contact",
        comodel_name="res.partner",
        required=True,
        index=True,
        ondelete="restrict",
        # pylint: disable=protected-access
        domain=lambda self: self._domain_partner_id(),
    )
    name = fields.Char(
        string="Identifier of partnerlink",
        size=MAX_SIZE_PARTNERLINK_CODE,
        store=True,
        index=True,
        compute="_compute_name",
    )
    profile_id = fields.Many2one(
        comodel_name="ter.profile",
        # pylint: disable=protected-access
        default=lambda self: self._default_profile_id(),
        required=True,
        index=True,
        ondelete="CASCADE",
    )
    is_main = fields.Boolean(default=False)
    percentage = fields.Float(digits=(32, 2), default=0, required=True)
    active = fields.Boolean(store=True, related="parcel_id.active")
    area_official = fields.Float(
        related="parcel_id.area_official",
        digits=(32, 4),
        store=True,
    )
    area_proportional = fields.Float(
        digits=(32, 4),
        compute="_compute_area_proportional",
    )
    area_unit_name = fields.Char(
        related="parcel_id.area_unit_name",
    )

    _sql_constraints = [
        (
            "owner_percentage",
            "CHECK (percentage >= 0 and percentage <= 100)",
            'Incorrect value of "Percentage".',
        ),
    ]

    @api.depends("parcel_id.alphanum_code", "partner_id.partner_code_asstr")
    def _compute_name(self):
        # pylint: disable=protected-access
        size = self.env["res.partner"]._size_partner_code
        for record in self:
            if not record.parcel_id:
                record.name = ""
                continue
            code_asstr = "0".zfill(size)
            if record.partner_id and record.partner_id.partner_code:
                code_asstr = record.partner_id.partner_code_asstr
            record.name = "%s-%s" % (record.parcel_id.alphanum_code, code_asstr)

    @api.depends("parcel_id.area_official", "percentage")
    def _compute_area_proportional(self):
        for record in self:
            record.area_proportional = (
                (record.parcel_id.area_official or 0.0) * record.percentage / 100.0
            )

    @api.model_create_multi
    def create(self, vals_list):
        profiles = {
            p.id: p
            for p in self.env["ter.profile"].browse(
                [v.get("profile_id") for v in vals_list if v.get("profile_id")]
            )
        }
        for vals in vals_list:
            profile = profiles.get(vals.get("profile_id"))
            if profile and not profile.requires_total:
                vals["percentage"] = 0
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "profile_id" in vals or "percentage" in vals:
            for record in self:
                profile = record.profile_id
                if profile and not profile.requires_total and record.percentage:
                    record.percentage = 0
        return res
