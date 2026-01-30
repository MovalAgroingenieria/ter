# -*- coding: utf-8 -*-

import base64
import json

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
            ("full", "Full export (multi-block)"),
        ],
        required=True,
    )

    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done"), ("error", "Error")],
        default="draft",
        required=True,
    )

    file_name = fields.Char()
    file_data = fields.Binary(required=True)

    info_json = fields.Json()
    error = fields.Text()

    # simple mode
    line_ids = fields.One2many("geofolia.import.line", "job_id", string="Lines")
    line_count = fields.Integer(compute="_compute_line_count", store=False)

    # full blocks
    product_line_ids = fields.One2many("geofolia.import.product.line", "job_id")
    employee_line_ids = fields.One2many("geofolia.import.employee.line", "job_id")
    partner_line_ids = fields.One2many("geofolia.import.partner.line", "job_id")
    harvested_product_line_ids = fields.One2many(
        "geofolia.import.harvested.product.line", "job_id"
    )
    equipment_line_ids = fields.One2many("geofolia.import.equipment.line", "job_id")
    activity_line_ids = fields.One2many("geofolia.import.activity.line", "job_id")

    @api.depends("line_ids")
    def _compute_line_count(self):
        for job in self:
            job.line_count = len(job.line_ids)

    def action_parse(self):
        for job in self:
            try:
                payload = job._load_json_payload()
                job._parse_payload(payload)
                job.state = "done"
                job.error = False
            except Exception as exc:  # noqa: BLE001
                job.state = "error"
                job.error = str(exc)

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

        if self.import_type == "fields":
            self.line_ids.unlink()
            items = payload.get("Fields")
            if not isinstance(items, list):
                raise UserError(_("Missing or invalid 'Fields' array."))
            self._create_lines_from_fields(items)
            return

        if self.import_type == "products":
            self.line_ids.unlink()
            items = payload.get("Products")
            if not isinstance(items, list):
                raise UserError(_("Missing or invalid 'Products' array."))
            self._create_lines_from_products(items)
            return

        # full
        self._clear_full_lines()
        self._parse_full_payload(payload)

    def _clear_full_lines(self):
        self.product_line_ids.unlink()
        self.employee_line_ids.unlink()
        self.partner_line_ids.unlink()
        self.harvested_product_line_ids.unlink()
        self.equipment_line_ids.unlink()
        self.activity_line_ids.unlink()

    def _parse_full_payload(self, payload):
        self._create_product_lines(payload.get("Products"))
        self._create_employee_lines(payload.get("Employees"))
        self._create_partner_lines(payload.get("Partners"))
        self._create_harvested_product_lines(payload.get("HarvestedProducts"))
        self._create_equipment_lines(payload.get("Equipments"))
        self._create_activity_lines(payload.get("Activities"))

        unsubs = payload.get("IEJsonUnsubscriptionElements")
        if unsubs is not None:
            info = dict(self.info_json or {})
            info["IEJsonUnsubscriptionElements"] = unsubs
            self.info_json = info

    # -------------------------
    # Helpers
    # -------------------------
    def _ensure_list(self, value, key_name):
        if value in (None, False):
            return []
        if not isinstance(value, list):
            raise UserError(_("Invalid '%s' array.") % key_name)
        return value

    def _to_date(self, value):
        if not value:
            return False
        return fields.Date.to_date(value)

    def _to_datetime(self, value):
        if not value:
            return False
        return fields.Datetime.to_datetime(value)

    def _to_float(self, value):
        if value in (None, ""):
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _to_int(self, value):
        if value in (None, ""):
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _json_text(self, obj):
        # siempre serializable a texto para debug/UI
        try:
            return json.dumps(obj, ensure_ascii=False, sort_keys=True)
        except Exception:  # noqa: BLE001
            return "{}"

    # -------------------------
    # Simple mode (tu modelo original)
    # -------------------------
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
                    "harvest_year": self._to_int(it.get("HarvestYear")),
                    "area": self._to_float(it.get("Area")),
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
                    "category_enum": self._to_int(it.get("CategoryEnum")),
                    "product_type_enum": self._to_int(it.get("ProductTypeEnum")),
                    "unit_symbol": it.get("UnitSymbol"),
                    "botanical_species": it.get("BotanicalSpecies"),
                    "variety_name": it.get("VarietyName"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.line"].create(vals_list)

    # -------------------------
    # Full blocks
    # -------------------------
    def _create_product_lines(self, items):
        self.ensure_one()
        items = self._ensure_list(items, "Products")
        if not items:
            return
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            vals_list.append(
                {
                    "job_id": self.id,
                    "farm_identification_code": it.get("FarmIdentificationCode"),
                    "external_id": it.get("SupplyId"),
                    "code": it.get("Code"),
                    "name": it.get("SupplyName"),
                    "category_enum": self._to_int(it.get("CategoryEnum")),
                    "product_type_enum": self._to_int(it.get("ProductTypeEnum")),
                    "unit_symbol": it.get("UnitSymbol"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.product.line"].create(vals_list)

    def _create_employee_lines(self, items):
        self.ensure_one()
        items = self._ensure_list(items, "Employees")
        if not items:
            return
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": it.get("Id") or it.get("EmployeeId"),
                    "code": it.get("Code"),
                    "name": it.get("Name") or it.get("FullName"),
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
        items = self._ensure_list(items, "Partners")
        if not items:
            return
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": it.get("Id") or it.get("PartnerId"),
                    "code": it.get("Code"),
                    "name": it.get("Name"),
                    "vat": it.get("VAT") or it.get("Vat"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.partner.line"].create(vals_list)

    def _create_harvested_product_lines(self, items):
        self.ensure_one()
        items = self._ensure_list(items, "HarvestedProducts")
        if not items:
            return
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": it.get("Id"),
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
        self.ensure_one()
        items = self._ensure_list(items, "Equipments")
        if not items:
            return
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": it.get("Id") or it.get("EquipmentId"),
                    "code": it.get("Code"),
                    "name": it.get("Name"),
                    "category": it.get("Category") or it.get("CategoryName"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.equipment.line"].create(vals_list)

    def _create_activity_lines(self, items):
        """
        En Action.Json las activities vienen con:
        - ActionId
        - StartingDate / EndingDate
        - StartTime / FinishTime
        - OperationName, StatusName/StatusCode, etc.
        """
        self.ensure_one()
        items = self._ensure_list(items, "Activities")
        if not items:
            return
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue

            starting_date = it.get("StartingDate")
            ending_date = it.get("EndingDate")

            vals_list.append(
                {
                    "job_id": self.id,
                    "farm_identification_code": it.get("FarmIdentificationCode"),
                    "external_id": it.get("ActionId") or it.get("Id") or it.get("ActivityId"),
                    "harvest_year": self._to_int(it.get("HarvestYear")),
                    "operation_name": it.get("OperationName"),
                    "operation_category": it.get("OperationCategory"),
                    "status_name": it.get("StatusName"),
                    "status_code": it.get("StatusCode"),
                    "starting_date": self._to_date(starting_date),
                    "ending_date": self._to_date(ending_date),
                    "start_time": it.get("StartTime"),
                    "finish_time": it.get("FinishTime"),
                    "duration_minutes": self._to_int(it.get("Duration")),
                    "last_modification_dt": self._to_datetime(it.get("LastModificationDate")),
                    "comment": it.get("Comment"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.activity.line"].create(vals_list)
