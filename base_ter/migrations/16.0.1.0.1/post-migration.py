# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    """Recompute stored number_of_parcels from active parcels only."""
    cr.execute(
        """
        UPDATE res_partner partner
           SET number_of_parcels = COALESCE(src.active_count, 0)
          FROM (
                SELECT parcel.partner_id,
                       COUNT(*) FILTER (WHERE parcel.active) AS active_count
                  FROM ter_parcel parcel
                 GROUP BY parcel.partner_id
               ) src
         WHERE partner.id = src.partner_id
           AND partner.number_of_parcels IS DISTINCT FROM src.active_count
        """
    )

    cr.execute(
        """
        UPDATE res_partner partner
           SET number_of_parcels = 0
         WHERE partner.number_of_parcels IS DISTINCT FROM 0
           AND NOT EXISTS (
                SELECT 1
                  FROM ter_parcel parcel
                 WHERE parcel.partner_id = partner.id
                   AND parcel.active
           )
        """
    )