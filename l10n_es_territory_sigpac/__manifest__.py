# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Territory: SIGPAC Integration",
    "summary": "In a territorial census, integration of the SIGPAC "
               "enclosures, and creation of a spatial link with the parcels.",
    "version": '16.0.1.0.0',
    "category": "Territory Management",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_ter",
        "l10n_es_territory",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ter_parcel_sigpaclink_cron.xml",
        "views/res_config_settings_view.xml",
        "views/ter_sigpac_view.xml",
        "views/ter_parcel_view.xml",
        "reports/ter_parcel_sigpac_report.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_es_territory_sigpac/static/src/css/l10n_es_territory_sigpac.css",
        ],
    },
    "installable": True,
    "pre_init_hook": "pre_init_hook",
    "uninstall_hook": "uninstall_hook",
    "application": False,
}
