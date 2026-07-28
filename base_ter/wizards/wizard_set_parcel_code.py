# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class WizardSetParcelCode(models.TransientModel):
    _name = "wizard.set.parcel.code"
    _inherit = ["wizard.active.record.mixin"]
    _description = "Dialog box to set a parcel code"

    parcel_code = fields.Char()
    rename_gis = fields.Boolean(
        string="Rename linked GIS geometry",
        default=True,
        help="Also rename the linked GIS geometry record (ter_gis_parcel) so "
        "the parcel keeps its map geometry after changing the code.",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        parcel = self._get_active_record_or_empty("ter.parcel")
        if parcel.exists():
            res["parcel_code"] = parcel.alphanum_code
        return res

    def set_parcel_code(self):
        self.ensure_one()
        parcel = self._get_active_record_or_empty("ter.parcel")
        if not parcel.exists():
            return

        parcel_code = (self.parcel_code or "").strip().upper() or False
        old_name = parcel.name
        parcel.write({"alphanum_code": parcel_code})
        if self.rename_gis and parcel.name != old_name:
            parcel._rename_gis_link(  # pylint: disable=protected-access
                old_name, parcel.name
            )
