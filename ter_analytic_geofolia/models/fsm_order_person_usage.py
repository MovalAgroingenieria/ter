# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class FsmOrderPersonUsage(models.Model):
    """Employee/worker time during a field service order.

    Each record represents one worker's time contribution to an
    activity imported from Geofolia.  Hours come from the JSON
    ``ActionEmployees`` block (``EmployeeTime`` in minutes,
    stored here as hours).
    """

    _name = "fsm.order.person.usage"
    _description = "FSM Order Person Usage"
    _order = "sequence, id"

    fsm_order_id = fields.Many2one(
        comodel_name="fsm.order",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    person_id = fields.Many2one(
        comodel_name="fsm.person",
        ondelete="set null",
        index=True,
    )
    name = fields.Char(
        required=True,
        help="Worker name from Geofolia.",
    )
    hours = fields.Float(
        digits=(16, 4),
        help="Work time in hours (converted from Geofolia minutes).",
    )
    geofolia_employee_id = fields.Char(
        string="Geofolia Employee ID",
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
                record.display_name = "%s — %.2f h" % (record.name or "", record.hours)
            else:
                record.display_name = record.name or ""
