# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import UserError


class TerParcelCadastreCompareWizard(models.TransientModel):
    _name = "ter.parcel.cadastre.compare.wizard"
    _description = "Compare parcel geometry with Cadastre"

    parcel_id = fields.Many2one(
        "ter.parcel",
        required=True,
        ondelete="cascade",
    )
    official_code = fields.Char(related="parcel_id.official_code", readonly=True)
    map_data = fields.Json(readonly=True)
    candidate_summary = fields.Text(readonly=True)
    selected_refcat = fields.Char(string="Selected cadastral reference")
    fill_code = fields.Boolean(
        string="Also fill cadastral reference (if empty)",
        default=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        parcel_id = self.env.context.get("active_id") or res.get("parcel_id")
        if not parcel_id:
            return res
        parcel = self.env["ter.parcel"].browse(parcel_id)
        res["parcel_id"] = parcel.id
        map_data = parcel._cadastre_match_build_map_data()
        res["map_data"] = map_data
        candidates = map_data.get("candidates") or []
        if candidates:
            res["selected_refcat"] = candidates[0]["refcat"]
        res["candidate_summary"] = self._format_candidate_summary(candidates)
        return res

    def _format_candidate_summary(self, candidates):
        if not candidates:
            return self.env._(
                "No overlapping cadastral parcels were found for this geometry."
            )
        lines = [
            self.env._("Overlapping cadastral parcels (by overlap):"),
        ]
        for candidate in candidates:
            lines.append(
                self.env._(
                    "- %(refcat)s: %(pct)s%%",
                    refcat=candidate["refcat"],
                    pct=candidate["intersection"],
                )
            )
        return "\n".join(lines)

    def action_apply_geometry(self):
        self.ensure_one()
        if not self.selected_refcat:
            raise UserError(self.env._("Select a cadastral parcel on the map first."))
        self.parcel_id.cadastre_match_apply_geometry(self.selected_refcat)
        if self.fill_code:
            self.parcel_id.cadastre_match_fill_code(self.selected_refcat)
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_fill_code_only(self):
        self.ensure_one()
        if not self.selected_refcat:
            raise UserError(self.env._("Select a cadastral parcel on the map first."))
        if not self.parcel_id.cadastre_match_fill_code(self.selected_refcat):
            raise UserError(
                self.env._(
                    "The cadastral reference could not be filled (the parcel "
                    "already has one or the reference does not match the "
                    "municipality)."
                )
            )
        return {"type": "ir.actions.client", "tag": "reload"}
