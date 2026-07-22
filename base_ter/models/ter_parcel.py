# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=protected-access

import base64
import logging
import time

import psycopg2
import requests
from psycopg2 import sql

from odoo import api, exceptions, fields, models
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.queue_job.job import identity_exact

from .. import hooks as base_ter_hooks

_logger = logging.getLogger(__name__)


class TerParcel(models.Model):
    _name = "ter.parcel"
    _description = "Parcel"
    _inherit = [
        "simple.model",
        "polygon.model",
        "gis.viewer",
        "mail.thread",
        "common.background.job",
    ]

    MAX_SIZE_OFFICIAL_CODE = 50

    _set_num_code = False
    _sequence_for_codes = ""
    _size_name = 20
    _minlength = 0
    _maxlength = 20
    _allowed_blanks_in_code = False
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = True
    _size_description = 75

    _gis_table = "ter_gis_parcel"
    _geom_field = "geom"
    _link_field = "name"
    _param_gis_selection = "idparcela"

    _aerial_image_size_big = 512
    _aerial_image_size_medium = 256
    _aerial_image_size_small = 128

    _aerial_image_zoom = 1.2
    _force_square_shape = True

    _area_fields = [("area_official", "Official Area")]
    _ha_name = "ha"

    alphanum_code = fields.Char(string="Parcel Code", required=True)

    municipality_id = fields.Many2one(
        comodel_name="res.municipality",
        required=True,
        index=True,
        ondelete="restrict",
    )
    place_id = fields.Many2one(
        comodel_name="res.place",
        index=True,
        ondelete="restrict",
    )

    area_official = fields.Float(
        string="Official Area",
        digits=(32, 4),
        default=0,
        required=True,
        index=True,
    )
    area_official_m2 = fields.Integer(
        string="Official Area (m²)",
        compute="_compute_area_official_m2",
    )

    diff_areas_threshold_exceeded = fields.Boolean(
        string="Threshold exceeded (difference between official and GIS areas)",
        compute="_compute_diff_areas_threshold_exceeded",
    )

    official_code = fields.Char(size=MAX_SIZE_OFFICIAL_CODE, index=True)

    partner_id = fields.Many2one(
        string="Parcel Manager",
        comodel_name="res.partner",
        store=True,
        compute="_compute_partner_id",
        readonly=False,
        index=True,
    )

    property_id = fields.Many2one(
        comodel_name="ter.property",
        index=True,
        ondelete="restrict",
    )

    aerial_image = fields.Image(
        max_width=_aerial_image_size_big,
        max_height=_aerial_image_size_big,
    )
    aerial_image_key = fields.Char(index=True, readonly=True)
    aerial_image_last_refresh = fields.Datetime(
        readonly=True,
        index=True,
        copy=False,
    )

    aerial_image_medium = fields.Image(
        string="Aerial Image (medium size)",
        max_width=_aerial_image_size_medium,
        max_height=_aerial_image_size_medium,
        store=True,
        related="aerial_image",
    )
    aerial_image_small = fields.Image(
        string="Aerial Image (small size)",
        max_width=_aerial_image_size_small,
        max_height=_aerial_image_size_small,
        store=True,
        related="aerial_image",
    )

    tag_id = fields.Many2many(
        string="Tags",
        comodel_name="ter.parceltag",
        relation="ter_parcel_parceltag_rel",
        column1="parcel_id",
        column2="parceltag_id",
    )

    province_id = fields.Many2one(
        comodel_name="res.province",
        store=True,
        index=True,
        compute="_compute_province_id",
    )
    region_id = fields.Many2one(
        comodel_name="res.admregion",
        store=True,
        index=True,
        compute="_compute_region_id",
    )

    area_unit_name = fields.Char(
        string="Area unit name", compute="_compute_area_unit_name"
    )

    property_data = fields.Char(compute="_compute_property_data")
    address_data = fields.Char(compute="_compute_address_data")

    partnerlink_ids = fields.One2many(
        string="Contacts of parcel",
        comodel_name="ter.parcel.partnerlink",
        inverse_name="parcel_id",
    )
    unit_ids = fields.One2many(
        string="Territorial Units",
        comodel_name="ter.use_unit",
        inverse_name="parcel_id",
    )
    unit_count = fields.Integer(
        string="Units",
        compute="_compute_unit_count",
    )
    partner_code = fields.Integer(compute="_compute_partner_code")

    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "area_official_ok",
            "CHECK (area_official >= 0)",
            'Incorrect value for "Official Area".',
        ),
    ]

    def _aerial_cache_key(self, params):
        """Generate cache key for aerial image.

        Args:
            params (dict): Dictionary with keys:
                - wms: WMS URL
                - layers: WMS layers
                - styles: WMS styles
                - image_height: Image height
                - image_width: Image width
                - zoom: Zoom level
                - force_square_shape: Force square shape
                - apply_filter: Apply filter
                - extra: Extra parameters (optional)
        """
        self.ensure_one()
        return self._make_wms_key(
            self.geom_ewkt or "",
            params.get("wms") or "",
            params.get("layers") or "",
            params.get("styles") or "",
            int(params.get("image_height") or 0),
            int(params.get("image_width") or 0),
            float(params.get("zoom") or 0.0),
            bool(params.get("force_square_shape")),
            bool(params.get("apply_filter")),
            params.get("extra") or "",
        )

    @api.depends("area_official")
    def _compute_area_official_m2(self):
        company = self.env.company
        is_ha, _, value_in_ha = company._get_area_unit_params()
        factor = 10000.0
        if not is_ha and value_in_ha and value_in_ha != 1:
            factor = value_in_ha * 10000.0
        for record in self:
            record.area_official_m2 = round((record.area_official or 0.0) * factor)

    @api.depends("mapped_to_polygon", "area_official_m2", "area_gis")
    def _compute_diff_areas_threshold_exceeded(self):
        company = self.env.company
        warning = int(company.warning_diff_areas or 0)
        for record in self:
            exceeded = False
            if warning > 0 and record.mapped_to_polygon:
                diff = abs((record.area_official_m2 or 0) - (record.area_gis or 0))
                threshold = int(
                    round((record.area_official_m2 or 0) * (warning / 100.0))
                )
                exceeded = diff > threshold
            record.diff_areas_threshold_exceeded = exceeded

    @api.depends("partnerlink_ids.is_main", "partnerlink_ids.partner_id")
    def _compute_partner_id(self):
        for record in self:
            main = record.partnerlink_ids.filtered("is_main")[:1]
            record.partner_id = main.partner_id if main else False

    @api.depends("unit_ids")
    def _compute_unit_count(self):
        for record in self:
            record.unit_count = len(record.unit_ids)

    def _get_wms_config(self):
        """Load WMS configuration from current company."""
        company = self.env.company
        return {
            "wmsbase_url": company.aerial_image_wmsbase_url or False,
            "wmsbase_layers": company.aerial_image_wmsbase_layers or False,
            "wmsvec_url": company.aerial_image_wmsvec_url or False,
            "wmsvec_parcel_layer": company.aerial_image_wmsvec_parcel_name or False,
            "wmsvec_filter": bool(company.aerial_image_wmsvec_parcel_filter),
            "image_height": int(company.aerial_image_height or 0),
            "image_zoom": float(company.aerial_image_zoom or 0),
        }

    def _fetch_and_store_aerial_image(self):
        """Fetch the aerial image from the WMS service and persist it.

        This performs the actual network call(s) and must only be
        triggered by an explicit action: the "Regenerate Image" button
        (``reset_aerial_image``), a mass generation action, or the
        background queue_job (``_job_generate_aerial_image``).
        """
        self.ensure_one()
        wms_cfg = self._get_wms_config()  # pylint: disable=protected-access
        image_height = wms_cfg["image_height"] or self._aerial_image_size_big
        image_zoom = wms_cfg["image_zoom"] or self._aerial_image_zoom
        is_ogc_ok = bool(
            wms_cfg["wmsbase_url"]
            and wms_cfg["wmsbase_layers"]
            and image_height >= 0
            and image_zoom >= 0
        )
        if not (is_ogc_ok and self.mapped_to_polygon):
            return False

        use_vector = bool(
            is_ogc_ok and wms_cfg["wmsvec_url"] and wms_cfg["wmsvec_parcel_layer"]
        )
        stored_base64 = None
        if not use_vector:
            key = self._aerial_cache_key(  # pylint: disable=protected-access
                {
                    "wms": wms_cfg["wmsbase_url"],
                    "layers": wms_cfg["wmsbase_layers"],
                    "styles": "default",
                    "image_height": image_height,
                    "image_width": 0,
                    "zoom": image_zoom,
                    "force_square_shape": self._force_square_shape,
                    "apply_filter": False,
                    "extra": "base",
                }
            )
            if self.aerial_image and self.aerial_image_key == key:
                stored_base64 = self.aerial_image
            else:
                stored_base64 = self.get_aerial_image(
                    wms=wms_cfg["wmsbase_url"],
                    layers=wms_cfg["wmsbase_layers"],
                    image_height=image_height,
                    image_format="png",
                    zoom=image_zoom,
                    force_square_shape=self._force_square_shape,
                )
        else:
            key = self._aerial_cache_key(  # pylint: disable=protected-access
                {
                    "wms": wms_cfg["wmsbase_url"],
                    "layers": wms_cfg["wmsbase_layers"],
                    "styles": "default",
                    "image_height": image_height,
                    "image_width": 0,
                    "zoom": image_zoom,
                    "force_square_shape": self._force_square_shape,
                    "apply_filter": False,
                    "extra": "base+vec:%s:%s:%s"
                    % (
                        wms_cfg["wmsvec_url"] or "",
                        wms_cfg["wmsvec_parcel_layer"] or "",
                        int(wms_cfg["wmsvec_filter"]),
                    ),
                }
            )
            if self.aerial_image and self.aerial_image_key == key:
                stored_base64 = self.aerial_image
            else:
                base_image_raw = self.get_aerial_image(
                    wms=wms_cfg["wmsbase_url"],
                    layers=wms_cfg["wmsbase_layers"],
                    image_height=image_height,
                    image_format="png",
                    zoom=image_zoom,
                    get_raw=True,
                    apply_filter=False,
                    force_square_shape=self._force_square_shape,
                )
                vector_image_raw = self.get_aerial_image(
                    wms=wms_cfg["wmsvec_url"],
                    layers=wms_cfg["wmsvec_parcel_layer"],
                    image_height=image_height,
                    image_format="png",
                    zoom=image_zoom,
                    get_raw=True,
                    apply_filter=wms_cfg["wmsvec_filter"],
                    force_square_shape=self._force_square_shape,
                )
                if base_image_raw and vector_image_raw:
                    merged_bytes = self.env["common.image"].merge_img(
                        base_image_raw,
                        vector_image_raw,
                        return_base64=False,
                    )
                    if merged_bytes:
                        stored_base64 = base64.b64encode(merged_bytes)

        if stored_base64:
            self.aerial_image = stored_base64
            self.aerial_image_key = key
            self.aerial_image_last_refresh = fields.Datetime.now()
            self.env["common.log"].register_in_log(
                self.env._("Aerial image OK. Parcel: %(name)s", name=self.name),
                source=self._name,
                message_type="INFO",
            )
            return True

        self.env["common.log"].register_in_log(
            self.env._("Error getting aerial image (is the WMS url correct?)"),
            source=self._name,
            message_type="WARNING",
        )
        return False

    def _job_generate_aerial_image(self):
        """Queue_job entry point used by the background refresh cron."""
        self.ensure_one()
        wms_errors = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            OSError,
        )
        try:
            self._fetch_and_store_aerial_image()  # pylint: disable=protected-access
        except wms_errors as exc:
            raise RetryableJobError(
                self.env._(
                    "WMS temporarily unavailable for parcel %(code)s: %(error)s",
                    code=self.alphanum_code,
                    error=str(exc),
                )
            ) from exc

    @api.model
    def cron_generate_pending_aerial_images(self, batch_size=200):
        """Incrementally (re)generate aerial images via queue_job.

        Each run picks a batch of parcels with GIS geometry, giving
        priority to those that never had a successful refresh
        (``aerial_image_last_refresh`` is null) and then to the ones
        refreshed longest ago. Each parcel is delayed as its own job, so
        every job commits independently, and ``identity_exact`` prevents
        enqueuing a duplicate job for a parcel that already has one
        pending/enqueued.
        """
        records = self.search(
            [("mapped_to_polygon", "=", True)],
            order="aerial_image_last_refresh asc nulls first, create_date asc",
            limit=batch_size,
        )
        for record in records:
            record.with_delay(
                channel="root.ter_gis_aerial_image",
                identity_key=identity_exact,
                description=self.env._(
                    "Generate aerial image: %(code)s", code=record.alphanum_code
                ),
            )._job_generate_aerial_image()  # pylint: disable=protected-access
        return len(records)

    @api.depends("municipality_id.province_id")
    def _compute_province_id(self):
        for record in self:
            record.province_id = (
                record.municipality_id.province_id if record.municipality_id else False
            )

    @api.depends("province_id.region_id")
    def _compute_region_id(self):
        for record in self:
            record.region_id = (
                record.province_id.region_id if record.province_id else False
            )

    @api.depends_context("lang")
    def _compute_area_unit_name(self):
        company = self.env.company
        is_ha, unit_name, _ = company._get_area_unit_params()
        if is_ha:
            unit_name = self.env._("ha")
        for record in self:
            record.area_unit_name = unit_name

    @api.depends("property_id")
    def _compute_property_data(self):
        for record in self:
            record.property_data = (
                record.property_id.name
                if record.property_id
                else self.env._("not assigned")
            )

    @api.depends("municipality_id", "place_id", "municipality_id.province_id")
    def _compute_address_data(self):
        for record in self:
            if not record.municipality_id or not record.municipality_id.province_id:
                record.address_data = ""
                continue

            base = "%s (%s)" % (
                record.municipality_id.name,
                record.municipality_id.province_id.name,
            )
            if (
                record.place_id
                and (record.place_id.name or "").lower()
                != (record.municipality_id.name or "").lower()
            ):
                base = "%s - %s" % (record.place_id.name, base)
            record.address_data = base

    @api.depends("partner_id.partner_code")
    def _compute_partner_code(self):
        for record in self:
            record.partner_code = (
                record.partner_id.partner_code
                if record.partner_id and record.partner_id.partner_code > 0
                else 0
            )

    @api.constrains("municipality_id", "place_id")
    def _check_place_id(self):
        for record in self:
            if (
                record.municipality_id
                and record.place_id
                and record.place_id.municipality_id != record.municipality_id
            ):
                raise exceptions.ValidationError(
                    self.env._("The place is not in the municipality.")
                )

    @api.constrains("partner_id", "property_id")
    def _check_property_id(self):
        company = self.env.company
        same_owner = bool(company.same_parcelmanager_propertyowner)
        if not same_owner:
            return

        for record in self:
            if (
                record.partner_id
                and record.property_id
                and record.partner_id != record.property_id.partner_id
            ):
                raise exceptions.ValidationError(
                    self.env._(
                        "The parcel manager and the property manager must be "
                        "the same person."
                    )
                )

    @api.constrains("partner_id", "partnerlink_ids")
    def _check_partner_id(self):
        for record in self:
            if record.partner_id:
                if not record.partner_id.is_holder:
                    raise exceptions.ValidationError(
                        self.env._("The contact chosen as main is not a manager.")
                    )
                if not record.partnerlink_ids:
                    raise exceptions.ValidationError(
                        self.env._(
                            "If a manager is assigned to the parcel, it is "
                            "mandatory to configure the contact list."
                        )
                    )

            main = record.partnerlink_ids.filtered("is_main")[:1]
            if main and record.partner_id and main.partner_id != record.partner_id:
                raise exceptions.ValidationError(
                    self.env._(
                        "The parcel manager and the main contact must be "
                        "the same person."
                    )
                )

    @api.constrains("partner_id", "partnerlink_ids")
    def _check_partnerlink_ids(self):
        for record in self:
            if not record.partnerlink_ids:
                if record.partner_id:
                    raise exceptions.ValidationError(
                        self.env._(
                            "The main contact exists, but the contact list of "
                            "the parcel is empty."
                        )
                    )
                continue

            if not record.partner_id:
                raise exceptions.ValidationError(
                    self.env._("It is mandatory to enter the parcel manager.")
                )

            mains = record.partnerlink_ids.filtered("is_main")
            if len(mains) != 1:
                raise exceptions.ValidationError(
                    self.env._(
                        "It is mandatory to enter the main contact of the "
                        "parcel (only one)."
                    )
                )

            profiles = record.partnerlink_ids.mapped("profile_id")
            for prof in profiles:
                if not prof or not prof.requires_total:
                    continue
                links = record.partnerlink_ids.filtered_domain(
                    [("profile_id", "=", prof.id)]
                )
                total = sum(links.mapped("percentage"))
                if total != 100:
                    raise exceptions.ValidationError(
                        self.env._(
                            "Review the profile percentages: there is a "
                            "percentage profile that does not add up to 100%."
                        )
                    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if not self.partner_id:
            return

        if not self.partnerlink_ids or len(self.partnerlink_ids) == 1:
            profile_id, percentage = self._get_default_profile()
            self.partnerlink_ids = [
                (5,),
                (
                    0,
                    0,
                    self._get_default_first_partnerlink_vals(
                        self.partner_id.id, profile_id, percentage
                    ),
                ),
            ]
            return

        main = self.partnerlink_ids.filtered("is_main")[:1]
        if main:
            self.partnerlink_ids = [(1, main.id, {"partner_id": self.partner_id.id})]

    def _get_default_profile(self):
        profile_id = self.env.ref("base_ter.ter_profile_01").id
        return profile_id, 100

    def _get_default_first_partnerlink_vals(self, partner_id, profile_id, percentage):
        return {
            "partner_id": partner_id,
            "profile_id": profile_id,
            "is_main": True,
            "percentage": percentage,
        }

    @api.depends("active", "name")
    @api.depends_context("show_archived_in_parcel_code")
    def _compute_display_name(self):
        show_archived = bool(
            self.env.context.get("show_archived_in_parcel_code", False)
        )
        for record in self:
            name = record.name
            if show_archived:
                name = (
                    self.env._("Available") if record.active else self.env._("ARCHIVED")
                )
            record.display_name = name

    def write(self, vals):
        res = super().write(vals)
        if "active" not in vals:
            return res

        partners = self.mapped("partnerlink_ids.partner_id").filtered("is_holder")
        for record in self.filtered("property_id"):
            record.property_id._refresh_computed_fields()  # pylint: disable=protected-access

        if partners:
            partners._refresh_computed_fields()  # pylint: disable=protected-access
        return res

    def _set_gis_geometry(self, geom_ewkt):
        """Insert or update this parcel's geometry in the ter_gis_parcel table.

        Parcel geometry is not stored on an ORM field: it lives in the GIS
        table keyed by ``name``. This mirrors
        ``ter.use_unit._sync_geom_to_gis_unit`` so parcels created from
        external sources (e.g. Geofolia Fields) become mapped in GIS.
        """
        self.ensure_one()
        if not self.name:
            return
        ewkt = (geom_ewkt or "").strip()
        if not ewkt:
            return
        if not ewkt.upper().startswith("SRID="):
            ewkt = "SRID=25830;%s" % ewkt
        qual = sql.SQL("{}.{}").format(
            sql.Identifier(base_ter_hooks.GIS_SCHEMA),
            sql.Identifier(base_ter_hooks.PARCEL_TABLE),
        )
        self.env.cr.execute(
            sql.SQL(
                "INSERT INTO {} (name, geom) "
                "VALUES (%s, ST_Multi("
                "ST_GeomFromEWKT(%s)::geometry"
                ")::geometry(MultiPolygon, 25830)) "
                "ON CONFLICT (name) DO UPDATE "
                "SET geom = EXCLUDED.geom"
            ).format(qual),
            (self.name, ewkt),
        )
        self.invalidate_recordset(["mapped_to_polygon", "geom_ewkt"])
        self._compute_mapped_to_polygon()

    def _get_measure_name_for_view(self):
        """Get area measure name from current company for view."""
        company = self.env.company
        is_ha, area_unit_name, value_in_ha = company._get_area_unit_params()
        measure_name = self.env._(self._ha_name)
        if (
            not is_ha
            and area_unit_name
            and value_in_ha
            and value_in_ha != 1
            and area_unit_name != measure_name
        ):
            measure_name = area_unit_name
        return measure_name

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type not in ("form", "tree"):
            return arch, view
        area_fields = self._add_area_fields() or []
        if not area_fields:
            return arch, view
        area_map = dict(area_fields)
        measure_name = (
            self._get_measure_name_for_view()
        )  # pylint: disable=protected-access

        for field_name, label in area_map.items():
            for node in arch.xpath(f"//field[@name='{field_name}']"):
                node.set("string", "%s (%s)" % (self.env._(label), measure_name))

        return arch, view

    def delete_aerial_image(self):
        for record in self:
            record.aerial_image = False
            record.aerial_image_key = False
            record.aerial_image_medium = False
            record.aerial_image_small = False

    def _reset_single_aerial_image(self):
        """Reset aerial image for a single parcel record."""
        self.ensure_one()
        self.aerial_image = False
        self.aerial_image_key = False
        self._fetch_and_store_aerial_image()  # pylint: disable=protected-access

    def reset_aerial_image(self):
        wms_errors = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            OSError,
        )

        if len(self) == 1:
            try:
                self._reset_single_aerial_image()  # pylint: disable=protected-access
                self.env.cr.commit()  # pylint: disable=invalid-commit
                self.env.invalidate_all()
            except wms_errors as e:
                _logger.warning(
                    "WMS fetch failed for parcel %s: %s", self.alphanum_code, e
                )
                raise exceptions.UserError(
                    self.env._(
                        "Could not fetch aerial image from WMS (timeout or "
                        "connection error). Try again later or check "
                        "network/IGN service. Parcel: %(code)s",
                        code=self.alphanum_code,
                    )
                ) from e
            return

        failed = []
        max_serialization_retries = 3
        for record in self.with_progress(self.env._("Getting the aerial images...")):
            for attempt in range(max_serialization_retries + 1):
                try:
                    record._reset_single_aerial_image()  # pylint: disable=protected-access
                    self.env.cr.commit()  # pylint: disable=invalid-commit
                    self.env.invalidate_all()
                    break
                except psycopg2.errors.SerializationFailure:
                    if attempt < max_serialization_retries:
                        self.env.cr.rollback()
                        self.env.invalidate_all()
                        time.sleep(0.5 * (attempt + 1))
                    else:
                        raise
                except wms_errors as e:
                    _logger.warning(
                        "WMS fetch failed for parcel %s: %s",
                        record.alphanum_code,
                        e,
                    )
                    failed.append(record.alphanum_code)
                    break
                except Exception as e:  # noqa: BLE001  # pylint: disable=W0718
                    # Never let a single bad record (e.g. a corrupt/
                    # degenerate geometry) abort the rest of the batch.
                    self.env.cr.rollback()
                    self.env.invalidate_all()
                    _logger.exception(
                        "Unexpected error generating aerial image for parcel %s: %s",
                        record.alphanum_code,
                        e,
                    )
                    failed.append(record.alphanum_code)
                    break
        if failed:
            raise exceptions.UserError(
                self.env._(
                    "Could not fetch aerial images for %(count)s parcel(s) "
                    "(timeout or connection error to WMS). Try again later: %(codes)s",
                    count=len(failed),
                    codes=", ".join(failed[:10]),
                )
            )

    _MASS_AERIAL_IMAGE_BATCH_NAME = "base_ter.ter_parcel.action_reset_all_aerial_images"
    _MASS_AERIAL_IMAGE_CHUNK_SIZE = 50

    @api.model
    def action_reset_all_aerial_images(self, from_backend=False):
        """Enqueue a background job batch to regenerate every parcel's image.

        The work is split into small chunks, each delayed as its own
        queue_job tagged to a ``queue.job.batch``, so progress can be
        tracked via the batch's ``completeness`` percentage. If a
        previous batch is still running, no duplicate is created; the
        user is notified instead.
        """
        launched = not self._is_background_batch_running(
            self._MASS_AERIAL_IMAGE_BATCH_NAME
        )
        if launched:
            batch = self._new_background_batch(self._MASS_AERIAL_IMAGE_BATCH_NAME)
            chunk_size = self._MASS_AERIAL_IMAGE_CHUNK_SIZE
            offset = 0
            while True:
                chunk_ids = self.search([], limit=chunk_size, offset=offset).ids
                if not chunk_ids:
                    break
                self.browse(chunk_ids).with_context(job_batch=batch).with_delay(
                    channel="root.ter_gis_aerial_image",
                    description=self.env._(
                        "Generate aerial images (parcels), records %(offset)s+",
                        offset=offset,
                    ),
                )._job_reset_all_aerial_images_chunk()  # pylint: disable=protected-access
                offset += chunk_size
        return self._background_job_notification(launched, from_backend)

    def _job_reset_all_aerial_images_chunk(self):
        """Queue_job entry point: regenerate this chunk's aerial images."""
        self.reset_aerial_image()

    def action_gis_preview(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s : %s" % (self.env._("Parcel on the map"), self.alphanum_code),
            "res_model": "wizard.show.gis.preview",
            "view_mode": "form",
            "target": "new",
            "context": {
                "src_model": "ter.parcel",
                "active_id": self.id,
            },
        }

    def action_set_parcel_code(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s : %s" % (self.env._("Parcel"), self.alphanum_code),
            "res_model": "wizard.set.parcel.code",
            "view_mode": "form",
            "target": "new",
        }

    def action_show_units(self):
        self.ensure_one()
        list_view = self.env.ref("base_ter.view_ter_unit_list")
        form_view = self.env.ref("base_ter.view_ter_unit_form")
        search_view = self.env.ref("base_ter.view_ter_unit_filter")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Territorial Units"),
            "res_model": "ter.use_unit",
            "view_mode": "list,form",
            "views": [
                (list_view.id, "list"),
                (form_view.id, "form"),
            ],
            "search_view_id": search_view.id,
            "target": "current",
            "domain": [("parcel_id", "=", self.id)],
            "context": {"default_parcel_id": self.id},
        }

    @api.model
    def _add_area_fields(self):
        return self._area_fields
