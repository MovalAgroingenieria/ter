# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    point_ids = fields.One2many("point.point", "partner_id", string="Points")
    number_of_points = fields.Integer(
        string="Number of points",
        compute="_compute_number_of_points",
        store=True,
        index=True,
    )

    @api.depends("point_ids")
    def _compute_number_of_points(self):
        for record in self:
            record.number_of_points = len(record.point_ids)

    def action_show_points(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Points"),
            "res_model": "point.point",
            "view_mode": "list,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }

    def action_gis_viewer_point(self):
        points = self.mapped("point_ids")
        if not points:
            return None
        # pylint: disable=protected-access
        return points.action_gis_viewer()
