# 2026 Moval Agroingenieria S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

XMLID_RENAMES = (
    ("res_municipality_view_tree", "res_municipality_view_list"),
    ("res_province_view_tree", "res_province_view_list"),
)


def migrate(cr, version):
    """Create compatibility xmlids for renamed inherited list views."""
    for old_name, new_name in XMLID_RENAMES:
        cr.execute(
            """
            SELECT model, res_id, noupdate
              FROM ir_model_data
             WHERE module = 'l10n_es_territory' AND name = %s
             LIMIT 1
            """,
            (old_name,),
        )
        row = cr.fetchone()
        if not row:
            continue

        model, res_id, noupdate = row

        cr.execute(
            """
            SELECT 1
              FROM ir_model_data
             WHERE module = 'l10n_es_territory' AND name = %s
             LIMIT 1
            """,
            (new_name,),
        )
        if cr.fetchone():
            continue

        cr.execute(
            """
            INSERT INTO ir_model_data
                (module, name, model, res_id, noupdate)
            VALUES
                ('l10n_es_territory', %s, %s, %s, %s)
            """,
            (new_name, model, res_id, noupdate),
        )
