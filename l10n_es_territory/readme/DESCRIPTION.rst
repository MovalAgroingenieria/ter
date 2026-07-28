Customization of the territorial base (base_ter module) to the administrative scope of Spain.

Functionality:

* Add cadastral codes to provinces and municipalities.
* Manage official cadastral references for parcels.
* Add Spanish regions and provinces.
* Company-dependent configuration for Territory settings.
* Compare a parcel geometry with the official Cadastre (INSPIRE WFS): review
  the overlapping cadastral parcels on a map, optionally overwrite the parcel
  geometry with the cadastral one and fill the cadastral reference.
* Background scan (queue job) that suggests the best cadastral match for
  parcels that already have geometry.
