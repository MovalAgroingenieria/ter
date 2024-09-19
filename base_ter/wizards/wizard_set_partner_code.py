# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, exceptions, _


class WizardSetPartnerCode(models.TransientModel):
    _name = 'wizard.set.partner.code'
    _description = 'Dialog box to set a partner code'

    partner_code = fields.Integer(
        string='Partner Code',)

    @api.model
    def default_get(self, var_fields):
        resp = None
        record = self.env['res.partner'].browse(
            self.env.context['active_id'])
        if record:
            resp = {
                'partner_code': record.partner_code,
                }
        return resp

    def set_partner_code(self):
        self.ensure_one()
        record = self.env['res.partner'].browse(
            self.env.context['active_id'])
        if record:
            partner_code = self.partner_code
            if not partner_code:
                partner_code = 0
                if record.parcel_ids:
                    raise exceptions.ValidationError(_(
                        'If a partner has any parcel, it is not possible to '
                        'reset the code.'))
            record.write({
                'partner_code': partner_code,
                })
