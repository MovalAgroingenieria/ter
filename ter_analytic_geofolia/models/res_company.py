# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    geofolia_default_parcel_id = fields.Many2one(
        comodel_name="ter.parcel",
        string="Geofolia default parcel",
        help="Default parcel for ter.use_unit when Fields have no geometry.",
    )
    geofolia_default_date_range_id = fields.Many2one(
        comodel_name="date.range",
        string="Geofolia default date range",
        domain=[("is_unit_use_type", "=", True)],
        help="Default date range for ter.use_unit when importing Geofolia Fields.",
    )
    geofolia_default_municipality_id = fields.Many2one(
        comodel_name="res.municipality",
        string="Geofolia default municipality",
        help="Fallback municipality used to create a parcel when a Geofolia "
        "Field's city does not match an existing municipality.",
    )
    geofolia_default_fsm_location_id = fields.Many2one(
        comodel_name="fsm.location",
        string="Geofolia default FSM location (activities)",
        help="Default FSM location for fsm.order created from Geofolia activities.",
    )
    geofolia_default_harvested_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Geofolia default harvested product",
        help="Product to assign to Harvested product lines when Geofolia sends no id.",
    )
    geofolia_default_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Geofolia default analytic account (timesheets)",
        help="Default analytic account for activity timesheets (Odoo 18).",
    )
