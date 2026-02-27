# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    parcel_id = fields.Many2one(
        comodel_name="ter.parcel",
        string="Parcel",
        readonly=True,
        index=True,
    )

    def _ter_invoicing_get_parcel_id_from_billable_item(self, vals):
        """Set parcel_id from ter.parcel.partnerlink when billable_item points to it."""
        if (
            vals.get("billable_item_model") != "ter.parcel.partnerlink"
            or not vals.get("billable_item_res_id")
        ):
            return None
        partnerlink = self.env["ter.parcel.partnerlink"].browse(
            vals["billable_item_res_id"]
        )
        if partnerlink.exists() and partnerlink.parcel_id:
            return partnerlink.parcel_id.id
        return None

    def _ter_invoicing_invalidate_parcel_totals(self, parcel_ids):
        """Invalidate total_invoiced for given parcels so they recompute on next read."""
        if not parcel_ids:
            return
        self.env["ter.parcel"].browse(parcel_ids).invalidate_recordset(
            ["total_invoiced"]
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("parcel_id"):
                parcel_id = self._ter_invoicing_get_parcel_id_from_billable_item(vals)
                if parcel_id:
                    vals["parcel_id"] = parcel_id
        lines = super().create(vals_list)
        parcel_ids = lines.mapped("parcel_id").ids
        self._ter_invoicing_invalidate_parcel_totals(parcel_ids)
        return lines

    def write(self, vals):
        old_parcel_ids = set(self.mapped("parcel_id").ids) if self else set()
        result = super().write(vals)
        # Sync parcel_id when billable item (partnerlink) was changed
        if "billable_item_model" in vals or "billable_item_res_id" in vals:
            to_update = self.filtered(
                lambda l: l.billable_item_model == "ter.parcel.partnerlink"
                and l.billable_item_res_id
            )
            by_parcel = {}  # parcel_id -> recordset
            for line in to_update:
                partnerlink = self.env["ter.parcel.partnerlink"].browse(
                    line.billable_item_res_id
                )
                new_parcel_id = (
                    partnerlink.parcel_id.id
                    if partnerlink.exists() and partnerlink.parcel_id
                    else False
                )
                if line.parcel_id.id != new_parcel_id:
                    by_parcel.setdefault(new_parcel_id, self.env["account.move.line"])
                    by_parcel[new_parcel_id] |= line
            for new_parcel_id, lines in by_parcel.items():
                lines.write({"parcel_id": new_parcel_id})
        new_parcel_ids = set(self.mapped("parcel_id").ids) if self else set()
        self._ter_invoicing_invalidate_parcel_totals(
            list(old_parcel_ids | new_parcel_ids)
        )
        return result

    def unlink(self):
        parcel_ids = self.mapped("parcel_id").ids
        result = super().unlink()
        self._ter_invoicing_invalidate_parcel_totals(parcel_ids)
        return result
