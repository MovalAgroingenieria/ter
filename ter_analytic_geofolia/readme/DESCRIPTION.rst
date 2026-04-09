This module imports **Geofolia** JSON exports into Odoo, mapping field-notebook
data to **OCA Field Service** locations, **base_ter** territorial use units,
products, employees, and analytic lines.

`Geofolia <https://www.geofolia.fr/>`_ is a field notebook for farmers where
they record plots, crop operations, supplies applied, and labour. This module
bridges that data into Odoo so it can be exploited for analytics, field service
management, and territorial tracking.

Key features:

* **Three import modes**:

  * *Fields (Plots)* — Creates/updates one ``fsm.location`` and one
    ``ter.use_unit`` per Geofolia field (1:1), including geometry (WKT
    EPSG:25830), crop name, area, harvest year, and automatic parcel resolution
    via PostGIS spatial intersection.
  * *Products (Supplies)* — Parses supply lines for review before applying.
  * *Full (All blocks)* — Parses and applies Products, Employees, Partners,
    Harvested Products, Equipments, and Activities with their employee hours.

* **Idempotent apply** — Every imported entity carries a
  ``geofolia_external_id``; re-importing the same JSON updates existing records
  instead of creating duplicates.

* **GIS integration** — Field geometries are matched against cadastral parcels
  via PostGIS ``ST_Intersection`` to automatically assign the best-overlapping
  parcel to each use unit.

* **Activity → Analytic lines + FSM orders** — Each activity creates an
  ``fsm.order`` on the resolved location, and each activity employee line
  becomes an ``account.analytic.line`` (timesheet) linked to that order.

* **Date range / campaign resolution** — Harvest years from Geofolia are
  matched to ``date.range`` periods, with company-level defaults as fallback.

* **Import wizard** with automatic JSON type detection (Fields, Products, Full)
  and batch processing support.
