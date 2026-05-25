.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============
Territory & GIS
===============

Odoo addons for territorial census management and GIS integration.

**Table of contents**

.. contents::
   :local:

Overview
========

This repository contains modules for:

* **base_ter**: Base territory module (parcels, properties, units, GIS)
* **base_ter_general**: Partner and parcel synchronization
* **base_ter_invoicing**: Territory invoicing
* **l10n_es_territory**: Spain - administrative divisions, cadastre
* **l10n_es_territory_sigpac**: Spain - SIGPAC integration
* **geofolia_json_import**: Geofolia JSON import (Fields/Products)
* **sms_wausms_ter**: SMS integration for territory

Requirements
============

* PostGIS extension for PostgreSQL
* Odoo 18.0
* Dependencies: base_gis, base_adi, base_gen, date_range (see each module)

Installation
============

1. Install PostGIS:

   .. code-block:: sql

      CREATE SCHEMA postgis;
      CREATE EXTENSION postgis WITH SCHEMA postgis;
      ALTER DATABASE <db_name> SET search_path = public, postgis;
      GRANT USAGE ON SCHEMA postgis TO public;
      GRANT SELECT, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA postgis TO public;
      GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA postgis TO public;

2. Install the addons path and update the module list.

Configuration
=============

* Configure GIS viewer URL, WMS endpoints and credentials in
  Settings > Territory
* For Spain: install l10n_es_territory for provinces/municipalities
* For SIGPAC: install l10n_es_territory_sigpac

Territory units (ter.unit) with geometry
========================================

When a ter.unit has a geometry (EWKT in ``geom_ewkt``, e.g. ``SRID=25830;POLYGON((...))``),
the parcel is automatically assigned as the parcel with **maximum overlap** using PostGIS
``ST_Intersects`` and ``ST_Area(ST_Intersection(...))``. The geometry is stored in the
``ter_gis_unit`` table for spatial operations.

Credits
=======

Authors
-------

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

.. image:: https://raw.githubusercontent.com/MovalAgroingenieria/public-assets/master/logos/logo_moval_small.png
   :target: https://moval.es
   :alt: Moval Agroingeniería S.L.

This module is maintained by Moval Agroingeniería S.L.
