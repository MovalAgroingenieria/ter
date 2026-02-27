# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import SUPERUSER_ID, api


def post_init_hook(env):
    if not isinstance(env, api.Environment):
        env = api.Environment(env, SUPERUSER_ID, {})

    env.cr.execute(
        """
        UPDATE ter_parcel_partnerlink AS tpp
        SET
            percentage_overhead = 100.0,
            area_overhead = tp.area_official
        FROM ter_parcel AS tp
        WHERE tpp.parcel_id = tp.id
          AND tpp.is_main IS TRUE
        """
    )


def uninstall_hook(env):
    if not isinstance(env, api.Environment):
        env = api.Environment(env, SUPERUSER_ID, {})

    env.cr.execute(
        """
        UPDATE product_category
        SET category_code = 0
        WHERE category_code = 2
        """
    )
