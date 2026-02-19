.. Copyright 2026 Moval Agroingeniería S.L.
.. License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========================================
Territory Analytic - Geofolia Import
=========================================

**Table of contents**

.. contents::
   :local:

Description
===========

This module imports Geofolia JSON exports into Odoo, mapping data to
**OCA Field Service** (``fsm.location``) and **base_ter** (``ter.use_unit``,
parcels, date ranges), plus ``product.product``, ``hr.employee``, and
``account.analytic.line``.

**JSON examples** (in ``examples/``):

* **Field.Json** — Geofolia "Fields" (plots): Id, Code, Name, HarvestYear,
  Area, City, Geography (WKT EPSG:25830), CropName, etc. One Field → one
  ``fsm.location`` and one ``ter.use_unit`` (1:1).
* **Action.Json** — Contains "Products" (supplies), "Employees", "Partners",
  "HarvestedProducts", "Equipments", "Activities". Products map to
  ``product.product``, Employees to ``hr.employee``, Activity employees to
  ``account.analytic.line``.
* **IdentificationCodes.json** — List of farm/titular identification codes
  (e.g. NIF/CIF); usable for partner or location grouping.

**Geofolia** is a field notebook for farmers: they record
what they do, what they apply (supplies/products), and where (plots/fields). The
import maps these to OCA Field Service locations and base_ter use units so that
orders, timesheets, or equipment can be linked to the same geography and campaign.

**OCA field-service modules that can help** (see
`OCA/field-service <https://github.com/OCA/field-service>`_):

* **fieldservice** (required) — Core: ``fsm.location``, ``fsm.order``, workers.
  Our import creates one ``fsm.location`` per Geofolia Field (plot). Optional
  use: create or link **fsm.order** for activities (e.g. sowing, treatments)
  on that location.
* **fieldservice_activity** — Actions to perform on service orders. Could align
  with Geofolia “Activities” (operation name, dates) so each activity type
  becomes an FSM activity template.
* **fieldservice_timesheet** — Timesheet on FSM orders. Complements our current
  mapping of activity employees → ``account.analytic.line``; could also post
  time to an order linked to the field/location.

**fsm.order creation (Activities):** One fsm.order per activity when applying
Full import. Location is resolved as: (1) first plot from activity CropZoneIds
(PlotId → ter.use_unit → fsm.location, requires Fields imported first), or
(2) company default ``geofolia_default_fsm_location_id``. Configure the default
in Configuration → Territory → Geofolia if plots are not yet imported.

* **fieldservice_equipment_*** — If Geofolia Equipments are to be tracked as
  FSM equipment on locations, adding one of these modules allows linking
  equipment to the same ``fsm.location`` we create from Fields.

The module depends on **fieldservice**, **fieldservice_activity**,
**fieldservice_account**, **fieldservice_vehicle**, and
**fieldservice_timesheet** (timesheet lines linked to fsm.order).

Import modes:

* **Fields (Plots)** — Parse ``Fields`` array; apply creates/updates
  ``fsm.location`` and ``ter.use_unit`` (1:1), with geometry and company
  defaults (parcel, date range).
* **Products (Supplies)** — Parse ``Products`` into simple lines (no apply
  to product.product in this mode; use Full for that).
* **Full (All blocks)** — Parse Products, Employees, Partners, HarvestedProducts,
  Equipments, Activities; apply creates/updates products, employees,
  analytic lines, etc.

Linkage to OCA Field Service and base_ter
==========================================

**Current mapping (Fields mode)**

* **Geofolia Field** (one JSON object with Id, Code, Name, Area, City,
  Geography, HarvestYear, …) →

  * **fsm.location** (OCA `fieldservice <https://github.com/OCA/field-service>`_):
    ``partner_id`` / ``owner_id`` from a created ``res.partner`` (name, city),
    ``ter_use_unit_id`` (required, 1:1). ``geofolia_external_id`` is related from
    ``ter_use_unit_id.geofolia_external_id``.

  * **ter.use_unit** (base_ter): ``parcel_id`` (from geometry via
    ``_get_parcel_from_geometry`` or company default),
    ``date_range_id`` (from HarvestYear or company default),
    ``date_start`` / ``date_end``, ``area_official``, ``name``, ``geom_ewkt``,
    ``geofolia_external_id``, ``fsm_location_id``.

  * Bidirectional link: ``fsm.location.ter_use_unit_id`` ↔ ``ter.use_unit.fsm_location_id`` (1:1).

