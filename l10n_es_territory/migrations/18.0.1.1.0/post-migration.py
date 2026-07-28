# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_es_territory.hooks import set_default_leaflet_pnoa


def migrate(cr, version):
    """Set the PNOA orthophoto as the default Leaflet base layer."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    set_default_leaflet_pnoa(env)
