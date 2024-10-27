# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, _


class TerGisParcelModel(models.Model):
    _inherit = ['ter.gis.parcel.model']

    def _compute_gis_data(self):
        super(TerGisParcelModel, self)._compute_gis_data()
        for record in self:
            record.gis_data = record.gis_data + '\n' + \
                '⸰ ' + _('Cadastral Area (m²)') + ': ' + \
                self.env['common.format'].transform_integer_to_locale(
                    record.parcel_id.cadastral_area)
