# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Base Territory Data Import",
    "summary": "Loads territory data (profiles, use types, attributes) from CSV files",
    "version": "18.0.1.0.0",
    "category": "Territory Management",
    "website": "https://www.moval.es",
    "author": "Moval Agroingeniería S.L.",
    "license": "AGPL-3",
    "post_init_hook": "post_init_hook",
    "depends": [
        "base_ter",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "wizards/wizard_import_catalog_csv_views.xml",
    ],
}
