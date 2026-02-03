# Geofolia JSON Format Compatibility

## OCA Maintenance Integration

Uses OCA Maintenance modules (v18):
- **maintenance_project**: Maintenance project in `res.company.geofolia_maintenance_project_id`. Equipment and maintenance requests are linked to this project.
- **maintenance.equipment**: Geofolia Equipments → `maintenance.equipment` with `geofolia_equipment_id` (idempotency).
- **maintenance.request**: Geofolia Activities → `maintenance.request` with `geofolia_action_id` (idempotency).
- **maintenance_timesheet**: Employee times from ActivityEmployees → `account.analytic.line` with `maintenance_request_id`.
- **maintenance_request_employee**: Employees linked to `maintenance.request.employee_ids`.
- **maintenance_product**: Equipment can optionally link to `product.product` (maintenance_ok).

Philosophy: One Geofolia ID, import all data, add to views, Many2one, search before create, one class per file.

## Compatible Structures

### Fields (Units)
- **Required**: `Id`, `Code`, `Name`, `Area`, `City`, `Geography`
- **Optional**: `FarmIdentificationCode`, `HarvestYear`, `CropName`, `VarietyName`, `SowingDate`, `HarvestDate`
- **Extra captured**: `RNCropCode`, `BotanicalSpeciesCode`, `IrrigationKind`, `IrrigationKindName`, `CityNumber`
- **Geography**: WKT in EPSG:25830 (ETRS89/UTM 30N). SRID from `Information.CoordinateReferenceSystem` or 25830 default.
- **Area**: If `Unit` = "ha" use as-is; else assume m² and convert to ha.

### Activities (Actions) → maintenance.request
- **maintenance.request**: One per Activity, `geofolia_action_id` = ActionId (idempotency).
- **Project**: From `geofolia_maintenance_project_id` (or `geofolia_timesheet_project_id` fallback).
- **Tasks**: `OperationName` or `OperationCategory` → `project.task` in the maintenance project.
- **ActionEmployees** → `account.analytic.line` with `maintenance_request_id`, plus `employee_ids` on the request.
- **ActionEmployees** link to **CropZoneIds** via `EmployeeRecognitionId` = `CropZone.RecognitionId`.
- Each CropZone: `PlotCode`, `FarmIdentificationCode`, `WorkedSurface` (m²).
- Parcel resolution: (FarmIdentificationCode + PlotCode) or PlotCode or FarmIdentificationCode.
- Status: `StatusName`, `StatusCode`, `OperationCategory` stored in analytic line.

### Products
- **Extra captured**: `RecognitionId`, `ProductComponentNTotal`, `ProductComponentP2O5`, `ProductComponentK2O`
- Applied to `product.product` when creating/updating.

### Equipments → maintenance.equipment
- **geofolia_equipment_id** = EquipmentId (idempotency).
- **project_id** = `geofolia_maintenance_project_id`.
- **name** from Name or Code.

### Full Export Blocks
- `Products`, `Employees`, `Partners`, `HarvestedProducts`, `Equipments`, `Activities`
- `Information` with `CoordinateReferenceSystem` (EPSG:25830 or 4326 detected).
- Fields are not parsed in full mode (use import_type "fields" separately).

## Sample Files
- `tests/data/field_sample.json`: Minimal Fields (no FarmIdentificationCode).
- `tests/data/action_sample.json`: Products only (for product import tests).
- `tests/data/action_sample_with_activities.json`: Products + Activities + CropZoneIds.
- `tests/data/full_sample_minimal.json`: Minimal full export with Fields + Activities + CropZoneIds.
- `examples_json/Field.Json`, `Action.Json`: Real Geofolia exports.
