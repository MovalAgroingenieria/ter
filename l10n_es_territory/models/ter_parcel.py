# Copyright 2024+2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from xml.etree import ElementTree

import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TerParcel(models.Model):
    _inherit = "ter.parcel"

    MAX_SIZE_OFFICIAL_CODE_URBAN = 50
    MAX_SIZE_CADASTRAL_FIELD = 10

    SIZE_RC1 = 7
    SIZE_RC2 = 7

    REQUEST_TIMEOUT = 5

    _SIZE_MUNICIPALITY_CADASTRAL_CODE = 5
    _SIZE_CADASTRAL_SECTOR = 1
    _SIZE_CADASTRAL_POLYGON = 3
    _SIZE_CADASTRAL_PARCEL = 5

    _URL_CADASTRAL_DATA = (
        "http://ovc.catastro.meh.es/ovcservweb/"
        "OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC?"
        "Provincia=&Municipio=&RC="
    )
    _URL_CADASTRAL_FORM = (
        "https://www1.sedecatastro.gob.es/"
        "CYCBienInmueble/OVCListaBienes.aspx?del=&muni=&rc1=rc1val&rc2=rc2val"
    )

    _AUTOMATIC_UPDATE_CADASTRAL_DATA = True

    parcel_type = fields.Selection(
        selection=[
            ("01_R", "Rustic"),
            ("02_U", "Urban"),
        ],
        default="01_R",
        required=True,
        index=True,
    )

    official_code_urban = fields.Char(size=MAX_SIZE_OFFICIAL_CODE_URBAN)

    cadastral_sector = fields.Char(size=MAX_SIZE_CADASTRAL_FIELD, default="A")
    cadastral_polygon = fields.Char(size=MAX_SIZE_CADASTRAL_FIELD)
    cadastral_parcel = fields.Char(size=MAX_SIZE_CADASTRAL_FIELD)

    official_code = fields.Char(
        store=True,
        compute="_compute_official_code",
        readonly=True,
    )

    cadastral_area = fields.Integer(default=0)

    cadastral_subparcel = fields.Char(size=MAX_SIZE_CADASTRAL_FIELD)

    official_code_with_subparcel = fields.Char(
        store=True,
        index=True,
        compute="_compute_official_code_with_subparcel",
        readonly=True,
    )

    @api.depends("official_code", "cadastral_subparcel")
    def _compute_official_code_with_subparcel(self):
        for record in self:
            if not record.official_code:
                record.official_code_with_subparcel = ""
                continue
            if record.cadastral_subparcel:
                record.official_code_with_subparcel = (
                    f"{record.official_code}-{record.cadastral_subparcel}"
                )
            else:
                record.official_code_with_subparcel = record.official_code

    @api.depends(
        "parcel_type",
        "municipality_id",
        "municipality_id.cadastral_code",
        "official_code_urban",
        "cadastral_sector",
        "cadastral_polygon",
        "cadastral_parcel",
    )
    def _compute_official_code(self):
        for record in self:
            record.official_code = record._get_official_code() or ""

    def _get_official_code(self):
        self.ensure_one()

        if self.parcel_type == "01_R":
            if not (
                self.municipality_id
                and self.municipality_id.cadastral_code
                and self.cadastral_sector
                and self.cadastral_polygon
                and self.cadastral_parcel
            ):
                return ""

            return (
                f"{self.municipality_id.cadastral_code}"
                f"{self.cadastral_sector}"
                f"{(self.cadastral_polygon or '').zfill(self._SIZE_CADASTRAL_POLYGON)}"
                f"{(self.cadastral_parcel or '').zfill(self._SIZE_CADASTRAL_PARCEL)}"
            )

        if self.official_code_urban:
            return (self.official_code_urban or "").strip()

        return ""

    @api.constrains("cadastral_area")
    def _check_cadastral_area_non_negative(self):
        for record in self:
            if record.cadastral_area is not None and record.cadastral_area < 0:
                raise ValidationError(
                    self.env._('Incorrect value for "Cadastral Area (m²)".')
                )

    @api.constrains("official_code")
    def _check_official_code_length(self):
        expected_len = (
            self._SIZE_MUNICIPALITY_CADASTRAL_CODE
            + self._SIZE_CADASTRAL_SECTOR
            + self._SIZE_CADASTRAL_POLYGON
            + self._SIZE_CADASTRAL_PARCEL
        )
        for record in self:
            if record.parcel_type != "01_R" or not record.official_code:
                continue
            if len(record.official_code) != expected_len:
                raise ValidationError(
                    self.env._("The length of the cadastral reference is not correct.")
                )

    @api.constrains("official_code_with_subparcel")
    def _check_official_code_with_subparcel_unique(self):
        for record in self:
            if not record.official_code_with_subparcel:
                continue
            if self.search_count(
                [
                    (
                        "official_code_with_subparcel",
                        "=",
                        record.official_code_with_subparcel,
                    ),
                    ("id", "!=", record.id),
                ]
            ):
                raise ValidationError(
                    self.env._(
                        "Repeated cadastral reference (with subparcel). "
                        "Check archived parcels."
                    )
                )

    def _sanitize_vals(self, vals):
        vals = dict(vals or {})

        if vals.get("cadastral_sector"):
            vals["cadastral_sector"] = (vals["cadastral_sector"] or "").strip().upper()

        if "cadastral_polygon" in vals:
            vals["cadastral_polygon"] = self._normalize_cadastral_numeric_field(
                vals.get("cadastral_polygon"),
                size=self._SIZE_CADASTRAL_POLYGON,
            )

        if "cadastral_parcel" in vals:
            vals["cadastral_parcel"] = self._normalize_cadastral_numeric_field(
                vals.get("cadastral_parcel"),
                size=self._SIZE_CADASTRAL_PARCEL,
            )

        if "parcel_type" in vals:
            if vals["parcel_type"] == "01_R":
                vals["official_code_urban"] = False
            else:
                vals["cadastral_sector"] = False
                vals["cadastral_polygon"] = False
                vals["cadastral_parcel"] = False

        if vals.get("cadastral_subparcel"):
            vals["cadastral_subparcel"] = (
                (vals["cadastral_subparcel"] or "").strip().upper()
            )

        return vals

    def _normalize_cadastral_numeric_field(self, value, size):
        if not value:
            return False
        try:
            number = int(str(value).strip())
        except (TypeError, ValueError):
            return False
        if number <= 0:
            return False
        return str(number).zfill(size)

    def _process_vals(self, vals):
        vals = self._sanitize_vals(vals)
        return super()._process_vals(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._maybe_update_cadastral_area()
        return records

    def write(self, vals):
        vals = self._sanitize_vals(vals)
        tracked = {
            "parcel_type",
            "municipality_id",
            "official_code_urban",
            "cadastral_sector",
            "cadastral_polygon",
            "cadastral_parcel",
        }
        need_update = bool(tracked.intersection(vals.keys()))
        res = super().write(vals)
        if need_update:
            self._maybe_update_cadastral_area()
        return res

    def _maybe_update_cadastral_area(self):
        if not self._AUTOMATIC_UPDATE_CADASTRAL_DATA:
            return
        for record in self:
            if not record.official_code:
                continue
            if record.cadastral_area:
                continue
            record.cadastral_area = record._get_cadastral_area()

    def _get_cadastral_area(self):
        self.ensure_one()
        if not self.official_code:
            return 0

        try:
            resp = requests.get(
                f"{self._URL_CADASTRAL_DATA}{self.official_code}",
                timeout=self.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException:
            return 0

        try:
            cadastral_data = ElementTree.fromstring(resp.content)
        except ElementTree.ParseError:
            return 0

        prefix = ""
        pos_closing = cadastral_data.tag.find("}")
        if pos_closing != -1:
            prefix = cadastral_data.tag[: pos_closing + 1]

        try:
            number_of_items = int(cadastral_data[0][0].text)
        except (IndexError, TypeError, ValueError):
            return 0

        if number_of_items != 1:
            return 0

        cadastral_area = 0
        for item in cadastral_data.iter(f"{prefix}ssp"):
            try:
                cadastral_area += int(item.text or 0)
            except (TypeError, ValueError):
                continue
        return cadastral_area

    def action_show_cadastral_form(self):
        self.ensure_one()
        if not self.official_code:
            return False

        expected_len = self.SIZE_RC1 + self.SIZE_RC2
        if len(self.official_code) != expected_len:
            return False

        rc1 = self.official_code[: self.SIZE_RC1]
        rc2 = self.official_code[self.SIZE_RC1 :]
        cadastral_link = self._URL_CADASTRAL_FORM.replace("rc1val", rc1).replace(
            "rc2val", rc2
        )
        return {
            "type": "ir.actions.act_url",
            "url": cadastral_link,
            "target": "new",
        }
