# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
"""Backfill fsm.order.geofolia_activity_id for idempotent re-sync.

Orders created by earlier Geofolia imports have no durable activity marker.
Recover it from the linked import activity line so that a re-import re-syncs
the existing order instead of creating a duplicate.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE fsm_order o
        SET geofolia_activity_id = al.external_id
        FROM geofolia_import_activity_line al
        WHERE al.fsm_order_id = o.id
          AND al.external_id IS NOT NULL
          AND o.geofolia_activity_id IS NULL
        """)
