# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
import datetime
import logging

import pytz
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from odoo import api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)


class DateRange(models.Model):
    _inherit = 'date.range'
    is_unit_use_type = fields.Boolean(
        string='Usable for Unit Use',
        default=False,
        help='If enabled, date ranges of this type can be used '
             'to define periods for territorial unit uses.', )

    use_type_id = fields.Many2one('ter.use_type', domain=[('parent_id', '=', False)])