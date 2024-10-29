# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Parameter initialization.
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_wmsbase_url',
        'https://www.ign.es/wms-inspire/pnoa-ma')
    env['ir.config_parameter'].set_param(
        'base_ter.aerial_image_wmsbase_layers', 'OI.OrthoimageCoverage')
    # Load i18n_extra.
    env.ref('base.module_l10n_es_territory')._update_translations(
        overwrite=True)
