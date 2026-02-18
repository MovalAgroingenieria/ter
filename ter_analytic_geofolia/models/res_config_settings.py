# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    geofolia_default_parcel_id = fields.Many2one(
        comodel_name="ter.parcel",
        related="company_id.geofolia_default_parcel_id",
        readonly=False,
        string="Geofolia default parcel",
    )
    geofolia_default_date_range_id = fields.Many2one(
        comodel_name="date.range",
        related="company_id.geofolia_default_date_range_id",
        readonly=False,
        domain=[("is_unit_use_type", "=", True)],
        string="Geofolia default date range",
    )
    geofolia_default_fsm_location_id = fields.Many2one(
        comodel_name="fsm.location",
        related="company_id.geofolia_default_fsm_location_id",
        readonly=False,
        string="Geofolia default FSM location (activities)",
    )
    geofolia_default_harvested_product_id = fields.Many2one(
        comodel_name="product.product",
        related="company_id.geofolia_default_harvested_product_id",
        readonly=False,
        string="Geofolia default harvested product",
    )
    geofolia_default_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        related="company_id.geofolia_default_analytic_account_id",
        readonly=False,
        string="Geofolia default analytic account (timesheets)",
    )
