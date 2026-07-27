# Copyright 2024-2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

"""Cleanup obsolete res.config.settings inherited view.

Older l10n_es_territory versions injected fields
base_ter_aerial_image_wmsbase_* in settings. Those fields were removed, but the
inherited view could remain in restored databases and breaks registry loading.
"""


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        SELECT res_id
        FROM ir_model_data
        WHERE module = 'l10n_es_territory'
          AND name = 'res_config_settings_view_form_inherit_l10n_es_territory'
          AND model = 'ir.ui.view'
        """
    )
    view_ids = [row[0] for row in cr.fetchall()]

    if view_ids:
        cr.execute(
            """
            DELETE FROM ir_ui_view
            WHERE id = ANY(%s)
            """,
            (view_ids,),
        )
    else:
        cr.execute(
            """
            DELETE FROM ir_ui_view
            WHERE name = 'res.config.settings.view.form.inherit.l10n_es_territory'
              AND model = 'res.config.settings'
              AND arch_db::text ILIKE '%base_ter_aerial_image_wmsbase_url%'
            """
        )

    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'l10n_es_territory'
          AND name = 'res_config_settings_view_form_inherit_l10n_es_territory'
          AND model = 'ir.ui.view'
        """
    )
