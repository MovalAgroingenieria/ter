.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=====================
Base Territory
=====================

**Table of contents**

.. contents::
   :local:

Description
===========

Base module for those modules that manage a territorial census.

Functionality:

* Management of a census of territories.
* Management of a census of "owners".
* Integration with GIS functionalities.
* **Use Types** (ter.use_type): hierarchical classification for territorial units
  (parcels, properties). Includes:

  - Kanban view with color badges (from Color Index field).
  - Stat-buttons to navigate to related Territorial Units (ter.unit),
    Parcels (ter.parcel), and Date Ranges (date.range).

* **Date Ranges** (date.range, when Usable for Unit Use): campaign periods for
  territorial units. Includes:

  - Kanban view with colors (from related Use Type).
  - Form view with stat-buttons to navigate to Territorial Units (ter.unit)
    and Parcels (ter.parcel).
  - Non-editable list view (edit via form only).
* **Territorial Units** (ter.unit): unit uses with chatter, notes, followers,
  state (draft/validated), validity_state. Name auto-generated from sequence
  (format: {type_code}-{date_start}-{date_end}-{parcel_code}-{sequence}).
  Kanban (default), list, form, pivot views. GIS viewer, archive, validate.
* Etc.

Installation
============

CREATE SCHEMA postgis;

CREATE EXTENSION postgis WITH SCHEMA postgis;

ALTER DATABASE <db_name> SET search_path = public, postgis;

GRANT USAGE ON SCHEMA postgis TO public;

GRANT SELECT, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA postgis TO public;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA postgis TO public;
GRANT USAGE ON SCHEMA postgis TO DB_USER;
ALTER ROLE  DB_USER SET search_path = public, postgis;

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
   :target: http://moval.es
   :alt: Moval Agroingeniería S.L.

This module is maintained by Moval Agroingeniería S.L.