**What is correct**

* 1:1 between ``fsm.location`` and ``ter.use_unit`` is consistent and
  appropriate for “one Geofolia plot = one FSM location = one territorial use unit”.
* Use of company defaults (``geofolia_default_parcel_id``, ``geofolia_default_date_range_id``)
  when geometry or harvest year is missing.
* Geometry: Geofolia Geography is WKT in EPSG:25830 (ETRS89 / UTM 30N), aligned
  with base_ter (PostGIS SRID 25830).
* Products/Employees/Activities: ``geofolia_external_id`` on product, hr.employee,
  and account.analytic.line avoids duplicates and allows idempotent apply.
* Activity employees → ``account.analytic.line`` (name, date, unit_amount, employee_id)
  for timesheet/analytic tracking.

**Activities and timesheet (activity_line_ids / activity_employee_line_ids)**

* **Current imputation**: Employee hours (activity_employee_line_ids) are applied
  to **``account.analytic.line``** (analytic/timesheet lines). Activity headers
  (activity_line_ids) are not mapped to any model; they only group employee lines
  in the job.
* **Field Service link**: The OCA
  `fieldservice_timesheet <https://github.com/OCA/field-service/tree/18.0/fieldservice_timesheet>`_
  module adds **``fsm_order_id``** to ``account.analytic.line`` (Many2one to
  ``fsm.order``) and **``timesheet_ids``** to ``fsm.order`` (One2many to
  ``account.analytic.line``), so imputed time can be shown on the FSM order.
* **Recommendation**: To have Geofolia hours appear on FSM orders, install
  **fieldservice_timesheet** (depends on **hr_timesheet** and
  **fieldservice_project**). When ``account.analytic.line`` has ``fsm_order_id``,
  this module can create one **fsm.order** per activity (using the default
  location set in Geofolia settings) and link each analytic line to that order.
* **Flow with fieldservice_timesheet**:

  * Activity (Geofolia) → **fsm.order** (work order), one per activity.

  * Activity employee (hours) → **account.analytic.line** with **fsm_order_id**
    set so time appears on the order’s Timesheet tab.

**What to verify (proposal, no change done here)**

* **OCA fieldservice form view**: The view inheritance uses
  ``//group[@id='main-right']`` to add Geofolia ID and Territory Use Unit on
  ``fsm.location``. Confirm that this ``id`` exists in the OCA 18.0 form
  (see `fieldservice/fsm_location <https://github.com/OCA/field-service/tree/18.0/fieldservice>`_).
  If not, switch to a stable selector (e.g. by ``name`` of a field).
* **Municipality**: Geofolia Field has ``City`` and ``CityNumber``. base_ter
  has ``res.municipality``. Optionally map City/CityNumber to ``res.municipality``
  (e.g. by name or by an external code) and set ``ter.use_unit``’s municipality
  (if base_ter or an extension exposes it on the unit) or leave it derived from
  parcel.
* **Partners**: Geofolia has ``FarmIdentificationCode`` and Partners block.
  Currently FSM location gets a new ``res.partner`` per field (name, city).
  If Partners are imported, consider reusing or linking that partner for
  ``fsm.location.partner_id`` when the field’s farm code matches.
* **IdentificationCodes.json**: Not yet used by the importer. Could be used to
  pre-create or match ``res.partner`` (e.g. by VAT or custom code) or to
  filter/validate which fields belong to which organisation.

**Summary**

The linkage between Geofolia Fields → ``fsm.location`` and ``ter.use_unit``
is coherent with OCA Field Service and base_ter. The main improvement areas
are: stable view xpath for FSM location form, optional municipality and
partner mapping from Geofolia, and possible use of IdentificationCodes for
partners or filtering.

