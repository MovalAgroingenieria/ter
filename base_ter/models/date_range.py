# 2024-2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
import datetime
import logging

import pytz
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from odoo import _, api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)


class DateRange(models.Model):
    _inherit = "date.range"

    is_unit_use_type = fields.Boolean(
        string="Usable for Unit Use",
        default=False,
        help="If enabled, date ranges of this type can be used "
        "to define periods for territorial unit uses.",
    )
    use_type_id = fields.Many2one(
        "ter.use_type",
        string="Use Type",
        domain=[("parent_id", "=", False)],
    )
    color = fields.Integer(
        string="Color Index",
        related="use_type_id.color",
        readonly=True,
    )
    unit_ids = fields.One2many(
        "ter.unit",
        "date_range_id",
        string="Units",
    )
    unit_count = fields.Integer(
        string="Units",
        compute="_compute_unit_count",
    )
    parcel_count = fields.Integer(
        string="Parcels",
        compute="_compute_parcel_count",
    )

    @api.depends("unit_ids")
    def _compute_unit_count(self):
        for record in self:
            record.unit_count = len(record.unit_ids)

    @api.depends("unit_ids", "unit_ids.parcel_id", "unit_ids.parcel_ids")
    def _compute_parcel_count(self):
        for record in self:
            units = record.unit_ids
            parcels = units.mapped("parcel_id") | units.mapped("parcel_ids")
            record.parcel_count = len(parcels)

    def action_show_units(self):
        self.ensure_one()
        list_view = self.env.ref("base_ter.c")
        form_view = self.env.ref("base_ter.view_ter_unit_form")
        search_view = self.env.ref("base_ter.view_ter_unit_filter")
        return {
            "type": "ir.actions.act_window",
            "name": _("Territorial Units"),
            "res_model": "ter.unit",
            "view_mode": "list,form",
            "views": [(list_view.id, "list"), (form_view.id, "form")],
            "search_view_id": search_view.id,
            "domain": [("date_range_id", "=", self.id)],
        }

    def action_show_parcels(self):
        self.ensure_one()
        Unit = self.env["ter.unit"]
        units = Unit.search([("date_range_id", "=", self.id)])
        parcel_ids = (units.mapped("parcel_id") | units.mapped("parcel_ids")).ids
        tree_view = self.env.ref("base_ter.ter_parcel_view_tree")
        form_view = self.env.ref("base_ter.ter_parcel_view_form")
        search_view = self.env.ref("base_ter.ter_parcel_view_search")
        return {
            "type": "ir.actions.act_window",
            "name": _("Parcels"),
            "res_model": "ter.parcel",
            "view_mode": "list,form",
            "views": [(tree_view.id, "list"), (form_view.id, "form")],
            "search_view_id": search_view.id,
            "domain": [("id", "in", parcel_ids)] if parcel_ids else [("id", "=", 0)],
        }