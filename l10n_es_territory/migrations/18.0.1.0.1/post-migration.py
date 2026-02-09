# Copyright 2024-2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

"""Add mapped_to_polygon column to base_adi tables if missing.

res.admregion, res.province and res.municipality inherit polygon.model which
defines mapped_to_polygon (store=True). If base_adi was installed before
polygon.model had this field stored, or the DB was restored without the column,
this migration adds it.
"""

import logging

from psycopg2 import sql

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    for table in ("res_admregion", "res_province", "res_municipality"):
        try:
            cr.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = 'mapped_to_polygon'
                """,
                (table,),
            )
            if cr.fetchone():
                continue
            cr.execute(
                sql.SQL(
                    "ALTER TABLE {} ADD COLUMN mapped_to_polygon BOOLEAN DEFAULT FALSE"
                ).format(sql.Identifier(table))
            )
            _logger.info(
                "l10n_es_territory: Added mapped_to_polygon column to %s", table
            )
        except Exception as e:
            _logger.warning(
                "l10n_es_territory: Could not add mapped_to_polygon to %s: %s",
                table,
                e,
            )
