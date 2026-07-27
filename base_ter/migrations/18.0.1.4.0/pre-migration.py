# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
"""Pre-migration for base_ter 18.0.1.4.0.

OCA compliance: primary view xml_ids are renamed from the legacy
``view_<name>`` form to the ``<model>_view_<type>`` form. Renaming the
metadata (instead of letting the loader recreate the views) keeps the same
``res_id`` and prevents duplicate ``ir.ui.view`` records on already-installed
databases. External references (dependent modules' ``inherit_id``) are updated
in their own XML.
"""

from openupgradelib import openupgrade

_XMLID_RENAMES = [
    ("base_ter.view_ter_unit_list", "base_ter.ter_use_unit_view_list"),
    ("base_ter.view_ter_unit_form", "base_ter.ter_use_unit_view_form"),
    ("base_ter.view_ter_unit_kanban", "base_ter.ter_use_unit_view_kanban"),
    ("base_ter.view_ter_unit_pivot", "base_ter.ter_use_unit_view_pivot"),
    ("base_ter.view_ter_unit_filter", "base_ter.ter_use_unit_view_search"),
    ("base_ter.view_ter_unit_graph", "base_ter.ter_use_unit_view_graph"),
    ("base_ter.view_ter_unit_calendar", "base_ter.ter_use_unit_view_calendar"),
    (
        "base_ter.view_ter_unit_report_pivot",
        "base_ter.ter_use_unit_report_view_pivot",
    ),
    (
        "base_ter.view_ter_unit_attribute_value_list",
        "base_ter.ter_unit_attribute_value_view_list",
    ),
    (
        "base_ter.view_ter_unit_attribute_value_form",
        "base_ter.ter_unit_attribute_value_view_form",
    ),
    ("base_ter.view_date_range_kanban", "base_ter.date_range_view_kanban"),
    ("base_ter.view_date_range_pivot", "base_ter.date_range_view_pivot"),
    ("base_ter.view_date_range_graph", "base_ter.date_range_view_graph"),
    ("base_ter.view_date_range_calendar", "base_ter.date_range_view_calendar"),
    ("base_ter.view_use_type_list", "base_ter.ter_use_type_view_list"),
    ("base_ter.view_use_type_form", "base_ter.ter_use_type_view_form"),
    ("base_ter.view_use_type_kanban", "base_ter.ter_use_type_view_kanban"),
    ("base_ter.view_use_type_search", "base_ter.ter_use_type_view_search"),
    (
        "base_ter.view_use_type_attribute_form",
        "base_ter.ter_use_type_attribute_view_form",
    ),
    (
        "base_ter.wizard_show_gis_preview_views",
        "base_ter.wizard_show_gis_preview_view_form",
    ),
]


@openupgrade.migrate()
def migrate(cr, version):
    cursor = cr.cr if hasattr(cr, "cr") else cr
    openupgrade.rename_xmlids(cursor, _XMLID_RENAMES)
