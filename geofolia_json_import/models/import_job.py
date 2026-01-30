# -*- coding: utf-8 -*-

import base64
import json
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class GeofoliaImportJob(models.Model):
    _name = "geofolia.import.job"
    _description = "Geofolia Import Job"
    _order = "id desc"

    name = fields.Char(required=True, default=lambda self: _("New"))
    import_type = fields.Selection(
        selection=[
            ("fields", "Fields (Plots)"),
            ("products", "Products (Supplies)"),
            ("full", "Full (All blocks)"),
        ],
        required=True,
        default="full",
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done"), ("error", "Error")],
        default="draft",
        required=True,
    )
    apply_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("ready", "Ready"),
            ("partial", "Partial"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="draft",
        required=True,
        index=True,
    )

    file_name = fields.Char()
    file_data = fields.Binary(required=True)

    info_json = fields.Json()
    error = fields.Text()

    # simple mode
    line_ids = fields.One2many("geofolia.import.line", "job_id", string="Lines")

    # full mode
    product_line_ids = fields.One2many(
        "geofolia.import.product.line", "job_id", string="Products"
    )
    employee_line_ids = fields.One2many(
        "geofolia.import.employee.line", "job_id", string="Employees"
    )
    partner_line_ids = fields.One2many(
        "geofolia.import.partner.line", "job_id", string="Partners"
    )
    harvested_product_line_ids = fields.One2many(
        "geofolia.import.harvested.product.line",
        "job_id",
        string="Harvested Products",
    )
    equipment_line_ids = fields.One2many(
        "geofolia.import.equipment.line", "job_id", string="Equipments"
    )
    activity_line_ids = fields.One2many(
        "geofolia.import.activity.line", "job_id", string="Activities"
    )
    activity_employee_line_ids = fields.One2many(
        "geofolia.import.activity.employee.line", "job_id", string="Activity Employees"
    )

    total_count = fields.Integer(compute="_compute_apply_stats")
    pending_count = fields.Integer(compute="_compute_apply_stats")
    processed_count = fields.Integer(compute="_compute_apply_stats")
    error_count = fields.Integer(compute="_compute_apply_stats")

    # ----------------------------
    # Public actions
    # ----------------------------

    def action_parse(self):
        for job in self:
            try:
                payload = job._load_json_payload()
                job._parse_payload(payload)
                job.state = "done"
                job.apply_state = "ready" if job.import_type == "full" else "done"
                job.error = False
            except Exception as exc:  # noqa: BLE001
                job.state = "error"
                job.apply_state = "error"
                job.error = str(exc)

    def action_apply(self):
        for job in self:
            if job.import_type != "full":
                continue
            job._apply_full_export(only_pending=False)
            job._recompute_apply_state()

    def action_apply_pending(self):
        for job in self:
            if job.import_type != "full":
                continue
            job._apply_full_export(only_pending=True)
            job._recompute_apply_state()

    # ----------------------------
    # Parsing
    # ----------------------------

    def _load_json_payload(self):
        self.ensure_one()
        if not self.file_data:
            raise UserError(_("No file provided."))

        try:
            raw = base64.b64decode(self.file_data)
        except Exception as exc:  # noqa: BLE001
            raise UserError(_("Invalid file content: %s") % str(exc)) from exc

        last_exc = None
        for encoding in ("utf-8-sig", "utf-8"):
            try:
                return json.loads(raw.decode(encoding))
            except Exception as exc:  # noqa: BLE001
                last_exc = exc

        raise UserError(_("Invalid JSON file: %s") % str(last_exc)) from last_exc

    def _parse_payload(self, payload):
        self.ensure_one()
        if not isinstance(payload, dict):
            raise UserError(_("JSON root must be an object."))

        info = payload.get("Information")
        if not isinstance(info, dict):
            raise UserError(_("Missing or invalid 'Information' object."))
        self.info_json = info

        self._clear_lines()

        if self.import_type == "fields":
            items = payload.get("Fields")
            if not isinstance(items, list):
                raise UserError(_("Missing or invalid 'Fields' array."))
            self._create_lines_from_fields(items)
            return

        if self.import_type == "products":
            items = payload.get("Products")
            if not isinstance(items, list):
                raise UserError(_("Missing or invalid 'Products' array."))
            self._create_lines_from_products(items)
            return

        self._create_full_lines(payload)

    def _clear_lines(self):
        self.line_ids.unlink()
        self.product_line_ids.unlink()
        self.employee_line_ids.unlink()
        self.partner_line_ids.unlink()
        self.harvested_product_line_ids.unlink()
        self.equipment_line_ids.unlink()
        self.activity_line_ids.unlink()
        self.activity_employee_line_ids.unlink()

    def _create_full_lines(self, payload):
        self.ensure_one()

        products = payload.get("Products") or []
        employees = payload.get("Employees") or []
        partners = payload.get("Partners") or []
        harvested = payload.get("HarvestedProducts") or []
        equipments = payload.get("Equipments") or []
        activities = payload.get("Activities") or []

        if isinstance(products, list):
            self._create_product_lines(products)
        if isinstance(employees, list):
            self._create_employee_lines(employees)
        if isinstance(partners, list):
            self._create_partner_lines(partners)
        if isinstance(harvested, list):
            self._create_harvested_product_lines(harvested)
        if isinstance(equipments, list):
            self._create_equipment_lines(equipments)
        if isinstance(activities, list):
            self._create_activity_lines(activities)

    # ----------------------------
    # Helpers
    # ----------------------------

    def _to_datetime(self, value):
        if not value:
            return False
        v = str(value).strip()
        v = v.replace("T", " ")
        v = re.sub(r"Z$", "", v)
        if "." in v:
            v = v.split(".", 1)[0]
        return fields.Datetime.to_datetime(v)

    def _to_date(self, value):
        if not value:
            return False
        v = str(value).strip()
        if "T" in v:
            v = v.split("T", 1)[0]
        return fields.Date.to_date(v)

    def _json_text(self, value):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:  # noqa: BLE001
            return str(value)

    # ----------------------------
    # Simple mode
    # ----------------------------

    def _create_lines_from_fields(self, items):
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_uuid": it.get("Id"),
                    "code": it.get("Code"),
                    "name": it.get("Name"),
                    "harvest_year": it.get("HarvestYear"),
                    "area": it.get("Area"),
                    "city": it.get("City"),
                    "crop_name": it.get("CropName"),
                    "geography_wkt": it.get("Geography"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.line"].create(vals_list)

    def _create_lines_from_products(self, items):
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_uuid": it.get("SupplyId"),
                    "code": it.get("Code"),
                    "name": it.get("SupplyName"),
                    "supply_id": it.get("SupplyId"),
                    "category_enum": it.get("CategoryEnum"),
                    "product_type_enum": it.get("ProductTypeEnum"),
                    "unit_symbol": it.get("UnitSymbol"),
                    "botanical_species": it.get("BotanicalSpecies"),
                    "variety_name": it.get("VarietyName"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.line"].create(vals_list)

    # ----------------------------
    # Full mode: staging lines
    # ----------------------------

    def _create_product_lines(self, items):
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            supply_id = it.get("SupplyId")
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": supply_id,
                    "code": it.get("Code"),
                    "name": it.get("SupplyName"),
                    "category_enum": it.get("CategoryEnum"),
                    "product_type_enum": it.get("ProductTypeEnum"),
                    "unit_symbol": it.get("UnitSymbol"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.product.line"].create(vals_list)

    def _create_employee_lines(self, items):
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            ext_id = it.get("EmployeeId") or it.get("Id")
            name = it.get("Name") or it.get("EmployeeName") or it.get("LastName")
            first_name = it.get("FirstName") or it.get("EmployeeFirstName")
            if first_name and name and first_name not in name:
                name = f"{first_name} {name}"
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": ext_id,
                    "code": it.get("Code") or it.get("EmployeeFarmIdentificationCode"),
                    "name": name,
                    "email": it.get("Email"),
                    "phone": it.get("Phone"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.employee.line"].create(vals_list)

    def _create_partner_lines(self, items):
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            ext_id = it.get("PartnerId") or it.get("Id")
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": ext_id,
                    "code": it.get("Code"),
                    "name": it.get("Name"),
                    "vat": it.get("Vat") or it.get("VAT"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.partner.line"].create(vals_list)

    def _create_harvested_product_lines(self, items):
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            ext_id = it.get("HarvestedProductId") or it.get("Id")
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": ext_id,
                    "code": it.get("Code"),
                    "name": it.get("Name"),
                    "unit_symbol": it.get("UnitSymbol"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.harvested.product.line"].create(vals_list)

    def _create_equipment_lines(self, items):
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            ext_id = it.get("EquipmentId") or it.get("Id")
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": ext_id,
                    "code": it.get("Code"),
                    "name": it.get("Name") or it.get("EquipmentName"),
                    "category": it.get("Category"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.equipment.line"].create(vals_list)

    def _create_activity_lines(self, items):
        ActivityLine = self.env["geofolia.import.activity.line"]
        EmpLine = self.env["geofolia.import.activity.employee.line"]

        act_vals = []
        emp_vals = []

        for it in items:
            if not isinstance(it, dict):
                continue

            action_id = it.get("ActionId") or it.get("Id")
            act_vals.append(
                {
                    "job_id": self.id,
                    "external_id": action_id,
                    "farm_identification_code": it.get("FarmIdentificationCode"),
                    "harvest_year": it.get("HarvestYear"),
                    "operation_name": it.get("OperationName"),
                    "operation_category": it.get("OperationCategory"),
                    "status_code": it.get("StatusCode"),
                    "status_name": it.get("StatusName"),
                    "comment": it.get("Comment"),
                    "duration_minutes": it.get("Duration"),
                    "starting_date": self._to_date(it.get("StartingDate")),
                    "ending_date": self._to_date(it.get("EndingDate")),
                    "last_modification_dt": self._to_datetime(it.get("LastModificationDate")),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )

        activities = ActivityLine.create(act_vals) if act_vals else ActivityLine
        by_external = {a.external_id: a for a in activities}

        for it in items:
            if not isinstance(it, dict):
                continue
            action_id = it.get("ActionId") or it.get("Id")
            activity = by_external.get(action_id)
            if not activity:
                continue

            employees = it.get("ActionEmployees") or []
            if not isinstance(employees, list):
                continue

            for emp in employees:
                if not isinstance(emp, dict):
                    continue
                emp_vals.append(
                    {
                        "job_id": self.id,
                        "activity_line_id": activity.id,
                        "employee_action_id": emp.get("EmployeeActionId") or action_id,
                        "employee_recognition_id": emp.get("EmployeeRecognitionId"),
                        "employee_order": emp.get("EmployeeOrder"),
                        "employee_farm_identification_code": emp.get(
                            "EmployeeFarmIdentificationCode"
                        ),
                        "employee_first_name": emp.get("EmployeeFirstName"),
                        "employee_name": emp.get("EmployeeName"),
                        "employee_id_external": emp.get("EmployeeId"),
                        "employee_time": emp.get("EmployeeTime"),
                        "raw_json": emp,
                        "raw_json_text": self._json_text(emp),
                    }
                )

        if emp_vals:
            EmpLine.create(emp_vals)

    # ----------------------------
    # Apply stats/state
    # ----------------------------

    @api.depends(
        "product_line_ids.sync_state",
        "employee_line_ids.sync_state",
        "partner_line_ids.sync_state",
        "harvested_product_line_ids.sync_state",
        "equipment_line_ids.sync_state",
        "activity_employee_line_ids.sync_state",
        "import_type",
    )
    def _compute_apply_stats(self):
        processed_states = ("created", "updated", "no_action", "skipped")
        for job in self:
            if job.import_type != "full":
                job.total_count = 0
                job.pending_count = 0
                job.processed_count = 0
                job.error_count = 0
                continue

            blocks = job._get_full_lines_by_block()
            total = pending = processed = errors = 0
            for lines in blocks.values():
                total += len(lines)
                pending += len(lines.filtered(lambda l: l.sync_state == "pending"))
                errors += len(lines.filtered(lambda l: l.sync_state == "error"))
                processed += len(lines.filtered(lambda l: l.sync_state in processed_states))

            job.total_count = total
            job.pending_count = pending
            job.processed_count = processed
            job.error_count = errors

    def _get_full_lines_by_block(self):
        self.ensure_one()
        return {
            "products": self.product_line_ids,
            "employees": self.employee_line_ids,
            "partners": self.partner_line_ids,
            "harvested_products": self.harvested_product_line_ids,
            "equipments": self.equipment_line_ids,
            "activity_employees": self.activity_employee_line_ids,
        }

    def _recompute_apply_state(self):
        self.ensure_one()
        if self.import_type != "full":
            self.apply_state = "done"
            return

        blocks = self._get_full_lines_by_block()
        total = sum(len(v) for v in blocks.values())
        if not total:
            self.apply_state = "done"
            return

        has_pending = any(v.filtered(lambda l: l.sync_state == "pending") for v in blocks.values())
        has_error = any(v.filtered(lambda l: l.sync_state == "error") for v in blocks.values())

        if has_error:
            self.apply_state = "partial" if has_pending else "error"
            return

        self.apply_state = "ready" if has_pending else "done"

    # ----------------------------
    # Apply: create/update Odoo records
    # ----------------------------

    def _apply_full_export(self, only_pending=False):
        self.ensure_one()

        def _todo(rs):
            if only_pending:
                return rs.filtered(lambda l: l.sync_state == "pending")
            return rs.filtered(lambda l: l.sync_state in ("pending", "error"))

        for line in _todo(self.product_line_ids):
            self._apply_product_line(line)

        for line in _todo(self.employee_line_ids):
            self._apply_employee_line(line)

        for line in _todo(self.harvested_product_line_ids):
            self._apply_product_like(line, label="harvested_products")

        for line in _todo(self.equipment_line_ids):
            self._apply_product_like(line, label="equipments")

        for line in _todo(self.activity_employee_line_ids):
            self._apply_activity_employee_line(line)

    def _apply_product_line(self, line):
        Product = self.env["product.product"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write({"sync_state": "skipped", "sync_message": _("Missing id.")})
                    return

                product = Product.search(
                    [("geofolia_external_id", "=", line.external_id)], limit=1
                )
                vals = {
                    "name": line.name or line.code or _("Geofolia product"),
                    "default_code": line.code,
                    "geofolia_external_id": line.external_id,
                }

                if product:
                    changed = any(
                        vals.get(k) and product[k] != vals[k] for k in ("name", "default_code")
                    )
                    if changed:
                        product.write(vals)
                        line.write(
                            {
                                "product_id": product.id,
                                "sync_state": "updated",
                                "sync_message": _("Updated product."),
                            }
                        )
                    else:
                        line.write(
                            {
                                "product_id": product.id,
                                "sync_state": "no_action",
                                "sync_message": _("Already up to date."),
                            }
                        )
                    return

                product = Product.create(vals)
                line.write(
                    {
                        "product_id": product.id,
                        "sync_state": "created",
                        "sync_message": _("Created product."),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            line.write({"sync_state": "error", "sync_message": str(exc)})

    def _apply_employee_line(self, line):
        Employee = self.env["hr.employee"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write({"sync_state": "skipped", "sync_message": _("Missing id.")})
                    return

                emp = Employee.search(
                    [("geofolia_external_id", "=", line.external_id)], limit=1
                )
                vals = {
                    "name": line.name or line.code or _("Geofolia employee"),
                    "work_email": line.email,
                    "work_phone": line.phone,
                    "geofolia_external_id": line.external_id,
                }

                if emp:
                    emp.write({k: v for k, v in vals.items() if v})
                    line.write(
                        {
                            "employee_id": emp.id,
                            "sync_state": "updated",
                            "sync_message": _("Updated employee."),
                        }
                    )
                    return

                emp = Employee.create(vals)
                line.write(
                    {
                        "employee_id": emp.id,
                        "sync_state": "created",
                        "sync_message": _("Created employee."),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            line.write({"sync_state": "error", "sync_message": str(exc)})

    def _apply_product_like(self, line, label):
        Product = self.env["product.product"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write({"sync_state": "skipped", "sync_message": _("Missing id.")})
                    return

                product = Product.search(
                    [("geofolia_external_id", "=", line.external_id)], limit=1
                )
                vals = {
                    "name": line.name or line.code or _("Geofolia (%s)") % label,
                    "default_code": line.code,
                    "geofolia_external_id": line.external_id,
                }

                if product:
                    product.write({k: v for k, v in vals.items() if v})
                    line.write(
                        {
                            "product_id": product.id,
                            "sync_state": "updated",
                            "sync_message": _("Updated product."),
                        }
                    )
                    return

                product = Product.create(vals)
                line.write(
                    {
                        "product_id": product.id,
                        "sync_state": "created",
                        "sync_message": _("Created product."),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            line.write({"sync_state": "error", "sync_message": str(exc)})

    def _apply_activity_employee_line(self, line):
        Analytic = self.env["account.analytic.line"]
        Employee = self.env["hr.employee"]

        try:
            with self.env.cr.savepoint():
                if line.analytic_line_id:
                    line.write(
                        {"sync_state": "no_action", "sync_message": _("Already linked.")}
                    )
                    return

                emp = False
                if line.employee_id_external:
                    emp = Employee.search(
                        [("geofolia_external_id", "=", line.employee_id_external)],
                        limit=1,
                    )
                if not emp and line.employee_name:
                    emp = Employee.search([("name", "=", line.employee_name)], limit=1)

                if not emp:
                    line.write(
                        {"sync_state": "skipped", "sync_message": _("Employee not found.")}
                    )
                    return

                ext_id = ":".join(
                    [
                        line.employee_action_id or "",
                        line.employee_recognition_id or "",
                        str(line.employee_order or 0),
                    ]
                )

                existing = Analytic.search(
                    [("geofolia_external_id", "=", ext_id)], limit=1
                )

                activity = line.activity_line_id
                unit_amount = (line.employee_time or 0.0) / 60.0

                vals = {
                    "name": activity.operation_name or _("Geofolia activity"),
                    "date": activity.starting_date or activity.ending_date,
                    "unit_amount": unit_amount,
                    "employee_id": emp.id,
                    "geofolia_external_id": ext_id,
                }

                if existing:
                    existing.write(vals)
                    line.write(
                        {
                            "employee_id": emp.id,
                            "analytic_line_id": existing.id,
                            "sync_state": "updated",
                            "sync_message": _("Updated analytic line."),
                        }
                    )
                    return

                rec = Analytic.create(vals)
                line.write(
                    {
                        "employee_id": emp.id,
                        "analytic_line_id": rec.id,
                        "sync_state": "created",
                        "sync_message": _("Created analytic line."),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            line.write({"sync_state": "error", "sync_message": str(exc)})


class ProductProduct(models.Model):
    _inherit = "product.product"

    geofolia_external_id = fields.Char(index=True)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    geofolia_external_id = fields.Char(index=True)


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    geofolia_external_id = fields.Char(index=True)
