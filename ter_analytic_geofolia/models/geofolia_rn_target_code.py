# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class GeofoliaRnTargetCode(models.Model):
    """Reference table for the Geofolia ``RNTargetCode`` (Target/Effects).

    Loaded from the Geofolia L_RNTarget reference list via XML data. Used to
    resolve the target/effect of a product usage line imported from
    Geofolia (``fsm.order.product.usage.rn_target_code_id``).
    """

    _name = "geofolia.rn.target.code"
    _description = "Geofolia RN Target Code (Target/Effects)"
    _order = "code"

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)

    _sql_constraints = [
        (
            "code_uniq",
            "unique(code)",
            "This RN target code already exists.",
        ),
    ]

    @api.depends("code", "name")
    def _compute_display_name(self):
        for record in self:
            if record.code:
                record.display_name = f"[{record.code}] {record.name}"
            else:
                record.display_name = record.name
