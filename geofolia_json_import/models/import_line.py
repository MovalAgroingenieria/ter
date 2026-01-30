# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo import _, models
from odoo.exceptions import UserError

class GeofoliaImportLine(models.Model):
    _name = "geofolia.import.line"
    _description = "Geofolia Import Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    import_type = fields.Selection(related="job_id.import_type", store=True, readonly=True)

    external_uuid = fields.Char()
    code = fields.Char()
    name = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()

    sync_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("skipped", "Skipped"),
            ("created", "Created"),
            ("updated", "Updated"),
            ("no_action", "No action"),
            ("error", "Error"),
        ],
        default="pending",
        index=True,
        required=True,
    )
    sync_message = fields.Text()

    # Fields (plots)
    harvest_year = fields.Integer()
    area = fields.Float()
    city = fields.Char()
    crop_name = fields.Char()
    geography_wkt = fields.Text()

    # Products (supplies)
    supply_id = fields.Char()
    category_enum = fields.Integer()
    product_type_enum = fields.Integer()
    unit_symbol = fields.Char()
    botanical_species = fields.Char()
    variety_name = fields.Char()

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_activity_line(line)
            line.job_id._recompute_apply_state()

class GeofoliaImportProductLine(models.Model):
    _name = "geofolia.import.product.line"
    _description = "Geofolia Import Product Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    farm_identification_code = fields.Char()
    external_id = fields.Char(index=True)  # SupplyId
    code = fields.Char()
    name = fields.Char()
    category_enum = fields.Integer()
    product_type_enum = fields.Integer()
    unit_symbol = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()

    sync_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("skipped", "Skipped"),
            ("created", "Created"),
            ("updated", "Updated"),
            ("no_action", "No action"),
            ("error", "Error"),
        ],
        default="pending",
        index=True,
        required=True,
    )
    sync_message = fields.Text()
    product_id = fields.Many2one("product.product", ondelete="set null")
    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            if line.job_id.import_type != "full":
                continue
            line.job_id._apply_product_line(line, source="products")
            line.job_id._recompute_apply_state()


class GeofoliaImportEmployeeLine(models.Model):
    _name = "geofolia.import.employee.line"
    _description = "Geofolia Import Employee Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    email = fields.Char()
    phone = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()

    sync_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("skipped", "Skipped"),
            ("created", "Created"),
            ("updated", "Updated"),
            ("no_action", "No action"),
            ("error", "Error"),
        ],
        default="pending",
        index=True,
        required=True,
    )
    sync_message = fields.Text()
    employee_id = fields.Many2one("hr.employee", ondelete="set null")

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_employee_line(line)
            line.job_id._recompute_apply_state()


class GeofoliaImportPartnerLine(models.Model):
    _name = "geofolia.import.partner.line"
    _description = "Geofolia Import Partner Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    vat = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()

    sync_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("skipped", "Skipped"),
            ("created", "Created"),
            ("updated", "Updated"),
            ("no_action", "No action"),
            ("error", "Error"),
        ],
        default="pending",
        index=True,
        required=True,
    )
    sync_message = fields.Text()


class GeofoliaImportHarvestedProductLine(models.Model):
    _name = "geofolia.import.harvested.product.line"
    _description = "Geofolia Import Harvested Product Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    unit_symbol = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()

    sync_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("skipped", "Skipped"),
            ("created", "Created"),
            ("updated", "Updated"),
            ("no_action", "No action"),
            ("error", "Error"),
        ],
        default="pending",
        index=True,
        required=True,
    )
    sync_message = fields.Text()
    product_id = fields.Many2one("product.product", ondelete="set null")


class GeofoliaImportEquipmentLine(models.Model):
    _name = "geofolia.import.equipment.line"
    _description = "Geofolia Import Equipment Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    category = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()

    sync_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("skipped", "Skipped"),
            ("created", "Created"),
            ("updated", "Updated"),
            ("no_action", "No action"),
            ("error", "Error"),
        ],
        default="pending",
        index=True,
        required=True,
    )
    sync_message = fields.Text()
    product_id = fields.Many2one("product.product", ondelete="set null")


class GeofoliaImportActivityLine(models.Model):
    _name = "geofolia.import.activity.line"
    _description = "Geofolia Import Activity Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")

    farm_identification_code = fields.Char()
    external_id = fields.Char(index=True)  # ActionId
    harvest_year = fields.Integer()

    operation_name = fields.Char()
    operation_category = fields.Char()

    status_name = fields.Char()
    status_code = fields.Char()

    starting_date = fields.Date()
    ending_date = fields.Date()
    start_time = fields.Char()
    finish_time = fields.Char()
    duration_minutes = fields.Integer()

    last_modification_dt = fields.Datetime()
    comment = fields.Text()

    raw_json = fields.Json()
    raw_json_text = fields.Text()

    sync_state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("skipped", "Skipped"),
            ("created", "Created"),
            ("updated", "Updated"),
            ("no_action", "No action"),
            ("error", "Error"),
        ],
        default="pending",
        index=True,
        required=True,
    )
    sync_message = fields.Text()

    employee_id = fields.Many2one("hr.employee", ondelete="set null")
    analytic_line_id = fields.Many2one("account.analytic.line", ondelete="set null")

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_activity_line(line)
            line.job_id._recompute_apply_state()