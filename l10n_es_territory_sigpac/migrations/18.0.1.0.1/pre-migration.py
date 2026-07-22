# Copyright 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

XMLID_RENAMES = [
    (
        "l10n_es_territory_sigpac.ter_sigpac_view_tree",
        "l10n_es_territory_sigpac.ter_sigpac_view_list",
    ),
    (
        "l10n_es_territory_sigpac.ter_parcel_sigpaclink_view_tree",
        "l10n_es_territory_sigpac.ter_parcel_sigpaclink_view_list",
    ),
    (
        "l10n_es_territory_sigpac.ter_parcel_sigpaclink_only_parcels_view_tree",
        "l10n_es_territory_sigpac.ter_parcel_sigpaclink_only_parcels_view_list",
    ),
    (
        "l10n_es_territory_sigpac.ter_parcel_sigpaclink_only_enclosures_view_tree",
        "l10n_es_territory_sigpac.ter_parcel_sigpaclink_only_enclosures_view_list",
    ),
]


@openupgrade.migrate()
def migrate(cr, version):
    if not version:
        return
    cursor = cr.cr if hasattr(cr, "cr") else cr
    openupgrade.rename_xmlids(cursor, XMLID_RENAMES)
