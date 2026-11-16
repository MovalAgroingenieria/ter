To use this module:

#. Go to **Census > Geofolia > New Import** and upload a Geofolia JSON file
   (``Field.Json``, ``Action.Json``, or a full export combining both).
#. The wizard auto-detects the file type. Confirm and click **Import**.
#. A new import record is created and the JSON is parsed into intermediate
   lines. You can browse all imports from **Census > Geofolia > Imports**.
#. Review the parsed lines in the import form (Fields, Products, Employees,
   etc.) or use the **Import Lines** menu for a global view.
#. Click **Apply All** to create or update the corresponding Odoo records:

   * *Fields mode*: Creates ``fsm.location`` + ``ter.use_unit`` per plot.
     Geometry is used to resolve the best-matching cadastral parcel via PostGIS.
   * *Full mode*: Creates/updates ``product.product``, ``hr.employee``,
     ``res.partner``, ``fsm.equipment``, ``fsm.order``, and
     ``account.analytic.line`` records.

#. Individual lines can also be applied selectively using the **Apply Selected**
   action on each line list.
#. Re-importing the same JSON file updates existing records (matched by
   ``geofolia_external_id``) rather than creating duplicates.

Import Review
~~~~~~~~~~~~~

Performed activities (``ZK2``) create work orders even without workers.
Materials, machinery, harvests and worked crop units are imported independently
of employee times. Forecast activities (``ZK1``) do not create work orders, and
no employee hours are invented for workerless activities.

Analytic entries use the company-configured Geofolia analytic account first.
Without that configuration, only a single unambiguous account from the order's
actual crop units can be used. Otherwise the employee line records an incident;
the order and its consumptions remain available. No arbitrary account is chosen.

Use **Geofolia > Crop Mappings** to review source crop names and select their
Odoo equivalents. A unique matching leaf crop is reused automatically, including
the aliases ``ORDI`` / ``CEBADA`` and ``ALFALS`` / ``ALFALFA``. Uncertain names
remain pending review; ``FEINES TERCERS`` is classified as **Not a Crop**.
Unknown crops do not receive the configured default crop, and existing crop
assignments are not overwritten. Saving a mapping does not update historical
units automatically; apply the corresponding field import again to fill units
without an assigned crop.

Original Geofolia sowing and harvest dates remain visible alongside the applied
territorial dates. **Adjusted Dates** and **Pending Review** filters identify
discrepancies. The importer may adapt territorial dates to the selected campaign,
but it does not change campaign boundaries.

Original Consumptions
~~~~~~~~~~~~~~~~~~~~~

Work orders retain their aggregated consumption lists and also expose
**Original Consumptions**. Each source row keeps its original quantity, unit,
recognition ID, lot information and JSON payload. A crop unit and parcel are
linked only when the source identifies a unique unit. Ambiguous rows are retained
for review without automatic distribution or proration. The complete original
activity payload is also retained for future cost allocation.

After upgrading, use **Refresh Source Audit** on existing imports to recover
original dates, crop mapping review and consumption detail from their retained
JSON without uploading the ZIP again. This action does not change territorial
dates, campaign boundaries, assigned crops or aggregated consumptions. Reapply
pending activities separately to create previously missing workerless orders.
