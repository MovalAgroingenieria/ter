# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, fields, models


class PointPartnerLink(models.Model):
    _name = "point.point.partnerlink"
    _description = "Point Contact Link"

    point_id = fields.Many2one(
        "point.point", required=True, ondelete="cascade", index=True
    )
    partner_id = fields.Many2one(
        "res.partner", string="Contact", required=True, ondelete="restrict"
    )
    profile_id = fields.Many2one(
        "point.profile",
        required=True,
        # pylint: disable=protected-access
        default=lambda self: self._default_profile_id(),
    )
    is_main = fields.Boolean(default=False)
    percentage = fields.Float(digits=(32, 2), default=0)
    active = fields.Boolean(related="point_id.active", store=True)
    name = fields.Char(compute="_compute_name", store=True, index=True)

    _sql_constraints = [
        (
            "point_partnerlink_percentage_ok",
            "CHECK (percentage >= 0 AND percentage <= 100)",
            "Percentage must be between 0 and 100.",
        )
    ]

    def _default_profile_id(self):
        return self.env.ref("base_point.point_profile_01").id

    @api.depends("point_id.alphanum_code", "partner_id.name")
    def _compute_name(self):
        for record in self:
            code = record.point_id.alphanum_code or ""
            pname = record.partner_id.name or ""
            record.name = f"{code}-{pname}" if code or pname else ""

    @api.constrains("profile_id", "percentage", "point_id", "active")
    def _check_profile_total_percentage(self):
        for record in self:
            point = record.point_id
            if not point:
                continue
            profile = record.profile_id
            if not (profile and profile.requires_total):
                continue
            links = point.partnerlink_ids.filtered_domain(
                [("profile_id", "=", profile.id), ("active", "=", True)]
            )
            total = sum(links.mapped("percentage"))
            if abs(total - 100.0) > 1e-6:
                raise exceptions.ValidationError(
                    record.env._(
                        "Profile '%(profile)s' requires total percentage 100, "
                        "but current total is %(total)s.",
                        profile=profile.display_name,
                        total=total,
                    )
                )
