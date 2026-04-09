Base module for those modules that manage a territorial census.

Functionality:

* Management of a census of territories (parcels, properties).
* Management of a census of "owners" and partner links.
* Integration with GIS functionalities (PostGIS, GIS viewer).
* **Use Types** (ter.use_type): hierarchical classification for territorial units.
  Includes kanban view with color badges, stat-buttons to navigate related
  units, parcels, and date ranges. Use-type catalog loaded from XML data
  via a dedicated import wizard.
* **Date Ranges** (date.range): campaign periods for territorial units with
  kanban view, form view with stat-buttons, and list view.
* **Territorial Units** (ter.use_unit): unit uses with chatter, notes,
  followers, state (draft/validated), validity_state. Kanban (default),
  list, form, pivot views. GIS viewer, archive, validate.
