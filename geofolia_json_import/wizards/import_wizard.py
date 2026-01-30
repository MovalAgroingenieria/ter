# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError


class GeofoliaImportWizard(models.TransientModel):
    _name = "geofolia.import.wizard"
    _description = "Geofolia Import Wizard"

    file_name = fields.Char()
    file_data = fields.Binary(required=True)

    import_type = fields.Selection(
        selection=[
            ("auto", "Autodetect"),
            ("fields", "Fields (Plots)"),
            ("products", "Products (Supplies)"),
            ("full", "Full export (multi-block)"),
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

        if not isinstance(payload, dict):
            raise UserError(_("Cannot autodetect JSON type. Choose it manually."))

        # "full" if it contains any of these multi-block keys
        multi_keys = (
            "Employees",
            "Partners",
            "HarvestedProducts",
            "Equipments",
            "Activities",
        )
        if any(k in payload for k in multi_keys):
            return "full"

        if isinstance(payload.get("Fields"), list):
            return "fields"
        if isinstance(payload.get("Products"), list):
            return "products"

        raise UserError(_("Cannot autodetect JSON type. Choose it manually."))
