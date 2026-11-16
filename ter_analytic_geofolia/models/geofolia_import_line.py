# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
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
    sowing_date = fields.Date(help="SowingDate from Geofolia JSON.")
    harvest_date = fields.Date(help="HarvestDate from Geofolia JSON.")
    area = fields.Float()
    city = fields.Char()
    crop_name = fields.Char()
    geography_wkt = fields.Text()
    crop_mapping_id = fields.Many2one("geofolia.crop.mapping", readonly=True)
    applied_date_start = fields.Date(readonly=True)
    applied_date_end = fields.Date(readonly=True)
    dates_adjusted = fields.Boolean(compute="_compute_review", store=True)
    review_required = fields.Boolean(compute="_compute_review", store=True)
    review_message = fields.Text(compute="_compute_review", store=True)

    @api.depends(
        "sowing_date",
        "harvest_date",
        "applied_date_start",
        "applied_date_end",
        "crop_mapping_id.state",
        "crop_name",
    )
    def _compute_review(self):
        for record in self:
            messages = []
            adjusted = bool(
                (
                    record.sowing_date
                    and record.applied_date_start
                    and record.sowing_date != record.applied_date_start
                )
                or (
                    record.harvest_date
                    and record.applied_date_end
                    and record.harvest_date != record.applied_date_end
                )
            )
            if adjusted:
                messages.append(
                    self.env._(
                        "Geofolia dates: %(start)s / %(end)s. Territorial dates: %(applied_start)s / %(applied_end)s.",
                        start=record.sowing_date or "-",
                        end=record.harvest_date or "-",
                        applied_start=record.applied_date_start or "-",
                        applied_end=record.applied_date_end or "-",
                    )
                )
            if not record.crop_mapping_id or record.crop_mapping_id.state == "review":
                messages.append(
                    self.env._(
                        "Crop mapping pending review: %(crop)s.",
                        crop=record.crop_name or "-",
                    )
                )
            record.dates_adjusted = adjusted
            record.review_required = bool(messages)
            record.review_message = "\n".join(messages) or False

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
        for record in self:
            if not record.job_id:
                raise UserError(self.env._("Missing job."))
            if record.job_id.import_type != "fields":
                continue
            record.job_id.with_context(geofolia_sync=True)._apply_field_line(
                record
            )  # pylint: disable=W0212
            record.job_id._recompute_apply_state_fields()  # pylint: disable=W0212
