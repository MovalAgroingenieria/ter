# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from .geofolia_protection import check_geofolia_protected


class FsmOrderUsageMixin(models.AbstractModel):
    """Common structure for Geofolia FSM order usage lines.

    Shared by the product, equipment and person usage models: the link to
    the order, the Geofolia origin marker and the denormalised owner/location
    relations.  Its ``write`` blocks manual edits of Geofolia-owned values so
    they can only be updated by re-importing.
    """

    _name = "fsm.order.usage.mixin"
    _description = "FSM Order Usage Line Mixin"
    _order = "sequence, id"

    _geofolia_lock_field = "from_geofolia"
    _geofolia_protected_fields = ()

    fsm_order_id = fields.Many2one(
        comodel_name="fsm.order",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    geofolia_recognition_id = fields.Char(
        string="Geofolia Recognition ID",
    )
    from_geofolia = fields.Boolean(
        default=False,
        copy=False,
        help="Set when the line was created by the Geofolia import. "
        "Locked lines can only be updated by re-importing.",
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

    def write(self, vals):
        check_geofolia_protected(
            self, vals, self._geofolia_protected_fields, self._geofolia_lock_field
        )
        return super().write(vals)
