# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.exceptions import UserError


class GeofoliaImportEquipmentLine(models.Model):
    _name = "geofolia.import.equipment.line"
    _description = "Geofolia Import Equipment Line"
    _order = "id asc"
    _inherit = "geofolia.import.base.line"

    external_id = fields.Char(index=True)
    farm_identification_code = fields.Char(
        default="",
        index=True,
        help="Farm identification from Geofolia; same EquipmentId can appear per farm.",
    )
    code = fields.Char()
    name = fields.Char()
    category = fields.Char()

    equipment_id = fields.Many2one(
        "fsm.equipment",
        string="FSM Equipment",
        ondelete="set null",
    )

    _sql_constraints = [
        (
            "geofolia_equipment_job_ext_farm_uniq",
            "unique(job_id, external_id, farm_identification_code)",
            "This equipment (and farm) has already been imported in this job.",
        ),
    ]

    def action_apply_selected(self):
        for record in self:
            if not record.job_id:
                raise UserError(self.env._("Missing job."))
            record.job_id._apply_equipment_line(record)  # pylint: disable=W0212
            record.job_id._recompute_apply_state()  # pylint: disable=W0212
