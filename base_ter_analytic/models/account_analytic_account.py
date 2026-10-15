# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    """Mark analytic accounts that can be linked to territorial use units."""

    _inherit = "account.analytic.account"

    ter_linkable = fields.Boolean(
        string="Linkable to Territory",
        default=True,
        help="Only analytic accounts with this flag can be selected on a "
        "territorial use unit.",
    )
    ter_use_unit_ids = fields.One2many(
        comodel_name="ter.use_unit",
        inverse_name="account_id",
        string="Territorial Units",
        groups="base_ter.group_ter_user",
    )
    ter_use_unit_count = fields.Integer(
        compute="_compute_ter_use_unit_count",
        groups="base_ter.group_ter_user",
    )

    @api.depends("ter_use_unit_ids")
    def _compute_ter_use_unit_count(self):
        counts = dict(
            self.env["ter.use_unit"]._read_group(  # pylint: disable=protected-access
                [("account_id", "in", self.ids)],
                groupby=["account_id"],
                aggregates=["__count"],
            )
        )
        for account in self:
            account.ter_use_unit_count = counts.get(account, 0)

    def action_view_ter_use_units(self):
        """Open the territorial use units linked to this analytic account."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Territorial Units"),
            "res_model": "ter.use_unit",
            "view_mode": "list,form",
            "domain": [("account_id", "=", self.id)],
            "context": {"default_account_id": self.id},
        }
