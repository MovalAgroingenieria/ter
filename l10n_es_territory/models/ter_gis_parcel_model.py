# Copyright 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class TerGisParcelModel(models.Model):
    _inherit = "ter.gis.parcel.model"

    @api.depends("parcel_id.cadastral_area")
    def _compute_gis_data(self):
        result = super()._compute_gis_data()
        formatter = self.env["common.format"]
        label = self.env._("Cadastral Area (m²)")

        for record in self:
            cadastral_area = record.parcel_id.cadastral_area if record.parcel_id else 0
            formatted_area = formatter.transform_integer_to_locale(cadastral_area or 0)
            extra = self.env._(
                "\n⸰ %(label)s: %(value)s",
                label=label,
                value=formatted_area,
            )
            record.gis_data = (record.gis_data or "") + extra
        return result
