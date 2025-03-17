# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    values = env['ir.config_parameter'].sudo()
    sigpac_minimum_intersection_percentage = 0.0
    old_intersection = values.get_param(
        'l10n_es_territory_sigpac.sigpac_minimum_intersection_percentage')
    if (old_intersection):
        sigpac_minimum_intersection_percentage = float(old_intersection)
    values.set_param('l10n_es_territory_sigpac.'
                     'sigpac_minimum_intersection_percentage',
                     sigpac_minimum_intersection_percentage)
