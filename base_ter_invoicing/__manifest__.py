# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    'name': 'Area-based massive invoicing',
    'summary': 'Extension of the massive invoicing module (base_invoicing) '
               'to support area-based billing.',
    'version': "17.0.1.0.0",
    'category': 'Accounting/Accounting',
    'website': 'https://www.moval.es',
    'author': 'Moval Agroingeniería',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'depends': [
        'base_ter',
        'base_invoicing',
    ],
    'data': [
        'data/product_category_data.xml',
        'views/ter_parcel_views.xml',
        'views/account_move_line_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'base_ter_invoicing/static/src/scss/base_ter_invoicing.scss',
        ],
    },
}
