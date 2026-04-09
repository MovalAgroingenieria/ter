After installation, configure the Geofolia defaults:

#. Go to **Settings > Territory > Geofolia**.
#. Set the **Default parcel** — used when a field's geometry does not intersect
   any known cadastral parcel.
#. Set the **Default period** (date range) — used when the harvest year from
   Geofolia does not match any existing ``date.range``.
#. Optionally set the **Default FSM location** — used for activities when the
   activity's plot has not been imported yet.

These defaults ensure the import can proceed even when geometry or date
information is incomplete.
