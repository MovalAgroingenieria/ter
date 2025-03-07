.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===============================================
SIGPAC Integration for Water Users Associations
===============================================

Integration of the SIGPAC enclosures, and creation of a spatial link with
the parcels.

Description
===========

This module allows to link the parcels with the official SIGPAC enclosures,
using spatial functions of the PostGis extension of PostgreSql.

Functionality:

* Load of SIGPAC enclosures of each municipality.
* Automatic spatial calculation of the SIGPAC enclosures linked to parcels.
* Extraction of alphanumeric data from SIGPAC.

Requirements:

* Postgis extension installed in the database.
* Table "wua_gis_parcel" in the database.
* "ogr2ogr" installed in the system.
* "SHP Path" and "SHP Names" parameters with values.

Parameter Examples:

* SHP Path: /tmp
* SHP Names: rec_30016_2022_20220113.shp,rec_30030_2022_20220113.shp("poligono">=529 and "poligono"<=539),rec_30045_2022_20220113.shp

Credits
=======

* Moval Agroingeniería S.L.

Contributors
------------

* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Miguel Mora <mmora@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Jorge Vera <jvera@moval.es>

Maintainer
----------

.. image:: https://services.moval.es/static/images/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
