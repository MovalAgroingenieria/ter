# Copyright 2024-2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class TerUseUnit(models.Model):
    """Extend territorial use units with an analytic account (requires 'analytic')."""

    _inherit = "ter.use_unit"

    account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        ondelete="set null",
        help="Analytic account for cost/revenue tracking of this territorial unit.",
    )
