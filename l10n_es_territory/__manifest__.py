# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Base-Territory (Spanish Localization)",
    "summary": "Customization of the territorial base (base_ter module) "
               "to the administrative scope of Spain.",
    "version": "16.0.1.0.0",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "website": "https://moval.es",
    "category": "Territory Management",
    "depends": [
        'base_ter',
    ],
    "data": [
        "views/res_province_views.xml",
        "views/res_municipality_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_es_territory/static/src/scss/l10n_es_territory.scss",
        ]
    },
    "installable": True,
    "application": False,
}
