# Copyright 2024-2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from psycopg2 import sql

from .. import hooks as base_ter_hooks


class TerUnit(models.Model):
    _inherit = "ter.use_unit"
    account_id = fields.Many2one("account.analytic.account", string="Analytic Account")
