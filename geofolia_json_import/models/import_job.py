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
        selection=[("fields", "Fields (Plots)"), ("products", "Products (Supplies)")],
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

    line_ids = fields.One2many("geofolia.import.line", "job_id", string="Lines")
    line_count = fields.Integer(compute="_compute_line_count", store=False)

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

        self.line_ids.unlink()

        if self.import_type == "fields":
            items = payload.get("Fields")
            if not isinstance(items, list):
                raise UserError(_("Missing or invalid 'Fields' array."))
            self._create_lines_from_fields(items)
        else:
            items = payload.get("Products")
            if not isinstance(items, list):
                raise UserError(_("Missing or invalid 'Products' array."))
            self._create_lines_from_products(items)

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
                }
            )
        if vals_list:
            self.env["geofolia.import.line"].create(vals_list)
