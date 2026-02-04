# Copyright 2024-2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Spain - Territory",
    "summary": "Customization of the territorial base (base_ter module) "
    "to the administrative scope of Spain.",
    "version": "18.0.1.0.0",
    "author": "Moval Agroingeniería S.L.",
    "license": "AGPL-3",
    "website": "https://moval.es",
    "category": "Territory Management",
    "depends": [
        "base_ter",
    ],
    "data": [
        "data/res_admregion_data.xml",
        "data/res_province_data.xml",
        "views/res_province_views.xml",
        "views/res_municipality_views.xml",
        "views/ter_parcel_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_es_territory/static/src/scss/l10n_es_territory.scss",
        ]
    },
    "post_init_hook": "post_init_hook",
    "external_dependencies": {
        "python": ["requests"],
    },
}
