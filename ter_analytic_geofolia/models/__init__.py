# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# isort: skip_file
# Import order is significant: the abstract "geofolia.import.base.line" must load
# before the concrete models that inherit it, so do NOT alphabetically sort this file.

from . import geofolia_import_base_line
from . import (
    account_analytic_line,
    fsm_equipment,
    fsm_location,
    fsm_order,
    fsm_order_equipment_usage,
    fsm_order_person_usage,
    fsm_order_product_usage,
    fsm_person,
    geofolia_import_activity_employee_line,
    geofolia_import_activity_line,
    geofolia_import_employee_line,
    geofolia_import_equipment_line,
    geofolia_import_harvested_product_line,
    geofolia_import_job,
    geofolia_import_line,
    geofolia_import_partner_line,
    geofolia_import_product_line,
    hr_employee,
    product_product,
    res_company,
    res_config_settings,
    res_partner,
    ter_use_unit,
    timesheets_analysis_report,
)
