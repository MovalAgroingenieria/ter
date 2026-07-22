# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
"""Backfill geofolia_created on parcels auto-created by previous Geofolia imports.

Parcels created by the Fields import use the ``GF{yy}-{seq}`` code pattern and
are linked to a ter.use_unit carrying a Geofolia external id.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE ter_parcel tp
        SET geofolia_created = true
        WHERE tp.geofolia_created IS NOT TRUE
          AND tp.alphanum_code ~ '^GF[0-9]{2}-[0-9]+$'
          AND EXISTS (
              SELECT 1 FROM ter_use_unit u
              WHERE u.parcel_id = tp.id
                AND u.geofolia_external_id IS NOT NULL
          )
        """)
