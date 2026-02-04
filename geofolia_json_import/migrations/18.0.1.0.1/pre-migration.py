# Copyright 2024-2026 Moval Agroingeniería S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

import logging

from psycopg2 import sql

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Remove duplicate (job_id, external_id) before unique constraint is applied."""
    if not version:
        return

    for table in ("geofolia_import_product_line", "geofolia_import_equipment_line"):
        try:
            cr.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
                """,
                (table,),
            )
            if not cr.fetchone()[0]:
                _logger.info(
                    "geofolia_json_import: Table %s does not exist, skipping duplicate cleanup",
                    table,
                )
                continue
            cr.execute(
                sql.SQL(
                    """
                    DELETE FROM {t} a
                    USING {t} b
                    WHERE a.job_id = b.job_id
                      AND (a.external_id = b.external_id
                           OR (a.external_id IS NULL AND b.external_id IS NULL))
                      AND a.id > b.id
                    """
                ).format(t=sql.Identifier(table))
            )
            deleted = cr.rowcount
            if deleted:
                _logger.info(
                    "geofolia_json_import: Removed %s duplicate row(s) from %s",
                    deleted,
                    table,
                )
        except Exception as e:
            _logger.warning(
                "geofolia_json_import: Could not clean duplicates in %s: %s",
                table,
                e,
            )
