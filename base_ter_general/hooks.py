# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, SUPERUSER_ID, _


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("DELETE FROM ir_config_parameter WHERE key LIKE 'base_ter_general.%';")
        env.cr.commit()
    except Exception:
        env.cr.rollback()
