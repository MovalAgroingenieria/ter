# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    is_unit_use_type = fields.Boolean(
        string="Usable for Unit Use",
        default=False,
        help="If enabled, date ranges of this type can be used "
        "to define periods for territorial unit uses.",
    )
