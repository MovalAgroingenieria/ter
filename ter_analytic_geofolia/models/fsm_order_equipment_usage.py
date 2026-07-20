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
    _order = "sequence, id"

    fsm_order_id = fields.Many2one(
        comodel_name="fsm.order",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
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
    geofolia_recognition_id = fields.Char(
        string="Geofolia Recognition ID",
    )

    location_id = fields.Many2one(
        related="fsm_order_id.location_id",
        store=True,
    )
    partner_id = fields.Many2one(
        related="fsm_order_id.location_id.owner_id",
        store=True,
        string="Owner",
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
