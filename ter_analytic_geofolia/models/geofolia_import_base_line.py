# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

"""Base and all full-export line models in one file so load order is fixed."""

from odoo import _, fields, models
from odoo.exceptions import UserError


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


class GeofoliaImportActivityLine(models.Model):
    _name = "geofolia.import.activity.line"
    _description = "Geofolia Import Activity Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    farm_identification_code = fields.Char()
    external_id = fields.Char(index=True)
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
    fsm_order_id = fields.Many2one(
        comodel_name="fsm.order",
        string="FSM Order",
        ondelete="set null",
        help="With fieldservice_timesheet, employee times link to this order.",
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

    person_id = fields.Many2one("fsm.person", ondelete="set null")
    analytic_line_id = fields.Many2one("account.analytic.line", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_act_emp_uniq",
            "unique(job_id, employee_action_id, "
            "employee_recognition_id, employee_order)",
            "This activity employee entry has already been imported.",
        ),
    ]

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_activity_employee_line(line)
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

    person_id = fields.Many2one("fsm.person", ondelete="set null")

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


class GeofoliaImportEquipmentLine(models.Model):
    _name = "geofolia.import.equipment.line"
    _description = "Geofolia Import Equipment Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    farm_identification_code = fields.Char(
        default="",
        index=True,
        help="Farm identification from Geofolia; same EquipmentId can appear per farm.",
    )
    code = fields.Char()
    name = fields.Char()
    category = fields.Char()

    equipment_id = fields.Many2one(
        "fsm.equipment",
        string="FSM Equipment",
        ondelete="set null",
    )

    _sql_constraints = [
        (
            "geofolia_equipment_job_ext_farm_uniq",
            "unique(job_id, external_id, farm_identification_code)",
            "This equipment (and farm) has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_equipment_line(line)
            line.job_id._recompute_apply_state()


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


class GeofoliaImportPartnerLine(models.Model):
    _name = "geofolia.import.partner.line"
    _description = "Geofolia Import Partner Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    code = fields.Char()
    name = fields.Char()
    vat = fields.Char()

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        ondelete="set null",
    )

    _sql_constraints = [
        (
            "geofolia_partner_job_ext_uniq",
            "unique(job_id, external_id)",
            "This partner has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        jobs = self.mapped("job_id")
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            line.job_id._apply_partner_line(line)
        for job in jobs:
            job._recompute_apply_state()


class GeofoliaImportProductLine(models.Model):
    _name = "geofolia.import.product.line"
    _description = "Geofolia Import Product Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    farm_identification_code = fields.Char(
        default="",
        index=True,
        help="Farm identification from Geofolia; same SupplyId can appear per farm.",
    )
    code = fields.Char()
    name = fields.Char()
    category_enum = fields.Integer()
    product_type_enum = fields.Integer()
    unit_symbol = fields.Char()

    product_id = fields.Many2one("product.product", ondelete="set null")

    _sql_constraints = [
        (
            "geofolia_product_job_ext_farm_uniq",
            "unique(job_id, external_id, farm_identification_code)",
            "This product (and farm) has already been imported in this job.",
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
