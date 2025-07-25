# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{

    'name': 'Base-Territory Module',
    'summary': 'Base module for those modules that manage a territorial census',
    'version': '16.0.1.0.0',
    'category': 'Territory Management',
    'website': 'https://www.moval.es',
    'author': 'Moval Agroingeniería',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'depends': [
        'mail',
        'contacts',
        'web_progress',
        'web_tree_many2one_clickable',
        'base_gen',
        'base_gis',
        'base_adi',
        'base_report',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ter_profile_data.xml',
        'data/base_ter_cron.xml',
        'wizards/wizard_set_parcel_code_views.xml',
        'wizards/wizard_set_partner_code_views.xml',
        'wizards/wizard_show_gis_preview_views.xml',
        'views/base_ter_menus.xml',
        'views/res_config_settings_views.xml',
        'views/ter_parcel_views.xml',
        'views/ter_property_views.xml',
        'views/ter_parceltag_views.xml',
        'views/res_partner_views.xml',
        'views/ter_profile_views.xml',
        'views/ter_propertytag_views.xml',
        'views/ter_gis_parcel_model_views.xml',
        'reports/property_partner_report.xml',
        'reports/parcel_partner_report.xml',
        'reports/parcel_report.xml',
        'reports/property_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'base_ter/static/src/scss/base_ter.scss',
            'base_ter/static/src/css/base_ter.css',
            'base_ter/static/lib/ter_iconset/iconset.css',
            'base_ter/static/src/js/base_ter_parcel_kanban_controller.js',
        ],
        'web.assets_frontend': [
            'base_ter/static/lib/ter_iconset/iconset.css',
        ],
        'web.report_assets_common': [
            'base_ter/static/lib/ter_iconset/iconset.css',
        ],
    },
    'external_dependencies': {
        'python': [
            'pycryptodome',
        ],
    },

}
