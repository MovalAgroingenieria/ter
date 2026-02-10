# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    geofolia_external_id = fields.Char(index=True)
    geofolia_source = fields.Selection(
        selection=[
            ("products", "Products"),
            ("harvested", "HarvestedProducts"),
            ("equipments", "Equipments"),
        ],
        index=True,
    )
    geofolia_job_id = fields.Many2one("geofolia.import.job", ondelete="set null")
    geofolia_source_line_ref = fields.Reference(
        selection=[
            ("geofolia.import.product.line", "Geofolia Product line"),
            ("geofolia.import.harvested.product.line", "Geofolia Harvested Product line"),
            ("geofolia.import.equipment.line", "Geofolia Equipment line"),
        ],
        string="Geofolia Source Line",
    )

    _sql_constraints = [
        (
            "geofolia_product_uniq",
            "unique(geofolia_source, geofolia_external_id)",
            "This Geofolia product has already been imported.",
        ),
    ]


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    geofolia_external_id = fields.Char(index=True)
    geofolia_job_id = fields.Many2one("geofolia.import.job", ondelete="set null")
    geofolia_source_line_ref = fields.Reference(
        selection=[("geofolia.import.employee.line", "Geofolia Employee line")],
        string="Geofolia Source Line",
    )

    _sql_constraints = [
        (
            "geofolia_employee_uniq",
            "unique(geofolia_external_id)",
            "This Geofolia employee has already been imported.",
        ),
    ]


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    geofolia_external_id = fields.Char(index=True)  # ActionId
    geofolia_job_id = fields.Many2one("geofolia.import.job", ondelete="set null")
    geofolia_activity_line_id = fields.Many2one(
        "geofolia.import.activity.line",
        ondelete="set null",
        index=True,
    )

    _sql_constraints = [
        (
            "geofolia_analytic_uniq",
            "unique(geofolia_external_id)",
            "This Geofolia activity has already been imported.",
        ),
    ]
