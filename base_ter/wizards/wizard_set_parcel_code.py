# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class WizardSetParcelCode(models.TransientModel):
    _name = 'wizard.set.parcel.code'
    _description = 'Dialog box to set a parcel code'

    parcel_code = fields.Char(
        string='Parcel Code',)

    @api.model
    def default_get(self, var_fields):
        resp = None
        record = self.env['ter.parcel'].browse(
            self.env.context['active_id'])
        if record:
            resp = {
                'parcel_code': record.alphanum_code,
                }
        return resp

    def set_parcel_code(self):
        self.ensure_one()
        record = self.env['ter.parcel'].browse(
            self.env.context['active_id'])
        if record:
            parcel_code = self.parcel_code
            if not parcel_code:
                parcel_code = None
            else:
                parcel_code = parcel_code.strip().upper()
            record.write({
                'alphanum_code': parcel_code,
                })
