# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.exceptions import UserError


class GeofoliaImportLine(models.Model):
    _name = "geofolia.import.line"
    _description = "Geofolia Import Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    import_type = fields.Selection(
        related="job_id.import_type", store=True, readonly=True
    )

    external_uuid = fields.Char()
    farm_identification_code = fields.Char(
        index=True,
        help="Farm identification from Geofolia (Fields). Links workers to locations.",
    )
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
    )
    sync_message = fields.Text()
    fsm_location_id = fields.Many2one(
        "fsm.location",
        string="FSM Location",
        ondelete="set null",
    )
    ter_use_unit_id = fields.Many2one(
        "ter.use_unit",
        string="Territory Use Unit",
        ondelete="set null",
    )

    def action_apply_selected(self):
        for line in self:
            if not line.job_id:
                raise UserError(self.env._("Missing job."))
            if line.job_id.import_type != "fields":
                continue
            line.job_id._apply_field_line(line)  # pylint: disable=W0212
            line.job_id._recompute_apply_state_fields()  # pylint: disable=W0212
