# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import unicodedata

from odoo import api, fields, models
from odoo.exceptions import UserError


class TerUseUnit(models.Model):
    _inherit = "ter.use_unit"

    _geofolia_lock_field = "geofolia_external_id"
    _geofolia_protected_fields = (
        "geofolia_external_id",
        "geofolia_code",
        "geofolia_harvest_year",
        "geofolia_crop_name",
        "geofolia_city",
    )

    geofolia_external_id = fields.Char(
        string="Geofolia ID",
        index=True,
        copy=False,
        groups="ter_analytic_geofolia.group_geofolia_import",
        help="External ID from Geofolia (Field) import. Prevents duplicate imports.",
    )
    fsm_location_id = fields.Many2one(
        comodel_name="fsm.location",
        string="FSM Location",
        index=True,
        ondelete="set null",
        help="Linked Field Service location (1:1 with this use unit).",
    )
    geofolia_code = fields.Char(copy=False)
    geofolia_harvest_year = fields.Integer(copy=False)
    geofolia_crop_name = fields.Char(copy=False)
    geofolia_city = fields.Char(copy=False)

    worked_unit_ids = fields.One2many(
        comodel_name="fsm.order.worked.unit",
        inverse_name="use_unit_id",
        string="Worked in work orders",
    )
    fsm_order_count = fields.Integer(
        compute="_compute_fsm_order_count",
    )

    _sql_constraints = [
        (
            "geofolia_ter_use_unit_external_id_uniq",
            "unique(geofolia_external_id)",
            "A use unit with this Geofolia ID already exists.",
        ),
    ]

    def write(self, vals):
        protected = [name for name in self._geofolia_protected_fields if name in vals]
        if protected and not self.env.context.get("geofolia_sync"):
            locked = self.sudo().filtered(self._geofolia_lock_field)
            if locked:
                raise UserError(
                    self.env._(
                        "These fields come from Geofolia and can only be "
                        "updated by re-importing from Geofolia: %(fields)s",
                        fields=", ".join(sorted(protected)),
                    )
                )
        return super().write(vals)

    @api.depends("worked_unit_ids.fsm_order_id")
    def _compute_fsm_order_count(self):
        for record in self:
            record.fsm_order_count = len(record.worked_unit_ids.mapped("fsm_order_id"))

    def action_view_fsm_orders(self):
        """Open the work orders (Partes) that worked on this use unit."""
        self.ensure_one()
        orders = self.worked_unit_ids.mapped("fsm_order_id")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Work Orders"),
            "res_model": "fsm.order",
            "view_mode": "list,form,kanban",
            "domain": [("id", "in", orders.ids)],
        }

    @api.model
    def _geofolia_crop_code(self, crop_name):
        """Return a 3-letter uppercase ASCII code from the crop name."""
        raw = (crop_name or "").strip()
        if not raw:
            return "XXX"
        normalized = unicodedata.normalize("NFKD", raw)
        ascii_only = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        letters = "".join(ch for ch in ascii_only if ch.isalnum())
        return letters[:3].upper() or "XXX"

    def _ter_unit_name_extra_code(self, vals):
        """Insert the Geofolia crop code in the auto-generated unit name."""
        crop_name = vals.get("geofolia_crop_name")
        if crop_name:
            return self._geofolia_crop_code(crop_name)
        return super()._ter_unit_name_extra_code(vals)

    def recompute_geofolia_names(self):
        """Rewrite the name of the Geofolia use units in ``self``.

        Units are grouped by (parcel, date_start, date_end) and ordered by
        crop then Geofolia id so the sequence (NN) is deterministic and
        idempotent on re-import. The name is built with the shared
        ``_build_ter_unit_name`` helper (parcel + YYMM period + crop code +
        sequence). The linked FSM location partner name is kept in sync so
        the location is recognizable too.
        """
        units = self.filtered("geofolia_external_id")
        groups = {}
        for unit in units:
            key = (
                unit.parcel_id.id,
                unit._ter_unit_period_code(unit.date_start),
                unit._ter_unit_period_code(unit.date_end),
            )
            groups.setdefault(key, self.browse())
            groups[key] |= unit
        synced = self.with_context(geofolia_sync=True)
        for group in groups.values():
            ordered = group.sorted(
                key=lambda u: (
                    u._geofolia_crop_code(u.geofolia_crop_name),
                    u.geofolia_external_id or "",
                    u.id,
                )
            )
            for seq, unit in enumerate(ordered):
                parcel = unit.parcel_id
                name = self._build_ter_unit_name(
                    {
                        "parcel_code": (parcel.name or parcel.alphanum_code or ""),
                        "date_start": unit.date_start,
                        "date_end": unit.date_end,
                        "extra_code": unit._geofolia_crop_code(unit.geofolia_crop_name),
                        "seq": seq,
                    }
                )
                if unit.name != name:
                    synced.browse(unit.id).name = name
                location = unit.fsm_location_id
                if location and location.partner_id.name != name:
                    location.partner_id.name = name
        return True
