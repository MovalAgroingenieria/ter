# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


class GeofoliaImportWizard(models.TransientModel):
    _name = "geofolia.import.wizard"
    _description = "Geofolia Import Wizard"

    file_name = fields.Char()
    file_data = fields.Binary(required=True)
    date_range_id = fields.Many2one(
        comodel_name="date.range",
        string="Campaign (Date Range)",
        domain="[('is_unit_use_type', '=', True)]",
        default=lambda self: self.env.company.geofolia_default_date_range_id,
        help="Campaign used for ter.use_unit when importing Fields. Required for Fields/Full import.",
    )
    import_type = fields.Selection(
        selection=[
            ("auto", "Autodetect"),
            ("fields", "Fields (Plots)"),
            ("products", "Products (Supplies)"),
            ("full", "Full (All blocks)"),
        ],
        default="auto",
        required=True,
    )

    def action_import(self):
        self.ensure_one()
        if not self.file_data:
            raise UserError(_("No file provided."))

        itype = self.import_type
        if itype == "auto":
            itype = self._autodetect_type()

        job = self.env["geofolia.import.job"].create(
            {
                "name": self.file_name or _("Geofolia Import"),
                "import_type": itype,
                "file_name": self.file_name,
                "file_data": self.file_data,
                "date_range_id": self.date_range_id.id if self.date_range_id else False,
            }
        )
        job.action_parse()
        return {
            "type": "ir.actions.act_window",
            "res_model": "geofolia.import.job",
            "view_mode": "form",
            "res_id": job.id,
            "target": "current",
        }

    def _autodetect_type(self):
        payload = self.env["geofolia.import.job"].new(
            {"file_data": self.file_data}
        )._load_json_payload()

        if isinstance(payload, dict):
            if isinstance(payload.get("Fields"), list):
                return "fields"
            if isinstance(payload.get("Products"), list) and isinstance(payload.get("Employees"), list):
                return "full"
            if isinstance(payload.get("Products"), list):
                return "products"

        raise UserError(_("Cannot autodetect JSON type. Choose it manually."))
