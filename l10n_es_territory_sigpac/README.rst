.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============================================
SIGPAC Integration for Territory
===============================================

This module integrates SIGPAC enclosures and creates a spatial link with
Territory parcels.

Description
===========

This module links parcels with the official SIGPAC enclosures using spatial
functions provided by the PostGIS extension of PostgreSQL.

Main features:

* Import of SIGPAC enclosure geometries from official shapefiles.
* Automatic spatial calculation of SIGPAC enclosures linked to parcels.
* Extraction of SIGPAC alphanumeric data and visualization shortcuts.

Requirements
============

* PostGIS extension installed in the database.
* Table ``ter_gis_parcel`` available in the database (parcels must be mapped to GIS).
* ``ogr2ogr`` installed on the server.
* SIGPAC settings configured at company level.

Configuration
=============

The configuration is available in *Settings > Territory* (``base_ter`` app).
All parameters are company-specific.

* **SIGPAC shapefiles path**: e.g. ``/tmp``
* **SIGPAC shapefiles names**: comma-separated list of shapefiles.
  Optionally, each file may include a filter expression using parentheses.

Example:

* ``rec_30016_2022_20220113.shp``
* ``rec_30030_2022_20220113.shp("poligono">=529 and "poligono"<=539)``
* ``rec_30045_2022_20220113.shp``

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
