# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
"""Pre-migration for base_ter 18.0.1.5.0.

Rename legacy primary list view xml_ids from *_view_tree to *_view_list
while preserving the same res_id to avoid duplicate ir.ui.view records.
"""

from openupgradelib import openupgrade

_XMLID_RENAMES = [
    ("base_ter.res_partner_view_tree", "base_ter.res_partner_view_list"),
    ("base_ter.ter_parcel_view_tree", "base_ter.ter_parcel_view_list"),
    (
        "base_ter.ter_parcel_partnerlink_view_tree",
        "base_ter.ter_parcel_partnerlink_view_list",
    ),
    (
        "base_ter.ter_propertytag_view_tree",
        "base_ter.ter_propertytag_view_list",
    ),
    (
        "base_ter.ter_gis_parcel_model_view_tree",
        "base_ter.ter_gis_parcel_model_view_list",
    ),
    ("base_ter.ter_parceltag_view_tree", "base_ter.ter_parceltag_view_list"),
    ("base_ter.ter_property_view_tree", "base_ter.ter_property_view_list"),
    ("base_ter.ter_profile_view_tree", "base_ter.ter_profile_view_list"),
]


@openupgrade.migrate()
def migrate(cr, version):
    cursor = cr.cr if hasattr(cr, "cr") else cr
    openupgrade.rename_xmlids(cursor, _XMLID_RENAMES)
