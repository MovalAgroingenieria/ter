# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


def post_init_hook(env):
    """Load i18n_extra translations to override fieldservice terms."""
    module = env["ir.module.module"].search(
        [("name", "=", "ter_analytic_geofolia")], limit=1
    )
    if module:
        module._update_translations(overwrite=True)  # pylint: disable=protected-access
