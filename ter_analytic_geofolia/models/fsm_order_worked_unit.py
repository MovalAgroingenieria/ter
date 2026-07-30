# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class FsmOrderWorkedUnit(models.Model):
    """Crop unit (use unit) worked during a field service order.

    A single Geofolia activity can span several crop units (``CropZoneIds``).
    Each record links one crop unit worked in the activity together with the
    surface worked on it, so the whole Parte can be seen in one place.
    """

    _name = "fsm.order.worked.unit"
    _description = "FSM Order Worked Crop Unit"
    _inherit = "fsm.order.usage.mixin"

    _geofolia_protected_fields = (
        "name",
        "plot_code",
        "worked_surface",
        "geofolia_plot_id",
    )

    use_unit_id = fields.Many2one(
        comodel_name="ter.use_unit",
        string="Crop Unit",
        ondelete="set null",
        index=True,
    )
    name = fields.Char(
        help="Internal fallback label (Geofolia plot code) used when the "
        "crop unit could not be matched. Not shown by default.",
    )
    plot_code = fields.Char(
        help="Plot code from Geofolia.",
    )
    worked_surface = fields.Float(
        digits=(16, 2),
        help="Surface worked on this crop unit in m² (from Geofolia).",
    )
    geofolia_plot_id = fields.Char(
        string="Geofolia Plot ID",
        index=True,
    )

    @api.depends("name", "worked_surface")
    def _compute_display_name(self):
        for record in self:
            if record.worked_surface:
                record.display_name = "%s — %.2f m²" % (
                    record.name or "",
                    record.worked_surface,
                )
            else:
                record.display_name = record.name or ""
