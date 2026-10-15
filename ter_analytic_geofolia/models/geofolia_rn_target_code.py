# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from lxml import etree

from odoo import api, fields, models, tools


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

    @api.model
    def _register_catalogue_xmlids(self):
        """Reuse manually created codes when installing the reference catalogue."""
        data = self.env["ir.model.data"].sudo()
        with tools.file_open(
            "ter_analytic_geofolia/data/geofolia_rn_target_code_data.xml"
        ) as source:
            catalogue_ids = set(etree.parse(source).xpath("//record/@id"))
        registered = set(
            data.search(
                [("module", "=", "ter_analytic_geofolia"), ("model", "=", self._name)]
            ).mapped("name")
        )
        values = []
        for target in self.search([], limit=None):
            if (
                not target.code
                or not target.code.isascii()
                or not target.code.isdigit()
            ):
                continue
            name = "rn_target_%s" % target.code
            if name in catalogue_ids and name not in registered:
                values.append(
                    {
                        "module": "ter_analytic_geofolia",
                        "name": name,
                        "model": self._name,
                        "res_id": target.id,
                        "noupdate": False,
                    }
                )
                registered.add(name)
        if values:
            data.create(values)

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
