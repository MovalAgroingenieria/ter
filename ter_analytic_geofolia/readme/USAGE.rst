To use this module:

#. Go to **Census > Geofolia > Import Jobs** and click **New Import**.
#. Upload a Geofolia JSON file (``Field.Json``, ``Action.Json``, or a full
   export combining both).
#. The wizard auto-detects the file type. Confirm and click **Import**.
#. A new import job is created and the JSON is parsed into intermediate lines.
#. Review the parsed lines in the job form (Fields, Products, Employees, etc.).
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
