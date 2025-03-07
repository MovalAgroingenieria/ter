# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: SIGPAC Integration",
    "summary": "In a water users association, integration of the SIGPAC "
               "enclosures, and creation of a spatial link with the parcels.",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure",
        "base_extra_gis",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/wua_config_settings_data.xml",
        "data/wua_parcel_sigpaclink_cron.xml",
        "views/resources.xml",
        "views/wua_config_settings_view.xml",
        "views/wua_sigpac_view.xml",
        "views/wua_parcel_view.xml",
        "reports/wua_parcel_sigpac_report.xml",
    ],
    "installable": True,
    "pre_init_hook": "pre_init_hook",
    "uninstall_hook": "uninstall_hook",
    "application": False,
}
