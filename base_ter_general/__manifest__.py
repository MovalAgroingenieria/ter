# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Base-Territory General Mapping Module",
    "summary": "Synchronization of partners and parcels with base entities.",
    "version": "18.0.1.0.0",
    "category": "Territory Management",
    "website": "https://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "uninstall_hook": "uninstall_hook",
    "depends": [
        "base_ter",
        "queue_job",
    ],
    "data": [
        "data/base_ter_general_cron.xml",
        "views/ter_parcel_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "base_ter_general/static/src/scss/base_ter_general.scss",
        ],
    },
}
