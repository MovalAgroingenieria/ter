# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    'name': 'Base-Territory (Spanish Localization)',
    'summary': 'Customization of the territorial base (base_ter module) '
               'to the administrative scope of Spain.',
    'version': '16.0.1.0.0',
    'author': 'Moval Agroingeniería',
    'license': 'AGPL-3',
    'website': 'https://moval.es',
    'category': 'Territory Management',
    'depends': [
        'base_ter',
    ],
    'data': [
        'data/res_admregion_data.xml',
        'data/res_province_data.xml',
        'views/res_province_views.xml',
        'views/res_municipality_views.xml',
        'views/ter_parcel_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'l10n_es_territory/static/src/scss/l10n_es_territory.scss',
        ]
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
