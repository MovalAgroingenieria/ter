# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, SUPERUSER_ID, exceptions


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute("""
        UPDATE ter_parcel_partnerlink tpp
        SET percentage_overhead = 100,
        area_overhead = tp.area_official
        FROM ter_parcel tp
        WHERE tpp.parcel_id = tp.id AND is_main
    """)
