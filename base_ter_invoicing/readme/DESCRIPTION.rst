Extension of the massive invoicing module (``base_invoicing``) to support
area-based billing for territorial parcels.

This module adds the concept of **overhead percentage** to parcel stakeholders,
allowing the allocation of costs proportional to the area each stakeholder
manages. The invoiced amount is calculated from the overhead percentage applied
to the total official area of the parcel.

Key capabilities:

* Assign an overhead percentage to each parcel partner link, determining the
  share of costs attributable to each stakeholder.
* Automatically compute the **ownership area** (for owners) and the **overhead
  area** based on the official parcel area and the assigned percentages.
* Integrate with the mass invoicing engine (``base_invoicing``) using parcel
  partner links as billable items, with area-based quantities.
* Display an **Invoiced** stat button on the parcel form, showing the total
  amount invoiced and linking to the related invoice lines.
* Add parcel reference fields (code, official code, property name) to invoice
  lines for easy traceability.
