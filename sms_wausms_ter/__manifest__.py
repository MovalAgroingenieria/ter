# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'SMS WauSMS Territory',
    'summary': 'SMS Text Messaging for Territory',
    'version': "17.0.1.0.0",
    'category': 'Tools',
    'website': 'https://www.moval.es',
    'author': 'Moval Agroingeniería',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'base_ter',
        'sms_wausms',
    ],
    'data_old': [
        'views/ter_parcel_views.xml',
        'views/ter_property_views.xml',
    ],
}
