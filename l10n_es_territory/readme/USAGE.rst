Compare a parcel with the Cadastre
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Make sure **Enable parcel geometry import from Cadastre** is on in
   *Settings > Territory* and, optionally, set the **Cadastre match minimum
   overlap (%)** used by the background scan.
#. Open a parcel that already has a geometry and click **Compare Cadastre**.
   The wizard queries the official Cadastre WFS for the overlapping cadastral
   parcels and shows them on a map (the parcel geometry in red, the cadastral
   candidates in blue, the selected one in green).
#. The cadastral parcel with the greatest overlap is pre-selected; click any
   parcel on the map to choose a different one.
#. Use **Overwrite geometry** to replace the parcel geometry with the
   selected cadastral one (the cadastral reference is also filled when it is
   empty), or **Fill cadastral reference only** to keep the geometry.

Background scan
~~~~~~~~~~~~~~~

From the parcels list, select several parcels and run **Scan Cadastre
(background)**. A queue job is created per parcel; it stores the best
cadastral match (reference and overlap percentage) so the parcels can be
triaged with the *Cadastre: Suggestion available* filter and reviewed one by
one in the comparison wizard. The scan never blocks and never fails the
records it processes.
