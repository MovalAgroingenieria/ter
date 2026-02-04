.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================
Geofolia import bridge
======================

**Table of contents**

.. contents::
   :local:

Description
===========

Import wizard and staging models to load Geofolia JSON exports into Odoo and
synchronize the data with Territory (parcels) and Timesheets.

Functionality
=============

* Import Geofolia JSON files in three modes:

  * *Fields (Plots)*: creates staging lines and maps them to ``ter.parcel``.
  * *Products (Supplies)*: creates staging lines for supplies.
  * *Full (All blocks)*: imports Products, Employees, Partners, Harvested Products,
    Equipments and Activities with employee imputations.

* Mapping of Geofolia Fields to ``ter.parcel`` using a persistent external id
  (``geofolia_external_id``).

* Creation and update of Odoo records from staging lines with per-line status:

  * *pending*, *skipped*, *created*, *updated*, *no_action*, *error*.

* Creation of analytic lines for activity employee imputations, linking them to a
  company-configured project and task (Timesheets), so they are visible in
  ``hr_timesheet``.

Credits
=======

* Moval Agroingeniería S.L.

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
   :target: https://www.moval.es
   :alt: Moval Agroingeniería S.L.

This module is maintained by Moval Agroingeniería S.L.
