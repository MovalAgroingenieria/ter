# Technical Proposals – base_ter / ter.unit

Review of technical proposals from the territorial unit use specification, applied to base_ter.

## Applied Changes

| Prop | Description |
|------|-------------|
| C2 | Explicit indexes on ter.unit: parcel_id, date_start, date_end, use_type_id |
| C3 | is_current field on ter.unit (store=True) + view filters |
| C4 | unlink restriction: forbid deleting ter.unit when it has GIS geometry |
| C5 | _check_domain_specific_rules() hook for extensions |
| C7 | Proposals documentation |

## Not Applied

- **C1** (UNIQUE alphanum_code): May fail if duplicates exist.
- **C6** (Fix _check_required_attributes): May change validation behaviour.
