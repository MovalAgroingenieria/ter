# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
"""Post-migration for base_ter 18.0.1.2.0.

Two data corrections needed only when upgrading an already-installed
``base_ter`` (a fresh install gets everything right from the data files
directly):

1. ``ter_parcel_cron_action_reset_all_aerial_images`` (ir.cron) already
   existed before this version with a different name/code (it used to
   run ``action_reset_all_aerial_images`` synchronously every week).
   Its data file is ``noupdate="1"``, so the XML update alone would
   leave the stale name/code in place. Force it to the new incremental,
   queue_job-based behaviour.

2. Backfill ``ter.parcel.aerial_image_last_refresh`` for parcels that
   already have a stored aerial image, so the (inactive by default)
   incremental refresh cron does not treat every pre-existing parcel
   as "never refreshed" (highest priority) the first time it is enabled.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    _fix_stale_parcel_cron(env)
    _backfill_aerial_image_last_refresh(cr)


def _fix_stale_parcel_cron(env):
    # `ir.cron`'s `name`/`code` are delegated to `ir.actions.server`
    # (``ir_actions_server_id`` field, ``delegate=True``), so they must be
    # updated through the ORM rather than raw SQL on the `ir_cron` table.
    cron = env.ref(
        "base_ter.ter_parcel_cron_action_reset_all_aerial_images",
        raise_if_not_found=False,
    )
    if not cron:
        return
    cron.write(
        {
            "name": (
                "Territorial Base: Generate pending aerial images of the "
                "parcels (queue_job)"
            ),
            "code": "model.cron_generate_pending_aerial_images(batch_size=200)",
            "interval_number": 1,
            "interval_type": "weeks",
        }
    )
    _logger.info(
        "base_ter 18.0.1.2.0 migration: updated stale "
        "ter_parcel_cron_action_reset_all_aerial_images cron (id=%s)",
        cron.id,
    )


def _backfill_aerial_image_last_refresh(cr):
    # `aerial_image` is an attachment-stored Image field (no DB column);
    # `aerial_image_key` is only ever set alongside a successfully stored
    # image, so it is used here as the "already has an image" proxy.
    cr.execute("""
        UPDATE ter_parcel
        SET aerial_image_last_refresh = COALESCE(write_date, create_date, now())
        WHERE aerial_image_key IS NOT NULL
          AND aerial_image_key != ''
          AND aerial_image_last_refresh IS NULL
        """)
    _logger.info(
        "base_ter 18.0.1.2.0 migration: backfilled aerial_image_last_refresh "
        "for %s parcel(s)",
        cr.rowcount,
    )
