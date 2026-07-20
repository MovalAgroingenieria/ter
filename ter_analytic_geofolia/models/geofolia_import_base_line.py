# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class GeofoliaImportBaseLine(models.AbstractModel):
    _name = "geofolia.import.base.line"
    _description = "Geofolia Import Base Line"

    job_id = fields.Many2one(
        "geofolia.import.job", string="Import", required=True, ondelete="cascade"
    )

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
