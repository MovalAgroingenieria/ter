# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models


class TerGisParcelModel(models.Model):
    _name = "ter.gis.parcel.model"
    _description = "GIS Parcel"
    _auto = False

    _aerial_image_size_small = 128

    name = fields.Char(string="Parcel Code")
    geom_geojson = fields.Char(string="GeoJSON Geometry")

    parcel_id = fields.Many2one(string="Parcel", comodel_name="ter.parcel")
    partner_id = fields.Many2one(string="Parcel Partner", comodel_name="res.partner")
    is_active = fields.Boolean(string="Active")

    diff_areas_threshold_exceeded = fields.Boolean(
        string="Threshold exceeded (difference between official and GIS areas)",
        related="parcel_id.diff_areas_threshold_exceeded",
        readonly=True,
    )
    diff_areas_threshold_exceeded_str = fields.Char(
        string="Threshold exceeded (difference between official and GIS areas) -str-",
        compute="_compute_diff_areas_threshold_exceeded_str",
    )

    gis_data = fields.Text(string="GIS Data", compute="_compute_gis_data")

    aerial_image_small = fields.Image(
        string="Aerial Image (small size)",
        max_width=_aerial_image_size_small,
        max_height=_aerial_image_size_small,
        related="parcel_id.aerial_image_small",
        readonly=True,
    )

    @api.depends("parcel_id", "diff_areas_threshold_exceeded")
    def _compute_diff_areas_threshold_exceeded_str(self):
        for record in self:
            if not record.parcel_id:
                record.diff_areas_threshold_exceeded_str = ""
                continue

            record.diff_areas_threshold_exceeded_str = _("CHECK") if record.diff_areas_threshold_exceeded else _("ok")

    @api.depends(
        "parcel_id",
        "parcel_id.area_official_m2",
        "parcel_id.area_gis",
        "parcel_id.perimeter_gis",
        "parcel_id.bounding_box_str",
    )
    def _compute_gis_data(self):
        formatter = self.env["common.format"]
        for record in self:
            if not record.parcel_id:
                record.gis_data = ""
                continue

            bbox = record.parcel_id.bounding_box_str or ""
            pos = bbox.find("(")
            if pos != -1:
                bbox = bbox[pos:]

            record.gis_data = "\n".join(
                [
                    "⸰ %s: %s"
                    % (
                        _("Official Area (m²)"),
                        formatter.transform_integer_to_locale(record.parcel_id.area_official_m2),
                    ),
                    "⸰ %s: %s"
                    % (
                        _("GIS Area (m²)"),
                        formatter.transform_integer_to_locale(record.parcel_id.area_gis),
                    ),
                    "⸰ %s: %s"
                    % (
                        _("GIS Perimeter (m)"),
                        formatter.transform_integer_to_locale(record.parcel_id.perimeter_gis),
                    ),
                    "⸰ %s" % bbox,
                ]
            )
