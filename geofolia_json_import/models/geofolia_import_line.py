# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, fields, models
from odoo.exceptions import UserError


class GeofoliaImportLine(models.Model):
    _name = "geofolia.import.line"
    _description = "Geofolia Import Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    import_type = fields.Selection(related="job_id.import_type", store=True, readonly=True)

    external_uuid = fields.Char()
    code = fields.Char()
    name = fields.Char()

    raw_json = fields.Json()
    raw_json_text = fields.Text()

    harvest_year = fields.Integer()
    area = fields.Float()
    city = fields.Char()
    crop_name = fields.Char()
    geography_wkt = fields.Text()

    supply_id = fields.Char()
    category_enum = fields.Integer()
    product_type_enum = fields.Integer()
    unit_symbol = fields.Char()
    botanical_species = fields.Char()
    variety_name = fields.Char()
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

    ter_unit_id = fields.Many2one(
        "ter.use_unit",
        string="Ter Unit",
        ondelete="set null",
        help="Target ter.use_unit created/updated by this line.",
    )

    def action_transform(self):
        """Transform / apply this line (called by Apply / Carga)."""
        return self.action_apply_selected()

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(_("Missing job."))
            if line.job_id.import_type != "fields":
                continue
            line.job_id._apply_field_line_to_ter_unit(line)
