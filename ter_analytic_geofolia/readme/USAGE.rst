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
