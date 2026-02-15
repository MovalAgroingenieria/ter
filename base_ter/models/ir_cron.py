# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class IrCron(models.Model):
    _inherit = "ir.cron"

    is_base_ter = fields.Boolean(string="Is this a base_ter action?", default=False)
