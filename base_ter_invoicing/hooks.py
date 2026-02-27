# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import SUPERUSER_ID, api


def post_init_hook(env):
    if not isinstance(env, api.Environment):
        env = api.Environment(env, SUPERUSER_ID, {})

    # Set 100% overhead for main contact; area_overhead is computed from this
    env.cr.execute(
        """
        UPDATE ter_parcel_partnerlink
        SET percentage_overhead = 100.0
        WHERE is_main IS TRUE
        """
    )


def uninstall_hook(env):
    if not isinstance(env, api.Environment):
        env = api.Environment(env, SUPERUSER_ID, {})

    category = env.ref(
        "base_ter_invoicing.product_category_02",
        raise_if_not_found=False,
    )
    if category:
        category.category_code = 0
