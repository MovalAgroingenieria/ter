# -*- coding: utf-8 -*-

from odoo import _, fields, models
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

    harvest_year = fields.Integer()
    area = fields.Float()
    city = fields.Char()
    crop_name = fields.Char()
    geography_wkt = fields.Text()

    supply_id = fields.Char()
    category_enum = fields.Integer()
    product_type_enum = fields.Integer()
    unit_symbol = fields.Char()
    botanical_species = fields.Char()
    variety_name = fields.Char()


class GeofoliaImportBaseLine(models.AbstractModel):
    _name = "geofolia.import.base.line"
    _description = "Geofolia Import Base Line"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")

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

    raw_json = fields.Json()
    raw_json_text = fields.Text()


class GeofoliaImportProductLine(models.Model):
    _name = "geofolia.import.product.line"
    _description = "Geofolia Import Product Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)  # SupplyId
    code = fields.Char()
    name = fields.Char()
    category_enum = fields.Integer()
    product_type_enum = fields.Integer()
    unit_symbol = fields.Char()

    product_id = fields.Many2one("product.product", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_product_job_ext_uniq",
            "unique(job_id, external_id)",
            "This product has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            if line.job_id.import_type != "full":
                continue
            line.job_id._apply_product_line(line)
            line.job_id._recompute_apply_state()


class GeofoliaImportEmployeeLine(models.Model):
    _name = "geofolia.import.employee.line"
    _description = "Geofolia Import Employee Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    email = fields.Char()
    phone = fields.Char()

    employee_id = fields.Many2one("hr.employee", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_employee_job_ext_uniq",
            "unique(job_id, external_id)",
            "This employee has already been imported in this job.",
        ),
    ]

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
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    vat = fields.Char()

    _sql_constraints = [
        (
            "geofolia_partner_job_ext_uniq",
            "unique(job_id, external_id)",
            "This partner has already been imported in this job.",
        ),
    ]


class GeofoliaImportHarvestedProductLine(models.Model):
    _name = "geofolia.import.harvested.product.line"
    _description = "Geofolia Import Harvested Product Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    unit_symbol = fields.Char()

    product_id = fields.Many2one("product.product", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_harvested_job_ext_uniq",
            "unique(job_id, external_id)",
            "This harvested product has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_product_like(line, label="harvested_products")
            line.job_id._recompute_apply_state()


class GeofoliaImportEquipmentLine(models.Model):
    _name = "geofolia.import.equipment.line"
    _description = "Geofolia Import Equipment Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    category = fields.Char()

    product_id = fields.Many2one("product.product", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_equipment_job_ext_uniq",
            "unique(job_id, external_id)",
            "This equipment has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_product_like(line, label="equipments")
            line.job_id._recompute_apply_state()


class GeofoliaImportActivityLine(models.Model):
    _name = "geofolia.import.activity.line"
    _description = "Geofolia Import Activity Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    farm_identification_code = fields.Char()
    external_id = fields.Char(index=True)  # ActionId
    harvest_year = fields.Integer()

    operation_name = fields.Char()
    operation_category = fields.Char()

    status_name = fields.Char()
    status_code = fields.Char()

    starting_date = fields.Date()
    ending_date = fields.Date()
    duration_minutes = fields.Integer()

    last_modification_dt = fields.Datetime()
    comment = fields.Text()

    employee_line_ids = fields.One2many(
        "geofolia.import.activity.employee.line",
        "activity_line_id",
        string="Employees",
    )

    _sql_constraints = [
        (
            "geofolia_activity_job_ext_uniq",
            "unique(job_id, external_id)",
            "This activity has already been imported in this job.",
        ),
    ]


class GeofoliaImportActivityEmployeeLine(models.Model):
    _name = "geofolia.import.activity.employee.line"
    _description = "Geofolia Import Activity Employee Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    activity_line_id = fields.Many2one(
        "geofolia.import.activity.line",
        required=True,
        ondelete="cascade",
    )

    employee_action_id = fields.Char(index=True)
    employee_recognition_id = fields.Char(index=True)
    employee_order = fields.Integer()

    employee_farm_identification_code = fields.Char()
    employee_first_name = fields.Char()
    employee_name = fields.Char()
    employee_id_external = fields.Char(index=True)
    employee_time = fields.Float()

    employee_id = fields.Many2one("hr.employee", ondelete="set null")
    analytic_line_id = fields.Many2one("account.analytic.line", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_act_emp_uniq",
            "unique(job_id, employee_action_id, employee_recognition_id, employee_order)",
            "This activity employee entry has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_activity_employee_line(line)
            line.job_id._recompute_apply_state()
