# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import json
from odoo.exceptions import ValidationError

class TerProject(models.Model):
    _name = "ter.project"
    _description = "Ter Project"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'account.analytic.account': 'account_id'}
    _order = "name, id"
    unit_ids = fields.One2many('ter.unit', 'project_id', string="Ter Unit(s)")
    account_id = fields.Many2one('account.analytic.account')
    date_start = fields.Date(string='Start Date')
    date = fields.Date(string='Expiration Date', index=True, tracking=True,
        help="Date on which this project ends. The timeframe defined on the project is taken into account when viewing its planning.")

    _sql_constraints = [
        ('project_date_greater', 'check(date >= date_start)', "The project's start date must be before its end date.")
    ]

    def account_analytic_line_action(self):
        self.ensure_one()
        line_ids = self.env['account.analytic.line'].search([('account_id', 'child_of', self.account_id.id)])

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.line",
            "domain": [('id', 'in', line_ids.ids)],
            "context": {"create": False},
            "name": _("Gross Account Analytic Line"),
            'view_mode': 'list,form',
        }

