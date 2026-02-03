# Geofolia JSON Format Compatibility

## Compatible Structures

### Fields (Parcels)
- **Required**: `Id`, `Code`, `Name`, `Area`, `City`, `Geography`
- **Optional**: `FarmIdentificationCode`, `HarvestYear`, `CropName`, `VarietyName`, `SowingDate`, `HarvestDate`
- **Extra captured**: `RNCropCode`, `BotanicalSpeciesCode`, `IrrigationKind`, `IrrigationKindName`, `CityNumber`
- **Geography**: WKT in EPSG:25830 (ETRS89/UTM 30N). SRID from `Information.CoordinateReferenceSystem` or 25830 default.
- **Area**: If `Unit` = "ha" use as-is; else assume m² and convert to ha.

### Activities (Actions)
- **Tasks**: `OperationName` or `OperationCategory` is used to find or create the `project.task`. If the task does not exist in the project, it is created. Falls back to company default task when both are empty.
- **ActionEmployees** link to **CropZoneIds** via `EmployeeRecognitionId` = `CropZone.RecognitionId`.
- Each CropZone: `PlotCode`, `FarmIdentificationCode`, `WorkedSurface` (m²).
- Parcel resolution: (FarmIdentificationCode + PlotCode) or PlotCode or FarmIdentificationCode.
- Status: `StatusName`, `StatusCode`, `OperationCategory` stored in analytic line.

### Products
- **Extra captured**: `RecognitionId`, `ProductComponentNTotal`, `ProductComponentP2O5`, `ProductComponentK2O`
- Applied to `product.product` when creating/updating.

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
