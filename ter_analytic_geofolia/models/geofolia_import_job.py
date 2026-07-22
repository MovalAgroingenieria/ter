# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=too-many-lines,protected-access

import base64
import binascii
import json
import re
import traceback
from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class GeofoliaImportJob(models.Model):  # pylint: disable=R0904
    _name = "geofolia.import.job"
    _description = "Geofolia Import"
    _order = "id desc"

    name = fields.Char(required=True, default=lambda self: self.env._("New"))
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
        selection=[
            ("draft", "To parse"),
            ("done", "Parsed"),
            ("error", "Parse error"),
        ],
        string="Parse",
        default="draft",
        required=True,
    )
    apply_state = fields.Selection(
        selection=[
            ("draft", "To apply"),
            ("ready", "Ready"),
            ("partial", "Partial"),
            ("done", "Applied"),
            ("error", "Error"),
        ],
        string="Apply",
        default="draft",
        required=True,
        index=True,
    )

    file_name = fields.Char()
    file_data = fields.Binary(required=True)

    info_json = fields.Json()
    error = fields.Text()

    line_ids = fields.One2many("geofolia.import.line", "job_id", string="Lines")

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
    timesheet_line_ids = fields.Many2many(
        "account.analytic.line",
        compute="_compute_timesheet_line_ids",
        string="Timesheet lines",
    )
    timesheet_count = fields.Integer(compute="_compute_timesheet_line_ids")
    fsm_order_ids = fields.Many2many(
        "fsm.order",
        compute="_compute_fsm_order_ids",
        string="FSM Orders (from activities)",
    )
    fsm_order_count = fields.Integer(compute="_compute_fsm_order_ids")

    total_count = fields.Integer(compute="_compute_apply_stats")
    pending_count = fields.Integer(compute="_compute_apply_stats")
    processed_count = fields.Integer(compute="_compute_apply_stats")
    error_count = fields.Integer(compute="_compute_apply_stats")

    product_processed_count = fields.Integer(compute="_compute_block_counts")
    product_error_count = fields.Integer(compute="_compute_block_counts")
    partner_processed_count = fields.Integer(compute="_compute_block_counts")
    partner_error_count = fields.Integer(compute="_compute_block_counts")
    employee_processed_count = fields.Integer(compute="_compute_block_counts")
    employee_error_count = fields.Integer(compute="_compute_block_counts")
    harvested_processed_count = fields.Integer(compute="_compute_block_counts")
    harvested_error_count = fields.Integer(compute="_compute_block_counts")
    equipment_processed_count = fields.Integer(compute="_compute_block_counts")
    equipment_error_count = fields.Integer(compute="_compute_block_counts")
    activity_employee_processed_count = fields.Integer(compute="_compute_block_counts")
    activity_employee_error_count = fields.Integer(compute="_compute_block_counts")

    line_count = fields.Integer(
        string="Line count",
        compute="_compute_line_count",
        help="Number of lines (Fields or Products mode).",
    )

    @api.depends("activity_employee_line_ids.analytic_line_id")
    def _compute_timesheet_line_ids(self):
        for record in self:
            lines = record.activity_employee_line_ids.mapped("analytic_line_id")
            record.timesheet_line_ids = lines.filtered(lambda r: r)
            record.timesheet_count = len(record.timesheet_line_ids)

    @api.depends("activity_line_ids.fsm_order_id")
    def _compute_fsm_order_ids(self):
        for record in self:
            orders = record.activity_line_ids.mapped("fsm_order_id")
            record.fsm_order_ids = orders.filtered(lambda r: r)
            record.fsm_order_count = len(record.fsm_order_ids)

    @api.depends(
        "line_ids.sync_state",
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
        for record in self:
            if record.import_type == "full":
                blocks = record._get_full_lines_by_block()
                total = pending = processed = errors = 0
                for lines in blocks.values():
                    total += len(lines)
                    pending += len(
                        lines.filtered(lambda rec: rec.sync_state == "pending")
                    )
                    errors += len(lines.filtered(lambda rec: rec.sync_state == "error"))
                    processed += len(
                        lines.filtered(lambda rec: rec.sync_state in processed_states)
                    )
                record.total_count = total
                record.pending_count = pending
                record.processed_count = processed
                record.error_count = errors
            elif record.import_type == "fields":
                lines = record.line_ids
                record.total_count = len(lines)
                record.pending_count = len(
                    lines.filtered(lambda rec: rec.sync_state == "pending")
                )
                record.error_count = len(
                    lines.filtered(lambda rec: rec.sync_state == "error")
                )
                record.processed_count = len(
                    lines.filtered(lambda rec: rec.sync_state in processed_states)
                )
            else:
                record.total_count = 0
                record.pending_count = 0
                record.processed_count = 0
                record.error_count = 0

    @api.depends(
        "product_line_ids.sync_state",
        "partner_line_ids.sync_state",
        "employee_line_ids.sync_state",
        "harvested_product_line_ids.sync_state",
        "equipment_line_ids.sync_state",
        "activity_employee_line_ids.sync_state",
        "import_type",
    )
    def _compute_block_counts(self):
        processed_states = ("created", "updated", "no_action", "skipped")
        for record in self:
            if record.import_type != "full":
                for attr in (
                    "product_processed_count",
                    "product_error_count",
                    "partner_processed_count",
                    "partner_error_count",
                    "employee_processed_count",
                    "employee_error_count",
                    "harvested_processed_count",
                    "harvested_error_count",
                    "equipment_processed_count",
                    "equipment_error_count",
                    "activity_employee_processed_count",
                    "activity_employee_error_count",
                ):
                    setattr(record, attr, 0)
                continue
            record.product_processed_count = len(
                record.product_line_ids.filtered(
                    lambda rec: rec.sync_state in processed_states
                )
            )
            record.product_error_count = len(
                record.product_line_ids.filtered(lambda rec: rec.sync_state == "error")
            )
            record.partner_processed_count = len(
                record.partner_line_ids.filtered(
                    lambda rec: rec.sync_state in processed_states
                )
            )
            record.partner_error_count = len(
                record.partner_line_ids.filtered(lambda rec: rec.sync_state == "error")
            )
            record.employee_processed_count = len(
                record.employee_line_ids.filtered(
                    lambda rec: rec.sync_state in processed_states
                )
            )
            record.employee_error_count = len(
                record.employee_line_ids.filtered(lambda rec: rec.sync_state == "error")
            )
            record.harvested_processed_count = len(
                record.harvested_product_line_ids.filtered(
                    lambda rec: rec.sync_state in processed_states
                )
            )
            record.harvested_error_count = len(
                record.harvested_product_line_ids.filtered(
                    lambda rec: rec.sync_state == "error"
                )
            )
            record.equipment_processed_count = len(
                record.equipment_line_ids.filtered(
                    lambda rec: rec.sync_state in processed_states
                )
            )
            record.equipment_error_count = len(
                record.equipment_line_ids.filtered(
                    lambda rec: rec.sync_state == "error"
                )
            )
            record.activity_employee_processed_count = len(
                record.activity_employee_line_ids.filtered(
                    lambda rec: rec.sync_state in processed_states
                )
            )
            record.activity_employee_error_count = len(
                record.activity_employee_line_ids.filtered(
                    lambda rec: rec.sync_state == "error"
                )
            )

    @api.depends("line_ids", "import_type")
    def _compute_line_count(self):
        for record in self:
            if record.import_type in ("fields", "products"):
                record.line_count = len(record.line_ids)
            else:
                record.line_count = 0

    def action_parse(self):
        for record in self:
            try:
                payload = record._load_json_payload()
                record._parse_payload(payload)
                record.state = "done"
                if record.import_type == "full":
                    record.apply_state = "ready"
                elif record.import_type == "fields":
                    record.apply_state = "ready"
                else:
                    record.apply_state = "done"
                record.error = False
            except Exception as exc:  # noqa: BLE001  # pylint: disable=W0718
                record.state = "error"
                record.apply_state = "error"
                record.error = record._format_exception(exc)

    def action_apply(self):
        for record in self:
            if record.import_type == "full":
                record._apply_full_export(only_pending=False)
                record._recompute_apply_state()
            elif record.import_type == "fields":
                record.action_apply_fields()

    def action_apply_pending(self):
        for record in self:
            if record.import_type != "full":
                continue
            record._apply_full_export(only_pending=True)
            record._recompute_apply_state()

    def action_reprocess(self):
        """Re-run apply on pending, error and skipped lines.
        Existing records are updated, not duplicated."""
        for record in self:
            if record.import_type == "full":
                record._apply_full_export(only_pending=True)
                record._recompute_apply_state()
            elif record.import_type == "fields":
                for line in record.line_ids.filtered(
                    lambda rec: rec.sync_state in ("pending", "error")
                ):
                    record._apply_field_line(line)
                record._recompute_apply_state_fields()

    def action_apply_fields(self):
        """Apply field lines: create/update fsm.location and ter.use_unit (1:1)."""
        for record in self:
            if record.import_type != "fields":
                continue
            for line in record.line_ids.filtered(
                lambda rec: rec.sync_state in ("pending", "error")
            ):
                record._apply_field_line(line)
            record._recompute_apply_state_fields()

    def action_view_created_lines(self):
        """Open lines with sync_state in (created, updated). Only for fields mode."""
        self.ensure_one()
        if self.import_type != "fields":
            return False
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Created / Updated"),
            "res_model": "geofolia.import.line",
            "view_mode": "list,form",
            "domain": [
                ("job_id", "=", self.id),
                ("sync_state", "in", ("created", "updated")),
            ],
            "context": {"default_job_id": self.id},
        }

    def action_view_error_lines(self):
        """Open lines with sync_state == error. Only for fields mode."""
        self.ensure_one()
        if self.import_type != "fields":
            return False
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Lines with error"),
            "res_model": "geofolia.import.line",
            "view_mode": "list,form",
            "domain": [("job_id", "=", self.id), ("sync_state", "=", "error")],
            "context": {"default_job_id": self.id},
        }

    def _action_view_block_lines(self, res_model, created=True):
        """Open list of job lines (full mode block) filtered by processed/error."""
        self.ensure_one()
        processed_states = ("created", "updated", "no_action", "skipped")
        name = self.env._("Processed") if created else self.env._("Errors")
        domain = [("job_id", "=", self.id)]
        if created:
            domain.append(("sync_state", "in", processed_states))
        else:
            domain.append(("sync_state", "=", "error"))
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": res_model,
            "view_mode": "list,form",
            "domain": domain,
            "context": {"default_job_id": self.id},
        }

    def action_view_created_product_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.product.line", created=True
        )

    def action_view_error_product_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.product.line", created=False
        )

    def action_view_created_partner_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.partner.line", created=True
        )

    def action_view_error_partner_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.partner.line", created=False
        )

    def action_view_created_employee_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.employee.line", created=True
        )

    def action_view_error_employee_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.employee.line", created=False
        )

    def action_view_created_harvested_product_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.harvested.product.line", created=True
        )

    def action_view_error_harvested_product_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.harvested.product.line", created=False
        )

    def action_view_created_equipment_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.equipment.line", created=True
        )

    def action_view_error_equipment_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.equipment.line", created=False
        )

    def action_view_created_activity_employee_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.activity.employee.line", created=True
        )

    def action_view_error_activity_employee_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return self._action_view_block_lines(
            "geofolia.import.activity.employee.line", created=False
        )

    def action_view_timesheet_lines(self):
        self.ensure_one()
        if self.import_type != "full" or not self.timesheet_line_ids:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Timesheet lines"),
            "res_model": "account.analytic.line",
            "view_mode": "list,form",
            "domain": [("id", "in", self.timesheet_line_ids.ids)],
        }

    def action_view_fsm_orders(self):
        """Open FSM orders created from Geofolia activities (OCA field-service)."""
        self.ensure_one()
        if self.import_type != "full" or not self.fsm_order_ids:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("FSM Orders (Activities)"),
            "res_model": "fsm.order",
            "view_mode": "list,form",
            "domain": [("id", "in", self.fsm_order_ids.ids)],
        }

    def action_view_partner_lines(self):
        """Open all partner lines of this job."""
        self.ensure_one()
        if self.import_type != "full":
            return False
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Partners"),
            "res_model": "geofolia.import.partner.line",
            "view_mode": "list,form",
            "domain": [("job_id", "=", self.id)],
            "context": {"default_job_id": self.id},
        }

    def action_view_activity_lines(self):
        self.ensure_one()
        if self.import_type != "full":
            return False
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Activities"),
            "res_model": "geofolia.import.activity.line",
            "view_mode": "list,form",
            "domain": [("job_id", "=", self.id)],
            "context": {"default_job_id": self.id},
        }

    def _load_json_payload(self):
        self.ensure_one()
        if not self.file_data:
            raise UserError(self.env._("No file provided."))

        try:
            raw = base64.b64decode(self.file_data)
        except (binascii.Error, ValueError) as exc:
            raise UserError(
                self.env._("Invalid file content: %(error)s", error=str(exc))
            ) from exc

        last_exc = None
        for encoding in ("utf-8-sig", "utf-8"):
            try:
                return json.loads(raw.decode(encoding))
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                last_exc = exc

        raise UserError(
            self.env._("Invalid JSON file: %(error)s", error=str(last_exc))
        ) from last_exc

    def _parse_payload(self, payload):
        self.ensure_one()
        if not isinstance(payload, dict):
            raise UserError(self.env._("JSON root must be an object."))

        info = payload.get("Information")
        if not isinstance(info, dict):
            raise UserError(self.env._("Missing or invalid 'Information' object."))
        self.info_json = info

        self._clear_lines()

        if self.import_type == "fields":
            items = payload.get("Fields")
            if not isinstance(items, list):
                raise UserError(self.env._("Missing or invalid 'Fields' array."))
            self._create_lines_from_fields(items)
            return

        if self.import_type == "products":
            items = payload.get("Products")
            if not isinstance(items, list):
                raise UserError(self.env._("Missing or invalid 'Products' array."))
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
        employees = self._normalize_items_list(
            payload.get("Employees"), dict_keys_ok=True
        )
        partners = payload.get("Partners") or []
        harvested = self._normalize_items_list(
            payload.get("HarvestedProducts"), dict_keys_ok=True
        )
        equipments = self._normalize_items_list(
            payload.get("Equipments"), dict_keys_ok=True
        )
        activities = payload.get("Activities") or []

        if isinstance(products, list):
            self._create_product_lines(products)
        if employees:
            self._create_employee_lines(employees)
        if isinstance(partners, list):
            self._create_partner_lines(partners)
        if harvested:
            self._create_harvested_product_lines(harvested)
        if equipments:
            self._create_equipment_lines(equipments)
        if isinstance(activities, list):
            self._create_activity_lines(activities)

    def _normalize_items_list(self, items, dict_keys_ok=False):
        """Convert Employees/HarvestedProducts/Equipments to list of dicts.
        Handles: dict (use values), list (filter to dicts only), list of strings.
        """
        if not items:
            return []
        if isinstance(items, dict):
            items = list(items.values()) if dict_keys_ok else []
        if not isinstance(items, list):
            return []
        result = []
        for it in items:
            if isinstance(it, dict):
                result.append(it)
            elif isinstance(it, str):
                result.append({"Id": it, "Name": it})
        return result

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
        except (TypeError, ValueError, OverflowError):
            return str(value)

    def _format_exception(self, exc):
        """Return exception message with traceback for debugging."""
        msg = str(exc)
        tb = traceback.format_exc()
        if tb and tb.strip() != msg:
            return f"{msg}\n\n{tb}"
        return msg

    def _write_line_error_state(self, line, exc):
        """Write error state to line.
        On failure (e.g. aborted transaction), rollback and re-raise."""
        try:
            line.write(
                {"sync_state": "error", "sync_message": self._format_exception(exc)}
            )
        except Exception:  # noqa: BLE001  # pylint: disable=W0718
            self.env.cr.rollback()
            raise exc from None

    @staticmethod
    def _parse_date(val):
        """Parse an ISO datetime string to a date object.

        Accepts 'YYYY-MM-DDThh:mm:ss' or 'YYYY-MM-DD'. Returns False if
        val is None or unparseable.
        """
        if not val or not isinstance(val, str):
            return False
        try:
            return fields.Date.from_string(val[:10])
        except (ValueError, IndexError):
            return False

    def _safe_scalar_str(self, val):
        """Coerce value to string for product/partner fields. Avoids tuples/lists
        that cause 'dictionary update sequence element #0 has length 1' errors."""
        if val is None or val is False:
            return False
        if isinstance(val, str):
            return val.strip() or False
        if isinstance(val, (list, tuple)):
            if not val:
                return False
            return self._safe_scalar_str(val[0])
        if isinstance(val, dict):
            return str(val)
        return str(val)

    def _sanitize_create_vals(self, vals):
        """Ensure scalar values in vals are safe for Model.create (no tuples/lists
        that cause 'dictionary update sequence element #0 has length 1' errors).
        Preserves Odoo command lists (e.g. [(6,0,ids)]) for relational fields."""
        if not isinstance(vals, dict):
            return vals
        result = {}
        for k, v in vals.items():
            if isinstance(v, (list, tuple)):
                if v and isinstance(v[0], (list, tuple)) and len(v[0]) >= 2:
                    result[k] = v
                else:
                    result[k] = self._safe_scalar_str(v) if v else False
            elif isinstance(v, dict):
                result[k] = str(v) if v else False
            elif (
                v is not None
                and v is not False
                and not isinstance(v, (str, int, float, bool))
            ):
                result[k] = str(v)
            else:
                result[k] = v
        return result

    def _create_lines_from_fields(self, items):
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_uuid": it.get("Id"),
                    "farm_identification_code": it.get("FarmIdentificationCode"),
                    "code": it.get("Code"),
                    "name": it.get("Name"),
                    "harvest_year": it.get("HarvestYear"),
                    "sowing_date": self._parse_date(it.get("SowingDate")),
                    "harvest_date": self._parse_date(it.get("HarvestDate")),
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

    def _create_product_lines(self, items):
        vals_list = []
        for it in items:
            if not isinstance(it, dict):
                continue
            supply_id = it.get("SupplyId")
            farm_code = it.get("FarmIdentificationCode") or ""
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": supply_id,
                    "farm_identification_code": farm_code,
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
        if isinstance(items, dict):
            items = list(items.values())
        if not isinstance(items, (list, tuple)):
            return
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
        if isinstance(items, dict):
            items = list(items.values())
        if not isinstance(items, (list, tuple)):
            return
        for it in items:
            if not isinstance(it, dict):
                continue
            ext_id = it.get("HarvestId") or it.get("HarvestedProductId") or it.get("Id")
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
        if isinstance(items, dict):
            items = list(items.values())
        if not isinstance(items, (list, tuple)):
            return
        for it in items:
            if not isinstance(it, dict):
                continue
            ext_id = it.get("EquipmentId") or it.get("Id")
            farm_code = it.get("FarmIdentificationCode") or ""
            vals_list.append(
                {
                    "job_id": self.id,
                    "external_id": ext_id,
                    "farm_identification_code": farm_code,
                    "code": it.get("Code"),
                    "name": (it.get("Name") or it.get("EquipmentName")),
                    "category": it.get("Category"),
                    "raw_json": it,
                    "raw_json_text": self._json_text(it),
                }
            )
        if vals_list:
            self.env["geofolia.import.equipment.line"].create(vals_list)

    def _create_activity_lines(self, items):
        activity_line_obj = self.env["geofolia.import.activity.line"]
        emp_line_obj = self.env["geofolia.import.activity.employee.line"]

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

        activities = (
            activity_line_obj.create(act_vals) if act_vals else activity_line_obj
        )
        by_external = {a.external_id: a for a in activities}

        for it in items:
            if not isinstance(it, dict):
                continue
            action_id = it.get("ActionId") or it.get("Id")
            activity = by_external.get(action_id)
            if not activity:
                continue

            employees = self._normalize_items_list(
                it.get("ActionEmployees"), dict_keys_ok=True
            )
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
            emp_line_obj.create(emp_vals)

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
            return
        blocks = self._get_full_lines_by_block()
        total = sum(len(v) for v in blocks.values())
        if not total:
            self.apply_state = "done"
            return
        has_pending = any(
            v.filtered(lambda rec: rec.sync_state == "pending") for v in blocks.values()
        )
        has_error = any(
            v.filtered(lambda rec: rec.sync_state == "error") for v in blocks.values()
        )
        if has_error:
            self.apply_state = "partial" if has_pending else "error"
            return
        self.apply_state = "ready" if has_pending else "done"

    def _recompute_apply_state_fields(self):
        self.ensure_one()
        if self.import_type != "fields":
            return
        lines = self.line_ids
        if not lines:
            self.apply_state = "done"
            return
        has_pending = lines.filtered(lambda rec: rec.sync_state == "pending")
        has_error = lines.filtered(lambda rec: rec.sync_state == "error")
        if has_error:
            self.apply_state = "partial" if has_pending else "error"
            return
        self.apply_state = "ready" if has_pending else "done"

    def _field_line_find_campaign(self, date_start, date_end, harvest_year, default):
        """Return the date.range (campaign) that best fits the field.

        Priority: a range that contains the explicit sowing/harvest dates →
        a range covering the harvest year → the configured default range.
        """
        dr_obj = self.env["date.range"]
        base_domain = [("is_unit_use_type", "=", True)]
        if date_start and date_end:
            campaign = dr_obj.search(
                base_domain
                + [
                    ("date_start", "<=", date_start),
                    ("date_end", ">=", date_end),
                ],
                limit=1,
            )
            if campaign:
                return campaign
        if harvest_year:
            midyear = fields.Date.from_string(f"{harvest_year}-06-30")
            campaign = dr_obj.search(
                base_domain
                + [
                    ("date_start", "<=", midyear),
                    ("date_end", ">=", midyear),
                ],
                limit=1,
            )
            if campaign:
                return campaign
        return default or dr_obj.browse()

    def _field_line_resolve_dates(self, line, default_date_range):
        """Return (date_range, date_start, date_end) for a field line.

        Fills missing SowingDate/HarvestDate from the resolved campaign
        (start/end), clamps the dates inside the campaign and guarantees
        date_start <= date_end so ter.use_unit constraints always hold.
        """
        date_start = line.sowing_date or False
        date_end = line.harvest_date or False
        harvest_year = line.harvest_year
        campaign = self._field_line_find_campaign(
            date_start, date_end, harvest_year, default_date_range
        )
        if campaign:
            if not date_start:
                date_start = campaign.date_start
            if not date_end:
                date_end = campaign.date_end
            if campaign.date_start and date_start < campaign.date_start:
                date_start = campaign.date_start
            if campaign.date_end and date_end > campaign.date_end:
                date_end = campaign.date_end
        else:
            if not date_start and harvest_year:
                date_start = fields.Date.from_string(f"{harvest_year}-01-01")
            if not date_end and harvest_year:
                date_end = fields.Date.from_string(f"{harvest_year}-12-31")
        if date_start and date_end and date_start > date_end:
            if campaign:
                date_start = campaign.date_start
                date_end = campaign.date_end
            else:
                date_start = date_end
        return campaign, date_start, date_end

    def _geofolia_city_number(self, line):
        """Return the Geofolia CityNumber (cadastral code) for a field line."""
        raw = line.raw_json or {}
        city_number = str(raw.get("CityNumber") or "").strip()
        if city_number.isdigit() and len(city_number) >= 3:
            return city_number
        return ""

    def _create_geofolia_municipality(self, line):
        """Create a res.municipality from the Geofolia CityNumber.

        CityNumber is the cadastral code: 2-digit province cadastral code
        plus the 3-digit municipality number. Returns an empty recordset
        when the province cannot be resolved or the city has no CityNumber.
        """
        muni_obj = self.env["res.municipality"]
        city = (line.city or "").strip()
        city_number = self._geofolia_city_number(line)
        if not city or not city_number:
            return muni_obj.browse()
        province = self.env["res.province"].search(
            [("cadastral_code", "=", int(city_number[:2]))], limit=1
        )
        municipality_number = int(city_number[2:])
        if not province or municipality_number <= 0:
            return muni_obj.browse()
        return muni_obj.create(
            {
                "alphanum_code": city,
                "province_id": province.id,
                "municipality_number": municipality_number,
            }
        )

    def _resolve_geofolia_municipality(self, line):
        """Resolve the municipality for a field.

        Priority: existing municipality by CityNumber (cadastral code) →
        by city name → create it from the CityNumber → configured default.
        """
        muni_obj = self.env["res.municipality"]
        city_number = self._geofolia_city_number(line)
        if city_number:
            municipality = muni_obj.search(
                [("cadastral_code", "=", city_number)], limit=1
            )
            if municipality:
                return municipality
        city = (line.city or "").strip()
        if city:
            municipality = muni_obj.search([("alphanum_code", "=ilike", city)], limit=1)
            if municipality:
                return municipality
        municipality = self._create_geofolia_municipality(line)
        if municipality:
            return municipality
        return self.env.company.geofolia_default_municipality_id

    def _build_geofolia_parcel_code(self, line):
        """Return a unique parcel code (<=20 chars) for an auto-created parcel."""
        parcel_obj = self.env["ter.parcel"]
        year = str(line.harvest_year or "")[-2:] or "00"
        base = f"GF{year}-"
        seq = parcel_obj.search_count([("alphanum_code", "=like", f"{base}%")]) + 1
        code = f"{base}{seq:05d}"
        while parcel_obj.search_count([("alphanum_code", "=", code)]):
            seq += 1
            code = f"{base}{seq:05d}"
        return code[:20]

    def _create_geofolia_field_parcel(self, line, geom_ewkt):
        """Create a ter.parcel for a Geofolia field.

        Uses the field geometry when provided (stored in the GIS parcel
        table). Raises a descriptive UserError when the municipality cannot
        be resolved.
        """
        municipality = self._resolve_geofolia_municipality(line)
        if not municipality:
            raise UserError(
                self.env._(
                    "Cannot create a parcel for Geofolia field "
                    "%(field)s: municipality %(city)s (code %(code)s) could "
                    "not be found or created. Set a default municipality in "
                    "the Geofolia settings.",
                    field=line.name or line.code or line.external_uuid or "",
                    city=line.city or "-",
                    code=self._geofolia_city_number(line) or "-",
                )
            )
        parcel = self.env["ter.parcel"].create(
            {
                "alphanum_code": self._build_geofolia_parcel_code(line),
                "municipality_id": municipality.id,
                "area_official": 0,
                "geofolia_created": True,
            }
        )
        if geom_ewkt:
            parcel._set_gis_geometry(geom_ewkt)
        return parcel

    def _field_line_resolve_parcel(self, line, default_parcel, existing_unit=None):
        """Return (parcel, geom_ewkt) for a field line, creating a parcel if needed.

        Re-import (the Geofolia id already has a use unit): keep the parcel
        already linked to that unit untouched, and only set its geometry when
        the parcel has none and the field now brings one.

        First import:
        - Geometry present and it overlaps an existing GIS parcel → reuse it.
        - Geometry present but no overlap → create a parcel with that geometry.
        - No geometry → use the configured default parcel, otherwise create a
          parcel without geometry so the record is still imported.
        """
        ter_unit_obj = self.env["ter.use_unit"]
        geom_ewkt = (line.geography_wkt or "").strip() or False
        if existing_unit and existing_unit.parcel_id:
            parcel = existing_unit.parcel_id
            if geom_ewkt and not parcel.mapped_to_polygon:
                parcel._set_gis_geometry(geom_ewkt)
            return parcel, geom_ewkt
        if geom_ewkt:
            temp_unit = ter_unit_obj.new({})
            parcel = temp_unit._get_parcel_from_geometry(geom_ewkt)
            if parcel:
                return parcel, geom_ewkt
            parcel = self._create_geofolia_field_parcel(line, geom_ewkt)
            return parcel, geom_ewkt
        if default_parcel:
            return default_parcel, False
        parcel = self._create_geofolia_field_parcel(line, False)
        return parcel, False

    def _field_line_write_parcel_error(self, line):
        line.write(
            {
                "sync_state": "error",
                "sync_message": self.env._(
                    "Could not determine or create a parcel for this field "
                    "(no geometry match and no municipality to create one)."
                ),
            }
        )

    def _field_line_write_daterange_error(self, line):
        line.write(
            {
                "sync_state": "error",
                "sync_message": self.env._(
                    "No campaign (date range) could be resolved. Set the "
                    "harvest year in the data, create a matching date range, "
                    "or configure a Geofolia default date range."
                ),
            }
        )

    def _field_line_apply_existing_location(
        self, location, line, ctx
    ):  # pylint: disable=too-many-branches
        """Update or create ter.use_unit for an existing fsm.location."""
        ter_unit_obj = self.env["ter.use_unit"]
        loc_name = ctx["loc_name"]
        if not location.ter_use_unit_id.geofolia_external_id and ctx.get("ext_id"):
            location.ter_use_unit_id.sudo().write(
                {"geofolia_external_id": ctx["ext_id"]}
            )
        location.partner_id.write({"name": loc_name, "city": line.city or False})
        unit = location.ter_use_unit_id
        if unit:
            unit_vals = {
                "area_official": ctx["area_official"],
                "name": loc_name,
                "geofolia_code": ctx.get("geofolia_code"),
                "geofolia_harvest_year": ctx.get("geofolia_harvest_year"),
                "geofolia_crop_name": ctx.get("geofolia_crop_name"),
                "geofolia_city": ctx.get("geofolia_city"),
            }
            if ctx.get("geom_ewkt"):
                unit_vals["geom_ewkt"] = ctx["geom_ewkt"]
            if ctx.get("date_start"):
                unit_vals["date_start"] = ctx["date_start"]
            if ctx.get("date_end"):
                unit_vals["date_end"] = ctx["date_end"]
            if ctx.get("date_range"):
                unit_vals["date_range_id"] = ctx["date_range"].id
            unit.write(unit_vals)
            line.write(
                {
                    "fsm_location_id": location.id,
                    "ter_use_unit_id": unit.id,
                    "sync_state": "updated",
                    "sync_message": self.env._("Updated location and use unit."),
                }
            )
            return
        parcel = ctx.get("parcel")
        date_range = ctx.get("date_range")
        if not parcel or not date_range:
            line.write(
                {
                    "sync_state": "error",
                    "sync_message": self.env._(
                        "Existing location but cannot create "
                        "ter.use_unit (parcel/date range missing)."
                    ),
                }
            )
            return
        ext_id = ctx.get("ext_id")
        unit = ter_unit_obj.search([("geofolia_external_id", "=", ext_id)], limit=1)
        if not unit:
            unit_vals = {
                "parcel_id": parcel.id,
                "date_range_id": date_range.id,
                "date_start": ctx["date_start"],
                "date_end": ctx["date_end"],
                "area_official": ctx["area_official"],
                "name": loc_name,
                "geofolia_external_id": ext_id,
                "fsm_location_id": location.id,
                "geofolia_code": ctx.get("geofolia_code"),
                "geofolia_harvest_year": ctx.get("geofolia_harvest_year"),
                "geofolia_crop_name": ctx.get("geofolia_crop_name"),
                "geofolia_city": ctx.get("geofolia_city"),
            }
            if ctx.get("geom_ewkt"):
                unit_vals["geom_ewkt"] = ctx["geom_ewkt"]
            unit = ter_unit_obj.create(unit_vals)
        else:
            unit_vals = {
                "fsm_location_id": location.id,
                "area_official": ctx["area_official"],
                "name": loc_name,
                "geofolia_code": ctx.get("geofolia_code"),
                "geofolia_harvest_year": ctx.get("geofolia_harvest_year"),
                "geofolia_crop_name": ctx.get("geofolia_crop_name"),
                "geofolia_city": ctx.get("geofolia_city"),
            }
            if ctx.get("geom_ewkt"):
                unit_vals["geom_ewkt"] = ctx["geom_ewkt"]
            if ctx.get("date_start"):
                unit_vals["date_start"] = ctx["date_start"]
            if ctx.get("date_end"):
                unit_vals["date_end"] = ctx["date_end"]
            if date_range:
                unit_vals["date_range_id"] = date_range.id
            if parcel:
                unit_vals["parcel_id"] = parcel.id
            unit.write(unit_vals)
        location.ter_use_unit_id = unit.id
        line.write(
            {
                "fsm_location_id": location.id,
                "ter_use_unit_id": unit.id,
                "sync_state": "created",
                "sync_message": self.env._("Created use unit and linked to location."),
            }
        )

    def _field_line_apply_new_location(self, line, ctx):
        """Create ter.use_unit first, then fsm.location (ter_use_unit_id required)."""
        fsm_loc_obj = self.env["fsm.location"]
        ter_unit_obj = self.env["ter.use_unit"]
        partner_obj = self.env["res.partner"]
        loc_name = ctx["loc_name"]
        parcel = ctx.get("parcel")
        date_range = ctx.get("date_range")
        if not parcel or not date_range:
            line.write(
                {
                    "sync_state": "error",
                    "sync_message": self.env._(
                        "Cannot create location: parcel/date range required "
                        "for ter.use_unit."
                    ),
                }
            )
            return
        ext_id = ctx["ext_id"]
        unit = ter_unit_obj.search([("geofolia_external_id", "=", ext_id)], limit=1)
        if not unit:
            unit_vals = {
                "parcel_id": parcel.id,
                "date_range_id": date_range.id,
                "date_start": ctx["date_start"],
                "date_end": ctx["date_end"],
                "area_official": ctx["area_official"],
                "name": loc_name,
                "geofolia_external_id": ext_id,
                "geofolia_code": ctx.get("geofolia_code"),
                "geofolia_harvest_year": ctx.get("geofolia_harvest_year"),
                "geofolia_crop_name": ctx.get("geofolia_crop_name"),
                "geofolia_city": ctx.get("geofolia_city"),
            }
            if ctx.get("geom_ewkt"):
                unit_vals["geom_ewkt"] = ctx["geom_ewkt"]
            unit = ter_unit_obj.create(unit_vals)
        else:
            unit_vals = {
                "parcel_id": parcel.id,
                "date_range_id": date_range.id,
                "date_start": ctx["date_start"],
                "date_end": ctx["date_end"],
                "area_official": ctx["area_official"],
                "name": loc_name,
                "geofolia_code": ctx.get("geofolia_code"),
                "geofolia_harvest_year": ctx.get("geofolia_harvest_year"),
                "geofolia_crop_name": ctx.get("geofolia_crop_name"),
                "geofolia_city": ctx.get("geofolia_city"),
            }
            if ctx.get("geom_ewkt"):
                unit_vals["geom_ewkt"] = ctx["geom_ewkt"]
            unit.write(unit_vals)
        partner = partner_obj.create(
            {"name": loc_name, "city": line.city or False, "is_company": False}
        )
        location = fsm_loc_obj.create(
            {
                "partner_id": partner.id,
                "owner_id": partner.id,
                "ter_use_unit_id": unit.id,
            }
        )
        unit.write({"fsm_location_id": location.id})
        line.write(
            {
                "fsm_location_id": location.id,
                "ter_use_unit_id": unit.id,
                "sync_state": "created",
                "sync_message": self.env._("Created location and use unit (1:1)."),
            }
        )

    def _build_field_line_ctx(self, line, ext_id, existing_unit=None):
        """Build context dict for field line processing."""
        company = self.env.company
        default_parcel = company.geofolia_default_parcel_id
        default_date_range = company.geofolia_default_date_range_id
        date_range, date_start, date_end = self._field_line_resolve_dates(
            line, default_date_range
        )
        parcel, geom_ewkt = self._field_line_resolve_parcel(
            line, default_parcel, existing_unit
        )
        area_official = float(line.area or 0)
        loc_name = (
            line.name
            or line.code
            or self.env._("Geofolia Field %(ext_id)s", ext_id=ext_id)
        )
        return {
            "parcel": parcel,
            "date_range": date_range,
            "date_start": date_start,
            "date_end": date_end,
            "geom_ewkt": geom_ewkt,
            "area_official": area_official,
            "loc_name": loc_name,
            "ext_id": ext_id,
            "geofolia_code": line.code or False,
            "geofolia_harvest_year": line.harvest_year or False,
            "geofolia_crop_name": line.crop_name or False,
            "geofolia_city": line.city or False,
        }

    def _apply_field_line(self, line):
        """Create or update fsm.location and ter.use_unit (1:1) from Field line."""
        self.ensure_one()
        fsm_loc_obj = self.env["fsm.location"]
        ter_unit_obj = self.env["ter.use_unit"]
        ext_id = (line.external_uuid or "").strip() or False
        if not ext_id:
            line.write(
                {
                    "sync_state": "skipped",
                    "sync_message": self.env._("Missing Geofolia ID."),
                }
            )
            return
        try:
            with self.env.cr.savepoint():
                unit = ter_unit_obj.search(
                    [("geofolia_external_id", "=", ext_id)], limit=1
                )
                location = unit.fsm_location_id if unit else fsm_loc_obj.browse()
                loc_name = (
                    line.name
                    or line.code
                    or self.env._("Geofolia Field %(ext_id)s", ext_id=ext_id)
                )
                if not unit and not location:
                    candidates = fsm_loc_obj.search(
                        [
                            ("geofolia_external_id", "=", False),
                            ("partner_id.name", "=", loc_name),
                            ("ter_use_unit_id", "!=", False),
                        ],
                        limit=2,
                    )
                    if len(candidates) == 1:
                        location = candidates
                        unit = candidates.ter_use_unit_id
                        unit.sudo().write({"geofolia_external_id": ext_id})
                ctx = self._build_field_line_ctx(line, ext_id, unit)
                if not ctx.get("parcel") and not location:
                    self._field_line_write_parcel_error(line)
                    return
                if not ctx.get("date_range") and not location:
                    self._field_line_write_daterange_error(line)
                    return
                if location:
                    self._field_line_apply_existing_location(location, line, ctx)
                else:
                    self._field_line_apply_new_location(line, ctx)
        except UserError as exc:
            line.write({"sync_state": "error", "sync_message": str(exc)})
        except Exception as exc:  # noqa: BLE001  # pylint: disable=W0718
            self._write_line_error_state(line, exc)

    def _apply_full_export(self, only_pending=False):
        self.ensure_one()

        def _todo(rs):
            if only_pending:
                return rs.filtered(
                    lambda rec: rec.sync_state in ("pending", "error", "skipped")
                )
            return rs.filtered(lambda rec: rec.sync_state in ("pending", "error"))

        for line in _todo(self.product_line_ids):
            self._apply_product_line(line)
        for line in _todo(self.partner_line_ids):
            self._apply_partner_line(line)
        for line in _todo(self.employee_line_ids):
            self._apply_employee_line(line)
        for line in _todo(self.harvested_product_line_ids):
            self._apply_product_like(line, label="harvested_products")
        for line in _todo(self.equipment_line_ids):
            self._apply_equipment_line(line)
        for line in _todo(self.activity_employee_line_ids):
            self._apply_activity_employee_line(line)
        self._recompute_activity_line_sync_state()

    def _recompute_activity_line_sync_state(self):
        """Update activity line sync_state from its activity employee lines."""
        for activity in self.activity_line_ids:
            children = activity.employee_line_ids
            if not children:
                continue
            if any(c.sync_state == "error" for c in children):
                activity.sync_state = "error"
            elif any(c.sync_state == "pending" for c in children):
                activity.sync_state = "pending"
            elif all(c.sync_state == "skipped" for c in children):
                activity.sync_state = "skipped"
            else:
                activity.sync_state = "no_action"

    def _apply_product_line(self, line):
        product_obj = self.env["product.product"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write(
                        {
                            "sync_state": "skipped",
                            "sync_message": self.env._("Missing id."),
                        }
                    )
                    return
                product = product_obj.search(
                    [("geofolia_external_id", "=", line.external_id)], limit=1
                )
                vals = {
                    "name": line.name or line.code or self.env._("Geofolia product"),
                    "default_code": line.code,
                    "geofolia_external_id": line.external_id,
                }
                if product:
                    changed = any(
                        vals.get(k) and product[k] != vals[k]
                        for k in ("name", "default_code")
                    )
                    if changed:
                        product.write(vals)
                        line.write(
                            {
                                "product_id": product.id,
                                "sync_state": "updated",
                                "sync_message": self.env._("Updated product."),
                            }
                        )
                    else:
                        line.write(
                            {
                                "product_id": product.id,
                                "sync_state": "no_action",
                                "sync_message": self.env._("Already up to date."),
                            }
                        )
                    return
                product = product_obj.create(self._sanitize_create_vals(vals))
                line.write(
                    {
                        "product_id": product.id,
                        "sync_state": "created",
                        "sync_message": self.env._("Created product."),
                    }
                )
        except Exception as exc:  # noqa: BLE001  # pylint: disable=W0718
            self._write_line_error_state(line, exc)

    def _apply_partner_line(self, line):
        """Create or update res.partner from partner line."""
        partner_obj = self.env["res.partner"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write(
                        {
                            "sync_state": "skipped",
                            "sync_message": self.env._("Missing id."),
                        }
                    )
                    return
                partner = partner_obj.search(
                    [("geofolia_external_id", "=", line.external_id)], limit=1
                )
                vals = {
                    "name": line.name or line.code or self.env._("Geofolia partner"),
                    "vat": line.vat or False,
                    "geofolia_external_id": line.external_id,
                }
                if partner:
                    changed = any(
                        vals.get(k) is not None and partner[k] != vals[k]
                        for k in ("name", "vat")
                    )
                    if changed:
                        partner.write(vals)
                        line.write(
                            {
                                "partner_id": partner.id,
                                "sync_state": "updated",
                                "sync_message": self.env._("Updated partner."),
                            }
                        )
                    else:
                        line.write(
                            {
                                "partner_id": partner.id,
                                "sync_state": "no_action",
                                "sync_message": self.env._("Already up to date."),
                            }
                        )
                    return
                partner = partner_obj.create(vals)
                line.write(
                    {
                        "partner_id": partner.id,
                        "sync_state": "created",
                        "sync_message": self.env._("Created partner."),
                    }
                )
        except Exception as exc:  # noqa: BLE001  # pylint: disable=W0718
            self._write_line_error_state(line, exc)

    def _apply_employee_line(self, line):
        """Create or update fsm.person (Field Service worker) from employee line."""
        person_obj = self.env["fsm.person"]
        partner_obj = self.env["res.partner"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write(
                        {
                            "sync_state": "skipped",
                            "sync_message": self.env._("Missing id."),
                        }
                    )
                    return
                person = person_obj.search(
                    [("geofolia_external_id", "=", line.external_id)], limit=1
                )
                name = (
                    line.name
                    or line.code
                    or self.env._(
                        "Geofolia worker %(ext_id)s",
                        ext_id=line.external_id,
                    )
                )
                if person:
                    partner_vals = {"name": name}
                    if line.email:
                        partner_vals["email"] = line.email
                    if line.phone:
                        partner_vals["phone"] = line.phone
                    person.partner_id.write(
                        {k: v for k, v in partner_vals.items() if v}
                    )
                    if not person.geofolia_external_id:
                        person.sudo().write({"geofolia_external_id": line.external_id})
                    line.write(
                        {
                            "person_id": person.id,
                            "sync_state": "updated",
                            "sync_message": self.env._("Updated field service person."),
                        }
                    )
                    return
                partner = partner_obj.create(
                    {
                        "name": name,
                        "email": line.email,
                        "phone": line.phone,
                        "is_company": False,
                    }
                )
                person_vals = {
                    "partner_id": partner.id,
                    "geofolia_external_id": line.external_id,
                }
                person = person_obj.create(person_vals)
                if not person.geofolia_external_id:
                    person.sudo().write({"geofolia_external_id": line.external_id})
                line.write(
                    {
                        "person_id": person.id,
                        "sync_state": "created",
                        "sync_message": self.env._("Created field service person."),
                    }
                )
        except Exception as exc:  # noqa: BLE001  # pylint: disable=W0718
            self._write_line_error_state(line, exc)

    def _apply_equipment_line(self, line):
        """Create or update fsm.equipment from equipment line (not product.product)."""
        equipment_obj = self.env["fsm.equipment"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    line.write(
                        {
                            "sync_state": "skipped",
                            "sync_message": self.env._("Missing id."),
                        }
                    )
                    return
                equipment = equipment_obj.search(
                    [("geofolia_external_id", "=", line.external_id)], limit=1
                )
                name = (
                    line.name
                    or line.code
                    or self.env._(
                        "Geofolia Equipment %(ext_id)s",
                        ext_id=line.external_id or "",
                    )
                )
                vals = self._sanitize_create_vals(
                    {
                        "name": self._safe_scalar_str(name)
                        or str(line.external_id or ""),
                        "geofolia_external_id": self._safe_scalar_str(line.external_id)
                        or str(line.external_id),
                    }
                )
                if equipment:
                    equipment.write({k: v for k, v in vals.items() if v})
                    line.write(
                        {
                            "equipment_id": equipment.id,
                            "sync_state": "updated",
                            "sync_message": self.env._("Updated equipment."),
                        }
                    )
                    return
                equipment = equipment_obj.create(vals)
                line.write(
                    {
                        "equipment_id": equipment.id,
                        "sync_state": "created",
                        "sync_message": self.env._("Created equipment."),
                    }
                )
        except Exception as exc:  # noqa: BLE001  # pylint: disable=W0718
            self._write_line_error_state(line, exc)

    def _apply_product_like(self, line, label):
        product_obj = self.env["product.product"]
        try:
            with self.env.cr.savepoint():
                if not line.external_id:
                    if label == "harvested_products":
                        company = getattr(self, "company_id", None) or self.env.company
                        product = None
                        msg_src = None
                        if line.code:
                            product = product_obj.search(
                                [("default_code", "=", line.code)], limit=1
                            )
                            if product:
                                msg_src = self.env._("matched by internal reference")
                        if not product and line.name:
                            product = product_obj.search(
                                [("name", "=", line.name)], limit=1
                            )
                            if product:
                                msg_src = self.env._("matched by product name")
                        if not product:
                            product = company.geofolia_default_harvested_product_id
                            if product:
                                msg_src = self.env._("default product from Settings")
                        if product:
                            line.write(
                                {
                                    "product_id": product.id,
                                    "sync_state": "no_action",
                                    "sync_message": self.env._(
                                        "No Geofolia id; %(src)s.",
                                        src=msg_src,
                                    ),
                                }
                            )
                            return
                    line.write(
                        {
                            "sync_state": "skipped",
                            "sync_message": self.env._("Missing id."),
                        }
                    )
                    return
                product = product_obj.search(
                    [("geofolia_external_id", "=", line.external_id)], limit=1
                )
                name_val = (
                    line.name
                    or line.code
                    or self.env._("Geofolia (%(label)s)", label=label)
                )
                code_val = line.code
                ext_val = self._safe_scalar_str(line.external_id) or str(
                    line.external_id
                )
                name_val = self._safe_scalar_str(name_val) or self.env._(
                    "Geofolia (%(label)s)", label=label
                )
                code_val = self._safe_scalar_str(code_val)
                vals = {
                    "name": name_val,
                    "default_code": code_val,
                    "geofolia_external_id": ext_val,
                }
                if product:
                    product.write({k: v for k, v in vals.items() if v})
                    line.write(
                        {
                            "product_id": product.id,
                            "sync_state": "updated",
                            "sync_message": self.env._("Updated product."),
                        }
                    )
                    return
                product = product_obj.create(self._sanitize_create_vals(vals))
                line.write(
                    {
                        "product_id": product.id,
                        "sync_state": "created",
                        "sync_message": self.env._("Created product."),
                    }
                )
        except Exception as exc:  # noqa: BLE001  # pylint: disable=W0718
            self._write_line_error_state(line, exc)

    def _get_analytic_account_for_activity(self, _activity):
        """Return analytic account: from parcel use_unit or company default."""
        company = getattr(self, "company_id", None) or self.env.company
        account = None
        location = company.geofolia_default_fsm_location_id
        if (
            location
            and getattr(location, "ter_use_unit_id", None)
            and location.ter_use_unit_id
        ):
            unit = location.ter_use_unit_id
            if getattr(unit, "account_id", None) and unit.account_id:
                account = unit.account_id
        if not account and company.geofolia_default_parcel_id:
            parcel = company.geofolia_default_parcel_id
            unit = self.env["ter.use_unit"].search(
                [("parcel_id", "=", parcel.id)],
                limit=1,
                order="id",
            )
            if unit and getattr(unit, "account_id", None) and unit.account_id:
                account = unit.account_id
        if not account:
            account = company.geofolia_default_analytic_account_id
        if not account:
            account = self.env["account.analytic.account"].search(
                [
                    ("company_id", "in", (company.id, False)),
                    ("plan_id", "!=", False),
                ],
                limit=1,
                order="id",
            )
        if not account:
            account = self.env["account.analytic.account"].search(
                [("company_id", "in", (company.id, False))],
                limit=1,
                order="id",
            )
        return account

    def _get_fsm_location_for_activity(self, activity):
        """Return fsm.location: CropZone PlotId, else company default, else any."""
        fsm_loc_obj = self.env["fsm.location"]
        ter_unit_obj = self.env["ter.use_unit"]
        raw = activity.raw_json or {}
        crop_zones = raw.get("CropZoneIds") or []
        if crop_zones and isinstance(crop_zones[0], dict):
            plot_id = crop_zones[0].get("PlotId")
            if plot_id:
                unit = ter_unit_obj.search(
                    [("geofolia_external_id", "=", str(plot_id))], limit=1
                )
                if unit and unit.fsm_location_id:
                    return unit.fsm_location_id
        company = getattr(self, "company_id", None) or self.env.company
        location = company.geofolia_default_fsm_location_id
        if location:
            return location
        return fsm_loc_obj.search([], limit=1)

    def _get_or_create_fsm_order_for_activity(self, activity):
        """Return or create fsm.order for this activity.

        Stored on activity.fsm_order_id.
        Location: from first CropZone PlotId (if Fields imported)
        or company default.  Enriches the order with equipment,
        description (products / harvests / weather) and sets it
        to the *Completed* stage.
        """
        if activity.fsm_order_id:
            return activity.fsm_order_id
        location = self._get_fsm_location_for_activity(activity)
        if not location:
            return self.env["fsm.order"]
        order_vals = self._build_fsm_order_vals(activity, location)
        order = self.env["fsm.order"].create(order_vals)
        activity.fsm_order_id = order.id
        self.env["fsm.activity"].create(
            {
                "name": activity.operation_name or self.env._("Geofolia activity"),
                "fsm_order_id": order.id,
            }
        )
        order.env.add_to_compute(order._fields["order_activity_ids"], order)
        self._enrich_fsm_order(order, activity)
        return order

    def _build_fsm_order_vals(self, activity, location):
        """Build vals dict for fsm.order creation."""
        op_name = activity.operation_name or self.env._("Geofolia activity")
        name = self._build_order_name(op_name, activity, location)
        order_vals = {
            "location_id": location.id,
            "name": name,
        }
        start_dt = end_dt = None
        if activity.starting_date:
            start_dt = datetime.combine(activity.starting_date, datetime.min.time())
            order_vals["request_early"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        if activity.ending_date:
            end_dt = datetime.combine(activity.ending_date, datetime.min.time())
            if not order_vals.get("request_early"):
                order_vals["request_early"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
        if start_dt and activity.duration_minutes and not end_dt:
            end_dt = start_dt + timedelta(minutes=activity.duration_minutes)
        elif end_dt and activity.duration_minutes and not start_dt:
            start_dt = end_dt - timedelta(minutes=activity.duration_minutes)
        if start_dt:
            order_vals["scheduled_date_start"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        if end_dt:
            order_vals["scheduled_date_end"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
        if start_dt and end_dt and not activity.duration_minutes:
            delta = end_dt - start_dt
            order_vals["scheduled_duration"] = delta.total_seconds() / 3600.0
        elif activity.duration_minutes:
            order_vals["scheduled_duration"] = activity.duration_minutes / 60.0
        # Actual execution dates (Geofolia activities are "Realizado")
        self._set_actual_dates(order_vals, start_dt, end_dt, activity)
        return order_vals

    @staticmethod
    def _build_order_name(op_name, activity, location):
        """Build a descriptive order name: 'OPERATION · Location · DD/MM/YYYY'."""
        parts = [op_name]
        loc_name = location.display_name or ""
        if loc_name:
            parts.append(loc_name)
        date_str = ""
        if activity.starting_date:
            date_str = activity.starting_date.strftime("%d/%m/%Y")
        elif activity.ending_date:
            date_str = activity.ending_date.strftime("%d/%m/%Y")
        if date_str:
            parts.append(date_str)
        return " · ".join(parts)

    @staticmethod
    def _set_actual_dates(order_vals, start_dt, end_dt, activity):
        """Set date_start / date_end (actual execution) on *order_vals*."""
        if start_dt:
            order_vals["date_start"] = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        actual_end = None
        if start_dt and activity.duration_minutes:
            actual_end = start_dt + timedelta(minutes=activity.duration_minutes)
        elif end_dt:
            actual_end = end_dt
        if actual_end:
            order_vals["date_end"] = actual_end.strftime("%Y-%m-%d %H:%M:%S")

    # -- fsm.order enrichment helpers --------------------------------

    def _enrich_fsm_order(self, order, activity):
        """Enrich *order* with structured usage lines and completed stage."""
        raw = activity.raw_json or {}
        self._link_equipment_to_order(order, raw)
        self._create_product_usage_lines(order, raw)
        self._create_equipment_usage_lines(order, raw)
        self._create_person_usage_lines(order, raw)
        worked = self._compute_worked_surface(raw)
        description = self._build_order_description(activity, raw)
        write_vals = {}
        if description:
            write_vals["description"] = description
        if worked > 0:
            write_vals["worked_surface"] = worked
        if write_vals:
            order.write(write_vals)
        order.action_complete()

    def _create_product_usage_lines(self, order, raw):
        """Create fsm.order.product.usage from ProductIds."""
        products = raw.get("ProductIds") or []
        if not products:
            return
        product_obj = self.env["product.product"]
        usage_obj = self.env["fsm.order.product.usage"]
        vals_list = []
        for seq, prod in enumerate(products, start=10):
            if not isinstance(prod, dict):
                continue
            supply_id = prod.get("SupplyId") or ""
            name = prod.get("SupplyName") or self.env._("Unknown")
            odoo_product = product_obj.browse()
            if supply_id:
                odoo_product = product_obj.search(
                    [
                        (
                            "geofolia_external_id",
                            "=",
                            str(supply_id),
                        )
                    ],
                    limit=1,
                )
            vals_list.append(
                {
                    "fsm_order_id": order.id,
                    "sequence": seq,
                    "product_id": odoo_product.id or False,
                    "name": self._safe_scalar_str(name) or str(supply_id),
                    "quantity": prod.get("Quantity") or 0.0,
                    "uom_name": prod.get("ReferentialUnitSymbol") or "",
                    "geofolia_supply_id": str(supply_id) if supply_id else False,
                    "geofolia_recognition_id": str(prod.get("RecognitionId") or "")
                    or False,
                }
            )
        if vals_list:
            usage_obj.create(vals_list)

    def _create_equipment_usage_lines(self, order, raw):
        """Create fsm.order.equipment.usage from ActionEquipments."""
        equip_items = raw.get("ActionEquipments") or []
        if not equip_items:
            return
        equipment_obj = self.env["fsm.equipment"]
        usage_obj = self.env["fsm.order.equipment.usage"]
        vals_list = []
        for seq, item in enumerate(equip_items, start=10):
            if not isinstance(item, dict):
                continue
            ext_id = item.get("EquipmentId") or ""
            name = item.get("EquipmentName") or self.env._("Unknown")
            minutes = item.get("EquipmentTime") or 0.0
            odoo_equip = equipment_obj.browse()
            if ext_id:
                odoo_equip = equipment_obj.search(
                    [
                        (
                            "geofolia_external_id",
                            "=",
                            str(ext_id),
                        )
                    ],
                    limit=1,
                )
            vals_list.append(
                {
                    "fsm_order_id": order.id,
                    "sequence": seq,
                    "equipment_id": odoo_equip.id or False,
                    "name": self._safe_scalar_str(name) or str(ext_id),
                    "hours": minutes / 60.0,
                    "geofolia_equipment_id": str(ext_id) if ext_id else False,
                    "geofolia_recognition_id": str(
                        item.get("EquipmentRecognitionId") or ""
                    )
                    or False,
                }
            )
        if vals_list:
            usage_obj.create(vals_list)

    def _create_person_usage_lines(self, order, raw):
        """Create fsm.order.person.usage from ActionEmployees."""
        emp_items = raw.get("ActionEmployees") or []
        if not emp_items:
            return
        person_obj = self.env["fsm.person"]
        usage_obj = self.env["fsm.order.person.usage"]
        vals_list = []
        for seq, item in enumerate(emp_items, start=10):
            if not isinstance(item, dict):
                continue
            ext_id = item.get("EmployeeId") or ""
            first = item.get("EmployeeFirstName") or ""
            last = item.get("EmployeeName") or ""
            name = ("%s %s" % (first, last)).strip()
            if not name:
                name = self.env._("Unknown")
            minutes = item.get("EmployeeTime") or 0.0
            odoo_person = person_obj.browse()
            if ext_id:
                odoo_person = person_obj.search(
                    [("geofolia_external_id", "=", str(ext_id))],
                    limit=1,
                )
            vals_list.append(
                {
                    "fsm_order_id": order.id,
                    "sequence": seq,
                    "person_id": odoo_person.id or False,
                    "name": name,
                    "hours": minutes / 60.0,
                    "geofolia_employee_id": (str(ext_id) if ext_id else False),
                    "geofolia_recognition_id": str(
                        item.get("EmployeeRecognitionId") or ""
                    )
                    or False,
                }
            )
        if vals_list:
            usage_obj.create(vals_list)

    @staticmethod
    def _compute_worked_surface(raw):
        """Return total worked surface in m² from CropZoneIds."""
        zones = raw.get("CropZoneIds") or []
        return sum((z.get("WorkedSurface") or 0) for z in zones if isinstance(z, dict))

    def _link_equipment_to_order(self, order, raw):
        """Link fsm.equipment from ActionEquipments to the order."""
        equipment_obj = self.env["fsm.equipment"]
        equip_items = raw.get("ActionEquipments") or []
        seen_ids = set()
        link_cmds = []
        for item in equip_items:
            if not isinstance(item, dict):
                continue
            ext_id = item.get("EquipmentId")
            if not ext_id or ext_id in seen_ids:
                continue
            seen_ids.add(ext_id)
            equip = equipment_obj.search(
                [("geofolia_external_id", "=", str(ext_id))],
                limit=1,
            )
            if equip:
                link_cmds.append((4, equip.id))
        if link_cmds:
            order.sudo().write({"equipment_ids": link_cmds})

    def _build_order_description(self, activity, raw):
        """Build HTML description with products, harvests and weather."""
        parts = []
        if activity.comment:
            comment = str(activity.comment).strip()
            if comment:
                parts.append("<b>%s</b>: %s" % (self.env._("Geofolia Ref."), comment))
        cat = activity.operation_category
        if cat:
            parts.append("<b>%s</b>: %s" % (self.env._("Category"), cat))
        self._append_products_description(parts, raw)
        self._append_harvests_description(parts, raw)
        self._append_weather_description(parts, raw)
        self._append_cropzones_description(parts, raw)
        if not parts:
            return ""
        return "<br/>".join(parts)

    def _append_products_description(self, parts, raw):
        """Append product lines to *parts*."""
        products = raw.get("ProductIds") or []
        if not products:
            return
        lines = []
        for prod in products:
            if not isinstance(prod, dict):
                continue
            name = prod.get("SupplyName") or self.env._("Unknown")
            qty = prod.get("Quantity") or 0
            unit = prod.get("ReferentialUnitSymbol") or ""
            lines.append("&nbsp;&nbsp;• %s: %s %s" % (name, qty, unit))
        if lines:
            parts.append(
                "<b>%s</b><br/>%s" % (self.env._("Products"), "<br/>".join(lines))
            )

    def _append_harvests_description(self, parts, raw):
        """Append harvest lines to *parts*."""
        harvests = raw.get("ActionHarvests") or []
        if not harvests:
            return
        lines = []
        for harv in harvests:
            if not isinstance(harv, dict):
                continue
            name = harv.get("HarvestGoodName") or self.env._("Unknown")
            qty = harv.get("Quantity") or 0
            unit = harv.get("HarvestGoodsUnitSymbol") or ""
            lines.append("&nbsp;&nbsp;• %s: %s %s" % (name, qty, unit))
        if lines:
            parts.append(
                "<b>%s</b><br/>%s" % (self.env._("Harvests"), "<br/>".join(lines))
            )

    def _append_weather_description(self, parts, raw):
        """Append weather info to *parts*."""
        weather_items = []
        if raw.get("Temperature"):
            weather_items.append(
                "%s: %s°C" % (self.env._("Temperature"), raw["Temperature"])
            )
        if raw.get("Hygrometry"):
            weather_items.append(
                "%s: %s%%" % (self.env._("Humidity"), raw["Hygrometry"])
            )
        if raw.get("WindSpeed"):
            direction = raw.get("WindDirection") or ""
            weather_items.append(
                "%s: %s %s" % (self.env._("Wind"), raw["WindSpeed"], direction)
            )
        if raw.get("Weather"):
            weather_items.append(raw["Weather"])
        if weather_items:
            parts.append(
                "<b>%s</b>: %s" % (self.env._("Weather"), ", ".join(weather_items))
            )

    def _append_cropzones_description(self, parts, raw):
        """Append worked surface info to *parts*."""
        zones = raw.get("CropZoneIds") or []
        if not zones:
            return
        total_ha = sum(
            (z.get("WorkedSurface") or 0) for z in zones if isinstance(z, dict)
        )
        if total_ha > 0:
            parts.append(
                "<b>%s</b>: %.2f m²" % (self.env._("Worked surface"), total_ha)
            )

    def _ensure_location_persons(self, location_ids, person_id):
        """Link fsm.person to fsm.location via fsm.location.person."""
        if not location_ids or not person_id:
            return
        loc_person_obj = self.env["fsm.location.person"]
        for loc_id in location_ids:
            exists = loc_person_obj.search(
                [
                    ("location_id", "=", loc_id),
                    ("person_id", "=", person_id),
                ],
                limit=1,
            )
            if not exists:
                loc_person_obj.sudo().create(
                    {"location_id": loc_id, "person_id": person_id}
                )

    def _find_person_for_activity_employee(self, line):
        """Find fsm.person by employee_id_external or employee_name."""
        person_obj = self.env["fsm.person"]
        if line.employee_id_external:
            person = person_obj.search(
                [("geofolia_external_id", "=", line.employee_id_external)],
                limit=1,
            )
            if person:
                return person
        if line.employee_name:
            return person_obj.search([("name", "=", line.employee_name)], limit=1)
        return person_obj.browse()

    def _build_analytic_vals_for_activity_employee(self, line, person, activity):
        """Build vals dict for account.analytic.line create/update."""
        analytic_obj = self.env["account.analytic.line"]
        ext_id = ":".join(
            [
                line.employee_action_id or "",
                line.employee_recognition_id or "",
                str(line.employee_order or 0),
            ]
        )
        line_date = activity.starting_date or activity.ending_date
        unit_amount = (line.employee_time or 0.0) / 60.0
        vals = {
            "name": activity.operation_name or self.env._("Geofolia activity"),
            "date": line_date,
            "unit_amount": unit_amount,
            "amount": 0.0,
            "geofolia_external_id": ext_id,
        }
        if "employee_id" in analytic_obj._fields:
            emp = self.env["hr.employee"].search([("name", "=", person.name)], limit=1)
            if emp:
                vals["employee_id"] = emp.id
        account = self._get_analytic_account_for_activity(activity)
        if account:
            col = (
                account.plan_id._column_name()
                if getattr(account, "plan_id", None)
                else "account_id"
            )
            if col in analytic_obj._fields:
                vals[col] = account.id
            elif "account_id" in analytic_obj._fields:
                vals["account_id"] = account.id
        return vals, account

    def _apply_activity_employee_line(self, line):
        """Create/update analytic line and assign fsm.person to fsm.order."""
        analytic_obj = self.env["account.analytic.line"]
        has_fsm_order = "fsm_order_id" in analytic_obj._fields

        try:
            with self.env.cr.savepoint():
                if line.analytic_line_id:
                    line.write(
                        {
                            "sync_state": "no_action",
                            "sync_message": self.env._("Already linked."),
                        }
                    )
                    return
                person = self._find_person_for_activity_employee(line)
                if not person:
                    line.write(
                        {
                            "sync_state": "skipped",
                            "sync_message": self.env._(
                                "Field service person not found."
                            ),
                        }
                    )
                    return
                activity = line.activity_line_id
                line_date = activity.starting_date or activity.ending_date
                if not line_date:
                    line.write(
                        {
                            "sync_state": "skipped",
                            "sync_message": self.env._("Activity has no date."),
                        }
                    )
                    return
                vals, account = self._build_analytic_vals_for_activity_employee(
                    line, person, activity
                )
                ext_id = vals["geofolia_external_id"]
                existing = analytic_obj.search(
                    [("geofolia_external_id", "=", ext_id)], limit=1
                )
                if not existing and not account:
                    line.write(
                        {
                            "sync_state": "skipped",
                            "sync_message": self.env._(
                                "Set analytic account (parcel or Geofolia settings)."
                            ),
                        }
                    )
                    return
                fsm_order = self._get_or_create_fsm_order_for_activity(activity)
                if fsm_order:
                    fsm_order.sudo().write(
                        {
                            "person_id": person.id,
                            "person_ids": [(4, person.id)],
                        }
                    )
                    if has_fsm_order:
                        vals["fsm_order_id"] = fsm_order.id
                        if (
                            "project_id" in analytic_obj._fields
                            and fsm_order.project_id
                        ):
                            vals["project_id"] = fsm_order.project_id.id
                        if (
                            "task_id" in analytic_obj._fields
                            and fsm_order.project_task_id
                        ):
                            vals["task_id"] = fsm_order.project_task_id.id
                if existing:
                    existing.write(vals)
                    line.write(
                        {
                            "person_id": person.id,
                            "analytic_line_id": existing.id,
                            "sync_state": "updated",
                            "sync_message": self.env._("Updated analytic line."),
                        }
                    )
                else:
                    rec = analytic_obj.create(vals)
                    line.write(
                        {
                            "person_id": person.id,
                            "analytic_line_id": rec.id,
                            "sync_state": "created",
                            "sync_message": self.env._("Created analytic line."),
                        }
                    )
                self._link_person_to_locations_by_farm(line, person)
        except Exception as exc:  # noqa: BLE001  # pylint: disable=W0718
            self._write_line_error_state(line, exc)

    def _link_person_to_locations_by_farm(self, activity_employee_line, person):
        """Link person to fsm.locations whose field has same FarmIdentificationCode."""
        activity = activity_employee_line.activity_line_id
        farm_code = activity.farm_identification_code
        if not farm_code or not person:
            return
        field_lines = self.env["geofolia.import.line"].search(
            [
                ("farm_identification_code", "=", farm_code),
                ("fsm_location_id", "!=", False),
            ]
        )
        location_ids = field_lines.mapped("fsm_location_id").ids
        self._ensure_location_persons(location_ids, person.id)
