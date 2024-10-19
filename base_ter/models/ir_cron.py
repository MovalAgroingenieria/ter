# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class IrCron(models.Model):
    _inherit = ['ir.cron']

    is_base_ter = fields.Boolean(
        string='Is this a base_ter action?',
        default=False,
    )
