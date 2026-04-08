# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class FSMOrder(models.Model):
    _inherit = "fsm.order"

    @api.depends("template_id")
    def _compute_order_activity_ids(self):
        result = super()._compute_order_activity_ids()
        for rec in self:
            if not rec.template_id:
                rec.order_activity_ids = self.env["fsm.activity"].search(
                    [("fsm_order_id", "=", rec.id)]
                )
        return result