Structure
=========

**Python**

* **models**

  * ``import_job.py`` — ``geofolia.import.job`` (parse + apply).
  * ``geofolia_import_base_line.py`` — Base and full-mode line models: product, employee,
    partner, harvested product, equipment, activity, activity employee.
  * ``geofolia_import_line.py`` — Field/Product simple lines (Fields mode).
  * ``geofolia_product_product.py`` — ``product.product`` + ``geofolia_external_id``.
  * ``geofolia_hr_employee.py`` — ``hr.employee`` + ``geofolia_external_id``.
  * ``geofolia_res_partner.py`` — ``res.partner`` + ``geofolia_external_id``.
  * ``geofolia_fsm_person.py`` — ``fsm.person`` + ``geofolia_external_id`` (activity workers).
  * ``geofolia_fsm_equipment.py`` — ``fsm.equipment`` + ``geofolia_external_id``.
  * ``geofolia_fsm_order.py`` — ``fsm.order`` extensions for activities.
  * ``geofolia_account_analytic_line.py`` — ``account.analytic.line`` + ``geofolia_external_id``.
  * ``geofolia_fsm_location.py`` — ``fsm.location`` + ``ter_use_unit_id`` (required),
    ``geofolia_external_id`` (related from ter.use_unit).
  * ``geofolia_ter_use_unit.py`` — ``ter.use_unit`` + ``geofolia_external_id``, ``fsm_location_id``.
  * ``res_company.py`` — ``res.company`` Geofolia defaults (parcel, date range).
  * ``res_config_settings.py`` — Settings for those defaults.
* **wizards**
  * ``import_wizard.py`` — ``geofolia.import.wizard`` (upload JSON, create job, parse).

**XML**

* ``security/security.xml`` — Group Geofolia Import.
* ``security/ir.model.access.csv`` — Access rights.
* ``views/import_job_views.xml`` — Job list/form, menus, wizard action.
* ``views/geofolia_import_line_views.xml`` — Field/Product line views.
* ``views/geofolia_import_*_line_views.xml`` — Full-mode line views (product, employee,
  partner, harvested product, equipment, activity, activity employee).
* ``views/import_wizard_views.xml`` — Wizard form.
* ``views/fsm_location_views.xml`` — fsm.location form inheritance (Geofolia ID, ter.use_unit).
* ``views/geofolia_fsm_equipment_views.xml`` — fsm.equipment form inheritance.
* ``views/ter_use_unit_views.xml`` — ter.use_unit form inheritance (Geofolia ID, FSM location).
* ``views/geofolia_external_id_views.xml`` — Geofolia external ID field views.
* ``views/res_config_settings_views.xml`` — Geofolia defaults block in settings.

Installation
============

#. Install **OCA fieldservice** (see `OCA/field-service <https://github.com/OCA/field-service>`_).
#. Install **base_ter**, **analytic**, **account**, **hr**, **product** (and optionally
   **base_ter_analytic** if you use analytic account on use units).
#. Install **ter_analytic_geofolia**.
#. In Configuration → Territory (base_ter) → Geofolia, set default parcel and
   default date range for Fields import when geometry or harvest year is missing.
   If you use **fieldservice_timesheet**, set also the default FSM location for
   Activities so that activity times are linked to an fsm.order.
#. Use “New Import” to upload a Geofolia JSON (Field.Json, Action.Json, or full
   export), choose type (Fields / Products / Full), then Parse and Apply.

Credits
=======

* Moval

Contributors
------------

* Guillermo Amante <gamante@moval.es>
* Samuel Fernández <sfernandez@moval.es>
* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Jesús Martínez <jmartinez@moval.es>
* Miguel Mora <mmora@moval.es>
* Miguel Ángel Rodríguez <marodriguez@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Jorge Vera <jvera@moval.es>
* César Andrés <candres@moval.es>

Maintainer
----------

.. image:: https://services.moval.es/static/images/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval

This module is maintained by Moval.
