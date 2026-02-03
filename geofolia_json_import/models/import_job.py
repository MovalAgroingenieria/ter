# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

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

    date_range_id = fields.Many2one(
        comodel_name="date.range",
        string="Campaign (Date Range)",
        domain="[('is_unit_use_type', '=', True)]",
        help="Campaign for ter.unit when importing Fields. From wizard.",
    )

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

    total_count = fields.Integer(compute="_compute_apply_stats", store=False)
    pending_count = fields.Integer(compute="_compute_apply_stats", store=False)
    processed_count = fields.Integer(compute="_compute_apply_stats", store=False)
    error_count = fields.Integer(compute="_compute_apply_stats", store=False)

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

    def action_apply_fields(self):
        for job in self:
            if job.import_type != "fields":
                continue
            lines = job.line_ids.filtered(
                lambda l: l.sync_state in ("pending", "error")
            )
            for line in lines:
                job._apply_field_line_to_ter_unit(line)

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
    # Simple mode: staging lines
    # ----------------------------

    def _create_lines_from_fields(self, items):
        self.ensure_one()
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
        self.ensure_one()
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
        self.ensure_one()
        vals_list = []
        seen = set()
        for it in items:
            if not isinstance(it, dict):
                continue
            supply_id = it.get("SupplyId")
            if supply_id and supply_id in seen:
                continue
            if supply_id:
                seen.add(supply_id)
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": supply_id,
                    "recognition_id": it.get("RecognitionId"),
                    "code": it.get("Code"),
                    "name": it.get("SupplyName"),
                    "rn_reference_supply_name": it.get("RNReferenceSupplyName"),
                    "rn_reference_supply_code": it.get("RNReferenceSupplyCode"),
                    "unit_symbol": it.get("UnitSymbol"),
                    "product_form_enum": it.get("ProductFormEnum"),
                    "category_enum": it.get("CategoryEnum"),
                    "product_type_enum": it.get("ProductTypeEnum"),
                    "product_component_n_total": it.get("ProductComponentNTotal"),
                    "product_component_p2o5": it.get("ProductComponentP2O5"),
                    "product_component_k2o": it.get("ProductComponentK2O"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.product.line"].create(vals_list)

    def _create_employee_lines(self, items):
        self.ensure_one()
        vals_list = []
        seen = set()
        for it in items:
            if not isinstance(it, dict):
                continue
            ext_id = it.get("EmployeeId") or it.get("Id")
            if ext_id and ext_id in seen:
                continue
            if ext_id:
                seen.add(ext_id)
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
                    "first_name": first_name,
                    "national_identification_code": it.get("NationalIdentificationCode"),
                    "specific_number": it.get("SpecificNumber"),
                    "email": it.get("Email"),
                    "phone": it.get("Phone"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.employee.line"].create(vals_list)

    def _create_partner_lines(self, items):
        self.ensure_one()
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
        self.ensure_one()
        vals_list = []
        seen = set()
        for it in items:
            if not isinstance(it, dict):
                continue
            ext_id = it.get("HarvestId") or it.get("HarvestedProductId") or it.get("Id")
            if ext_id and ext_id in seen:
                continue
            if ext_id:
                seen.add(ext_id)
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": ext_id,
                    "code": it.get("Code"),
                    "name": it.get("Name"),
                    "botanical_species_name": it.get("BotanicalSpeciesName"),
                    "botanical_species_id": it.get("BotanicalSpeciesId"),
                    "harvested_product_kind_id": it.get("HarvestedProductKindId"),
                    "unit_symbol": it.get("UnitSymbol"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.harvested.product.line"].create(vals_list)

    def _create_equipment_lines(self, items):
        self.ensure_one()
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
        self.ensure_one()
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
                    "last_modification_dt": self._to_datetime(
                        it.get("LastModificationDate")
                    ),
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

            zones = it.get("CropZoneIds") or []
            zones_by_rec = {
                z.get("RecognitionId"): z
                for z in zones
                if isinstance(z, dict) and z.get("RecognitionId")
            }
            for emp in employees:
                if not isinstance(emp, dict):
                    continue
                rec_id = emp.get("EmployeeRecognitionId")
                zone = zones_by_rec.get(rec_id) if rec_id else None
                emp_vals.append(
                    {
                        "job_id": self.id,
                        "activity_line_id": activity.id,
                        "employee_action_id": emp.get("EmployeeActionId") or action_id,
                        "employee_recognition_id": rec_id,
                        "employee_order": emp.get("EmployeeOrder"),
                        "employee_farm_identification_code": emp.get(
                            "EmployeeFarmIdentificationCode"
                        ),
                        "employee_first_name": emp.get("EmployeeFirstName"),
                        "employee_name": emp.get("EmployeeName"),
                        "employee_id_external": emp.get("EmployeeId"),
                        "employee_time": emp.get("EmployeeTime"),
                        "plot_code": zone.get("PlotCode") if zone else None,
                        "worked_surface": zone.get("WorkedSurface") if zone else None,
                        "raw_json": emp,
                        "raw_json_text": self._json_text(emp),
                    }
                )

        if emp_vals:
            EmpLine.create(emp_vals)

    # ----------------------------
    # Apply: ter.unit mapping (Fields -> ter.unit)
    # ----------------------------

    def _get_date_range_for_harvest_year(self, harvest_year):
        """Find date.range for harvest year."""
        year = int(harvest_year or 0) or fields.Date.today().year
        DateRange = self.env["date.range"]
        default = self.env.company.geofolia_default_date_range_id
        if default and default.is_unit_use_type:
            return default
        candidates = DateRange.search(
            [
                ("is_unit_use_type", "=", True),
                ("date_start", "<=", "%d-12-31" % year),
                ("date_end", ">=", "%d-01-01" % year),
            ],
            limit=1,
        )
        if candidates:
            return candidates[0]
        return DateRange.search([("is_unit_use_type", "=", True)], limit=1)

    def _get_ter_unit_vals_from_field_line(self, line):
        """Build ter.unit vals from Geofolia field line (Field = ter.unit)."""
        self.ensure_one()
        raw = line.raw_json or {}
        vals = {
            "geofolia_uid": line.external_uuid,
            "name": (line.name or line.code or "").strip() or f"GF-{line.external_uuid}",
            "geofolia_code": raw.get("Code"),
            "geofolia_name": raw.get("Name"),
            "geofolia_parent_id1": raw.get("ParentId1"),
            "geofolia_main_plot_id": raw.get("MainPlotId"),
            "geofolia_irrigation_kind": raw.get("IrrigationKind"),
            "geofolia_irrigation_kind_name": raw.get("IrrigationKindName"),
            "geofolia_comment": raw.get("Comment"),
            "geofolia_ferti_diary_comment": raw.get("FertiDiaryComment"),
            "geofolia_phyto_diary_comment": raw.get("PhytoDiaryComment"),
            "geofolia_plot_kind": raw.get("PlotKind"),
            "geofolia_plot_kind_name": raw.get("PLotKindName") or raw.get(
                "PlotKindName"
            ),
            "geofolia_crop_name": raw.get("CropName"),
            "geofolia_botanical_species_code": raw.get("BotanicalSpeciesCode"),
            "geofolia_variety_name": raw.get("VarietyName"),
            "geofolia_unit": raw.get("Unit"),
        }
        if line.area is not None:
            area_val = float(line.area)
            unit = (raw.get("Unit") or "").strip().lower()
            vals["area_official"] = (
                area_val if unit == "ha" else (area_val / 10000.0)
            )
        vals["geofolia_area"] = line.area
        if line.geography_wkt:
            wkt = (line.geography_wkt or "").strip()
            if wkt and not wkt.upper().startswith("SRID="):
                srid = self._get_geometry_srid_from_job()
                vals["geom_ewkt"] = "SRID=%s;" % srid + wkt
            else:
                vals["geom_ewkt"] = wkt
        vals["geofolia_geography"] = line.geography_wkt
        vals["geofolia_last_modification_date"] = self._to_datetime(
            raw.get("LastModificationDate")
        )
        vals["geofolia_last_modification_geometry_date"] = self._to_datetime(
            raw.get("LastModificationGeometryDate")
        )
        date_range = self.date_range_id or self._get_date_range_for_harvest_year(
            line.harvest_year
        )
        if date_range:
            vals["date_range_id"] = date_range.id
            vals["date_start"] = date_range.date_start
            vals["date_end"] = date_range.date_end
            if date_range.use_type_id:
                vals["use_type_id"] = date_range.use_type_id.id
        else:
            year = int(line.harvest_year or 0) or self.env.context.get("date") or fields.Date.today().year
            vals["date_start"] = "%d-01-01" % year
            vals["date_end"] = "%d-12-31" % year
        vals.setdefault("area_official", 0.0)
        return vals

    def _apply_field_line_to_ter_unit(self, line):
        """Create or update ter.unit from Geofolia Field line."""
        self.ensure_one()
        Unit = self.env["ter.unit"]

        ext_id = line.external_uuid
        if not ext_id:
            line.write({"sync_state": "skipped", "sync_message": _("Missing id.")})
            return

        vals = self._get_ter_unit_vals_from_field_line(line)
        if not vals.get("date_range_id"):
            line.write(
                {
                    "sync_state": "skipped",
                    "sync_message": _(
                        "No campaign (date range). Create one with "
                        "'Usable for Unit Use' or set company default."
                    ),
                }
            )
            return
        if not vals.get("geom_ewkt"):
            line.write(
                {
                    "sync_state": "skipped",
                    "sync_message": _(
                        "Field has no geometry. ter.unit needs geometry to resolve parcel."
                    ),
                }
            )
            return

        try:
            with self.env.cr.savepoint():
                unit = Unit.search([("geofolia_uid", "=", ext_id)], limit=1)
                if unit:
                    write_vals = {
                        k: v for k, v in vals.items()
                        if k in unit._fields and v not in (False, None, "")
                    }
                    if write_vals:
                        unit.write(write_vals)
                    line.write(
                        {
                            "ter_unit_id": unit.id,
                            "sync_state": "updated",
                            "sync_message": _("Updated unit."),
                        }
                    )
                else:
                    unit = Unit.create(vals)
                    line.write(
                        {
                            "ter_unit_id": unit.id,
                            "sync_state": "created",
                            "sync_message": _("Created unit."),
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            line.write({"sync_state": "error", "sync_message": str(exc)})

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
                processed += len(
                    lines.filtered(lambda l: l.sync_state in processed_states)
                )

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

        has_pending = any(
            v.filtered(lambda l: l.sync_state == "pending") for v in blocks.values()
        )
        has_error = any(
            v.filtered(lambda l: l.sync_state == "error") for v in blocks.values()
        )

        if has_error:
            self.apply_state = "partial" if has_pending else "error"
            return

        self.apply_state = "ready" if has_pending else "done"

    # ----------------------------
    # Apply: create/update Odoo records (full)
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
            self._apply_harvested_product_line(line)

        for line in _todo(self.equipment_line_ids):
            self._apply_equipment_line(line)

        for line in _todo(self.activity_employee_line_ids):
            self._apply_activity_employee_line(line)

    def _apply_product_line(self, line):
        Product = self.env["product.product"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write(
                        {"sync_state": "skipped", "sync_message": _("Missing id.")}
                    )
                    return

                product = Product.search(
                    [
                        ("geofolia_source", "=", "products"),
                        ("geofolia_external_id", "=", line.external_id),
                    ],
                    limit=1,
                )
                vals = {
                    "name": line.name or line.code or _("Geofolia product"),
                    "default_code": line.code,
                    "geofolia_external_id": line.external_id,
                    "geofolia_source": "products",
                    "geofolia_recognition_id": line.recognition_id,
                    "geofolia_rn_reference_supply_name": line.rn_reference_supply_name,
                    "geofolia_rn_reference_supply_code": line.rn_reference_supply_code,
                    "geofolia_unit_symbol": line.unit_symbol,
                    "geofolia_product_form_enum": line.product_form_enum,
                    "geofolia_product_component_n_total": line.product_component_n_total,
                    "geofolia_product_component_p2o5": line.product_component_p2o5,
                    "geofolia_product_component_k2o": line.product_component_k2o,
                    "maintenance_ok": True,
                }

                if product:
                    check_keys = (
                        "name",
                        "default_code",
                        "geofolia_recognition_id",
                        "geofolia_rn_reference_supply_name",
                        "geofolia_rn_reference_supply_code",
                        "geofolia_unit_symbol",
                        "geofolia_product_form_enum",
                        "geofolia_product_component_n_total",
                        "geofolia_product_component_p2o5",
                        "geofolia_product_component_k2o",
                    )
                    changed = any(
                        vals.get(k) is not None and product[k] != vals[k]
                        for k in check_keys
                        if k in vals
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
                    line.write(
                        {"sync_state": "skipped", "sync_message": _("Missing id.")}
                    )
                    return

                emp = Employee.search(
                    [("geofolia_external_id", "=", line.external_id)], limit=1
                )
                vals = {
                    "name": line.name or line.code or _("Geofolia employee"),
                    "work_email": line.email,
                    "work_phone": line.phone,
                    "geofolia_external_id": line.external_id,
                    "geofolia_first_name": line.first_name,
                    "geofolia_national_identification_code": (
                        line.national_identification_code
                    ),
                    "geofolia_specific_number": line.specific_number,
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

    def _apply_harvested_product_line(self, line):
        """Create or update project.task from Geofolia HarvestedProducts line."""
        Task = self.env["project.task"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write(
                        {"sync_state": "skipped", "sync_message": _("Missing id.")}
                    )
                    return

                project = self.env.company.geofolia_timesheet_project_id
                if not project:
                    line.write(
                        {
                            "sync_state": "error",
                            "sync_message": _(
                                "Geofolia timesheet project not configured."
                            ),
                        }
                    )
                    return

                task = Task.search(
                    [("geofolia_harvest_id", "=", line.external_id)], limit=1
                )
                vals = {
                    "name": line.name or line.code or _("Geofolia harvested product"),
                    "project_id": project.id,
                    "geofolia_harvest_id": line.external_id,
                    "geofolia_botanical_species_name": line.botanical_species_name,
                    "geofolia_botanical_species_id": line.botanical_species_id,
                    "geofolia_harvested_product_kind_id": line.harvested_product_kind_id,
                    "geofolia_unit_symbol": line.unit_symbol,
                }

                if task:
                    write_vals = {k: v for k, v in vals.items() if k != "project_id"}
                    changed = any(
                        write_vals.get(k) != task[k]
                        for k in write_vals
                        if k in task._fields
                    )
                    if changed:
                        task.write(write_vals)
                        line.write(
                            {
                                "task_id": task.id,
                                "sync_state": "updated",
                                "sync_message": _("Updated task."),
                            }
                        )
                    else:
                        line.write(
                            {
                                "task_id": task.id,
                                "sync_state": "no_action",
                                "sync_message": _("Already up to date."),
                            }
                        )
                    return

                task = Task.create(vals)
                line.write(
                    {
                        "task_id": task.id,
                        "sync_state": "created",
                        "sync_message": _("Created task."),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            line.write({"sync_state": "error", "sync_message": str(exc)})

    def _apply_equipment_line(self, line):
        """Create or update maintenance.equipment from Geofolia Equipment line."""
        Equipment = self.env["maintenance.equipment"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write(
                        {"sync_state": "skipped", "sync_message": _("Missing id.")}
                    )
                    return

                project = self.env.company.geofolia_maintenance_project_id
                if not project:
                    line.write(
                        {
                            "sync_state": "error",
                            "sync_message": _(
                                "Geofolia maintenance project not configured."
                            ),
                        }
                    )
                    return

                equipment = Equipment.search(
                    [("geofolia_equipment_id", "=", line.external_id)], limit=1
                )
                vals = {
                    "name": line.name or line.code or _("Geofolia equipment"),
                    "geofolia_equipment_id": line.external_id,
                    "project_id": project.id,
                }

                if equipment:
                    write_vals = {
                        k: v for k, v in vals.items() if k != "project_id" and v
                    }
                    if write_vals:
                        equipment.write(write_vals)
                    line.write(
                        {
                            "equipment_id": equipment.id,
                            "sync_state": "updated",
                            "sync_message": _("Updated equipment."),
                        }
                    )
                    return

                equipment = Equipment.create(vals)
                line.write(
                    {
                        "equipment_id": equipment.id,
                        "sync_state": "created",
                        "sync_message": _("Created equipment."),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            line.write({"sync_state": "error", "sync_message": str(exc)})

    def _apply_product_like(self, line, label):
        Product = self.env["product.product"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write(
                        {"sync_state": "skipped", "sync_message": _("Missing id.")}
                    )
                    return

                product = Product.search(
                    [("geofolia_external_id", "=", line.external_id)], limit=1
                )
                raw = line.raw_json or {}
                vals = {
                    "name": line.name or line.code or _("Geofolia (%s)") % label,
                    "default_code": line.code,
                    "geofolia_external_id": line.external_id,
                    "geofolia_recognition_id": raw.get("RecognitionId"),
                    "geofolia_product_component_n_total": raw.get("ProductComponentNTotal"),
                    "geofolia_product_component_p2o5": raw.get("ProductComponentP2O5"),
                    "geofolia_product_component_k2o": raw.get("ProductComponentK2O"),
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

    def _resolve_parcel_from_farm_identification_code(self, farm_code):
        """Resolve ter.parcel from Geofolia FarmIdentificationCode (Field Code or farm id)."""
        if not farm_code:
            return self.env["ter.parcel"]
        farm_code = str(farm_code).strip()
        Parcel = self.env["ter.parcel"]
        # First: match alphanum_code (Field Code)
        parcel = Parcel.search([("alphanum_code", "=", farm_code)], limit=1)
        if parcel:
            return parcel
        # Second: match geofolia_farm_identification_code
        return Parcel.search(
            [("geofolia_farm_identification_code", "=", farm_code)], limit=1
        )

    def _resolve_unit_from_crop_zone(self, activity_raw, recognition_id):
        """
        Resolve ter.unit from Activity CropZoneIds. CropZone.RecognitionId may match
        ter.unit.geofolia_uid (Field Id from Geofolia).
        """
        if not activity_raw or not recognition_id:
            return self.env["ter.unit"]
        zones = activity_raw.get("CropZoneIds") or []
        if not isinstance(zones, list):
            return self.env["ter.unit"]
        zone = next(
            (
                z
                for z in zones
                if isinstance(z, dict) and z.get("RecognitionId") == recognition_id
            ),
            None,
        )
        if not zone:
            return self.env["ter.unit"]
        field_id = zone.get("FieldId") or zone.get("RecognitionId")
        if field_id:
            return self.env["ter.unit"].search(
                [("geofolia_uid", "=", str(field_id))], limit=1
            )
        return self.env["ter.unit"]

    def _resolve_parcel_from_crop_zone(self, activity_raw, recognition_id):
        """
        Resolve ter.parcel from Activity CropZoneIds.
        First tries ter.unit (Fields) by geofolia_uid, then falls back to ter.parcel.
        """
        unit = self._resolve_unit_from_crop_zone(activity_raw, recognition_id)
        if unit and unit.parcel_id:
            return unit.parcel_id
        if not activity_raw or not recognition_id:
            return self.env["ter.parcel"]
        zones = activity_raw.get("CropZoneIds") or []
        if not isinstance(zones, list):
            return self.env["ter.parcel"]
        zone = next(
            (
                z
                for z in zones
                if isinstance(z, dict) and z.get("RecognitionId") == recognition_id
            ),
            None,
        )
        if not zone:
            return self.env["ter.parcel"]
        plot_code = (zone.get("PlotCode") or "").strip()
        farm_code = (zone.get("FarmIdentificationCode") or "").strip()
        Parcel = self.env["ter.parcel"]
        if plot_code and farm_code:
            parcel = Parcel.search(
                [
                    ("geofolia_farm_identification_code", "=", farm_code),
                    ("alphanum_code", "=", plot_code),
                ],
                limit=1,
            )
            if parcel:
                return parcel
        if plot_code:
            return Parcel.search([("alphanum_code", "=", plot_code)], limit=1)
        if farm_code:
            return self._resolve_parcel_from_farm_identification_code(farm_code)
        return self.env["ter.parcel"]

    def _resolve_ter_unit_for_parcel_date(self, parcel, activity_date):
        """Find active ter.unit for parcel at activity date (begin_date <= date <= end_date)."""
        if not parcel or not activity_date:
            return self.env["ter.unit"]
        return self.env["ter.unit"].search(
            [
                ("parcel_id", "=", parcel.id),
                ("date_start", "<=", activity_date),
                ("date_end", ">=", activity_date),
                ("active", "=", True),
            ],
            order="sequence, id",
            limit=1,
        )

    def _get_or_create_task_for_operation(
        self, project, operation_name=None, operation_category=None
    ):
        """
        Find or create project.task for the operation from the JSON.
        Matches by operation_name first, then operation_category.
        Creates the task if it does not exist.
        Falls back to company default task when both are empty.
        """
        Task = self.env["project.task"]
        name = (operation_name or operation_category or "").strip()
        if not name:
            default_task = self.env.company.geofolia_timesheet_task_id
            if default_task and default_task.project_id == project:
                return default_task
            name = _("Geofolia activity")
        task = Task.search(
            [
                ("project_id", "=", project.id),
                ("name", "=", name),
            ],
            limit=1,
        )
        if task:
            return task
        return Task.create(
            {
                "project_id": project.id,
                "name": name,
            }
        )

    def _get_geometry_srid_from_job(self):
        """Extract SRID from info_json CoordinateReferenceSystem. Default 25830 (ETRS89/UTM)."""
        info = self.info_json or {}
        crs = info.get("CoordinateReferenceSystem") or ""
        if isinstance(crs, str) and "25830" in crs:
            return 25830
        if isinstance(crs, str) and "4326" in crs:
            return 4326
        return 25830

    def _get_territory_vals_for_analytic_line(self, activity, employee_line=None):
        """
        Build territory-related vals for account.analytic.line from activity.
        Uses CropZoneIds + EmployeeRecognitionId for precise ter.unit/parcel per employee,
        else falls back to Activity FarmIdentificationCode.
        """
        vals = {}
        parcel = self.env["ter.parcel"]
        ter_unit = self.env["ter.unit"]
        activity_raw = activity.raw_json or {}

        if employee_line and employee_line.employee_recognition_id:
            ter_unit = self._resolve_unit_from_crop_zone(
                activity_raw, employee_line.employee_recognition_id
            )
            if ter_unit and ter_unit.parcel_id:
                parcel = ter_unit.parcel_id
            elif not ter_unit:
                parcel = self._resolve_parcel_from_crop_zone(
                    activity_raw, employee_line.employee_recognition_id
                )
        if not parcel and activity.farm_identification_code:
            parcel = self._resolve_parcel_from_farm_identification_code(
                activity.farm_identification_code
            )
        if not parcel and not ter_unit:
            return vals

        if parcel:
            vals["ter_parcel_id"] = parcel.id
            vals["ter_property_id"] = parcel.property_id.id if parcel.property_id else False

        activity_date = activity.starting_date or activity.ending_date
        if not ter_unit and parcel:
            ter_unit = self._resolve_ter_unit_for_parcel_date(parcel, activity_date)
        if ter_unit:
            vals["ter_unit_id"] = ter_unit.id
            vals["ter_use_type_id"] = ter_unit.use_type_id.id if ter_unit.use_type_id else False
            if ter_unit.account_id:
                vals["account_id"] = ter_unit.account_id.id
        vals["geofolia_status_name"] = activity.status_name
        vals["geofolia_status_code"] = activity.status_code
        if employee_line and employee_line.worked_surface:
            vals["geofolia_worked_surface"] = employee_line.worked_surface
        return vals

    def _get_or_create_maintenance_request_for_activity(self, activity):
        """Get or create maintenance.request for Geofolia activity. Idempotent by geofolia_action_id."""
        self.ensure_one()
        if not activity.external_id:
            return self.env["maintenance.request"]
        Request = self.env["maintenance.request"]
        existing = Request.search(
            [("geofolia_action_id", "=", activity.external_id)], limit=1
        )
        if existing:
            if not activity.maintenance_request_id:
                activity.maintenance_request_id = existing.id
            return existing

        project = self.env.company.geofolia_maintenance_project_id
        if not project:
            return self.env["maintenance.request"]

        task = self._get_or_create_task_for_operation(
            project,
            operation_name=activity.operation_name,
            operation_category=activity.operation_category,
        )

        schedule_date = None
        if activity.starting_date:
            schedule_date = fields.Datetime.combine(
                activity.starting_date, fields.Datetime.min.time()
            )

        vals = {
            "name": activity.operation_name or _("Geofolia activity"),
            "geofolia_action_id": activity.external_id,
            "project_id": project.id,
            "task_id": task.id if task else False,
            "request_date": activity.starting_date or activity.ending_date,
            "schedule_date": schedule_date,
            "maintenance_type": "corrective",
        }
        if activity.comment:
            vals["description"] = "<p>%s</p>" % (
                str(activity.comment or "").replace("\n", "<br/>")
            )

        request = Request.create(vals)
        activity.maintenance_request_id = request.id
        return request

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
                        {
                            "sync_state": "skipped",
                            "sync_message": _("Employee not found."),
                        }
                    )
                    return

                company = self.env.company
                project = (
                    company.geofolia_maintenance_project_id
                    or company.geofolia_timesheet_project_id
                )
                if not project:
                    line.write(
                        {
                            "sync_state": "error",
                            "sync_message": _(
                                "Missing Geofolia maintenance or timesheet project."
                            ),
                        }
                    )
                    return

                activity = line.activity_line_id
                maint_request = self._get_or_create_maintenance_request_for_activity(
                    activity
                )
                if not maint_request:
                    line.write(
                        {
                            "sync_state": "error",
                            "sync_message": _(
                                "Could not create maintenance request."
                            ),
                        }
                    )
                    return

                if emp and maint_request.employee_ids and emp not in maint_request.employee_ids:
                    maint_request.employee_ids = [(4, emp.id)]
                elif emp and not maint_request.employee_ids:
                    maint_request.employee_ids = [(4, emp.id)]

                task = maint_request.task_id or self._get_or_create_task_for_operation(
                    project,
                    operation_name=activity.operation_name,
                    operation_category=activity.operation_category,
                )

                ext_id = ":".join(
                    [
                        line.employee_action_id or "",
                        line.employee_recognition_id or "",
                        str(line.employee_order or 0),
                    ]
                )

                vals = {
                    "name": activity.operation_name or _("Geofolia activity"),
                    "geofolia_operation_category": activity.operation_category,
                    "date": activity.starting_date or activity.ending_date,
                    "unit_amount": (line.employee_time or 0.0) / 60.0,
                    "employee_id": emp.id,
                    "geofolia_external_id": ext_id,
                    "project_id": project.id,
                    "task_id": task.id if task else False,
                    "maintenance_request_id": maint_request.id,
                    "geofolia_activity_line_id": activity.id,
                }

                territory_vals = self._get_territory_vals_for_analytic_line(
                    activity, employee_line=line
                )
                vals.update(territory_vals)

                existing = Analytic.search(
                    [("geofolia_external_id", "=", ext_id)], limit=1
                )
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


