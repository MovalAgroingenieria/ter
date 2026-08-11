# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, api


class ReportParcelProfile(models.AbstractModel):
    _name = 'report.base_ter.parcel_profile_template'
    _description = 'Parcels by Profile Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        # When 'data' is passed, the client drops the docids from the URL,
        # so they must be recovered from the context (active_ids).
        if not docids:
            docids = self.env.context.get('active_ids', [])
        partners = self.env['res.partner'].browse(docids)
        profile_ids = data.get('profile_ids') or \
            partners.mapped('partnerlink_ids.profile_id').ids
        profiles = self.env['ter.profile'].browse(profile_ids)
        has_overhead = \
            'area_overhead' in self.env['ter.parcel.partnerlink']._fields
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': partners,
            'profiles': profiles,
            'has_overhead': has_overhead,
        }