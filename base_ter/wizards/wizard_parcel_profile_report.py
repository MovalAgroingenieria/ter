# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, exceptions, _


class WizardParcelProfileReport(models.TransientModel):
    _name = 'wizard.parcel.profile.report'
    _description = 'Dialog box to print parcels by profile'

    profile_ids = fields.Many2many(
        string='Profiles',
        comodel_name='ter.profile',
        required=True,)

    @api.model
    def default_get(self, var_fields):
        resp = super().default_get(var_fields)
        partner_ids = self.env.context.get('active_ids', [])
        partners = self.env['res.partner'].browse(partner_ids)
        profiles = partners.mapped('partnerlink_ids.profile_id')
        if profiles:
            resp['profile_ids'] = [(6, 0, profiles.ids)]
        return resp

    def action_print(self):
        self.ensure_one()
        partner_ids = self.env.context.get('active_ids', [])
        partners = self.env['res.partner'].browse(partner_ids)
        if not partners:
            raise exceptions.UserError(_('No partner selected.'))
        data = {'profile_ids': self.profile_ids.ids}
        report = self.env.ref('base_ter.action_parcel_profile_report')
        return report.report_action(partners, data=data)
