# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
            ("full", "Full (All blocks)"),
        ],
        default="auto",
        required=True,
    )

    def action_import(self):
        self.ensure_one()
        if not self.file_data:
            raise UserError(_("No file provided."))

        try:
            itype = self.import_type
            if itype == "auto":
                itype = self._autodetect_type()

            with self.env.cr.savepoint():
                job = self.env["geofolia.import.job"].create(
                    {
                        "name": self.file_name or _("Geofolia Import"),
                        "import_type": itype,
                        "file_name": self.file_name,
                        "file_data": self.file_data,
                    }
                )
                job.action_parse()
                if job.state == "done":
                    job.action_apply()
        except UserError as exc:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Import error"),
                    "message": str(exc),
                    "type": "danger",
                    "sticky": True,
                },
            }
        except Exception as exc:
            _logger.exception("Geofolia import failed")
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Import failed"),
                    "message": str(exc) or type(exc).__name__,
                    "type": "danger",
                    "sticky": True,
                },
            }

        return {
            "type": "ir.actions.act_window",
            "res_model": "geofolia.import.job",
            "view_mode": "form",
            "res_id": job.id,
            "target": "current",
        }

    def _autodetect_type(self):
        payload = (
            self.env["geofolia.import.job"]
            .new({"file_data": self.file_data})
            ._load_json_payload()
        )

        if isinstance(payload, dict):
            if isinstance(payload.get("Fields"), list):
                return "fields"
            if isinstance(payload.get("Products"), list) and isinstance(
                payload.get("Employees"), list
            ):
                return "full"
            if isinstance(payload.get("Products"), list):
                return "products"

        raise UserError(_("Cannot autodetect JSON type. Choose it manually."))
