# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class FsmOrderEquipmentUsage(models.Model):
    """Equipment usage (with time) during a field service order.

    Each record represents one piece of equipment (tractor, sprayer…)
    used during an activity imported from Geofolia.  Hours come from
    the JSON ``ActionEquipments`` block (``EquipmentTime`` in minutes,
    stored here as hours).
    """

    _name = "fsm.order.equipment.usage"
    _description = "FSM Order Equipment Usage"
    _inherit = "fsm.order.usage.mixin"

    _geofolia_protected_fields = (
        "name",
        "hours",
        "geofolia_equipment_id",
        "geofolia_recognition_id",
    )

    equipment_id = fields.Many2one(
        comodel_name="fsm.equipment",
        ondelete="set null",
        index=True,
    )
    name = fields.Char(
        required=True,
        help="Equipment name from Geofolia.",
    )
    hours = fields.Float(
        digits=(16, 4),
        help="Usage time in hours (converted from Geofolia minutes).",
    )
    geofolia_equipment_id = fields.Char(
        string="Geofolia Equipment ID",
        index=True,
    )

    @api.depends("name", "hours")
    def _compute_display_name(self):
        for record in self:
            if record.hours:
                record.display_name = "%s — %.2f h" % (
                    record.name or "",
                    record.hours,
                )
            else:
                record.display_name = record.name or ""
