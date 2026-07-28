# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Base Point",
    "summary": "Management of geolocated point-based entity censuses",
    "version": "18.0.1.0.0",
    "category": "Point Management",
    "website": "https://www.moval.es",
    "author": "Moval Agroingenieria S.L.",
    "license": "AGPL-3",
    "installable": True,
    "post_init_hook": "post_init_hook",
    "depends": [
        "mail",
        "contacts",
        "base_gen",
        "base_gis",
        "base_gis_viewer",
        "base_adi",
    ],
    "data": [
        "security/point_security.xml",
        "security/ir.model.access.csv",
        "data/point_profile_data.xml",
        "wizards/wizard_set_point_code_views.xml",
        "views/point_menus.xml",
        "views/res_config_settings_views.xml",
        "views/point_point_views.xml",
        "views/point_pointtag_views.xml",
        "views/point_profile_views.xml",
        "views/res_partner_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "base_point/static/lib/point_iconset/iconset.css",
        ],
        "web.assets_frontend": [
            "base_point/static/lib/point_iconset/iconset.css",
        ],
        "web.report_assets_common": [
            "base_point/static/lib/point_iconset/iconset.css",
        ],
    },
}
