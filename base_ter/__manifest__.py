# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Base-Territory Module",
    "summary": "Base module for those modules that manage a territorial census",
    "version": "16.0.1.0.0",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "website": "https://moval.es",
    "category": "Territory Management",
    "depends": [
        'mail',
        'contacts',
        'web_progress',
        'base_gen',
        'base_gis',
        'base_adi',
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ter_profile_data.xml",
        "wizards/wizard_set_parcel_code_views.xml",
        "wizards/wizard_set_partner_code_views.xml",
        "views/base_ter_menus.xml",
        "views/res_config_settings_views.xml",
        "views/ter_parcel_views.xml",
        "views/ter_property_views.xml",
        "views/ter_parceltag_views.xml",
        "views/res_partner_views.xml",
        "views/ter_profile_views.xml",
        "views/ter_propertytag_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "base_ter/static/src/scss/base_ter.scss",
        ]
    },
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
}
