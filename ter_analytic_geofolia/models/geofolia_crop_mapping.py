import unicodedata

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GeofoliaCropMapping(models.Model):
    _name = "geofolia.crop.mapping"
    _description = "Geofolia Crop Mapping"
    _order = "name"
    _check_company_auto = True

    name = fields.Char(string="Geofolia Crop", required=True)
    normalized_name = fields.Char(compute="_compute_normalized_name", store=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    use_type_id = fields.Many2one("ter.use_type", string="Odoo Crop")
    is_non_crop = fields.Boolean(string="Not a Crop")
    state = fields.Selection(
        [
            ("review", "Pending Review"),
            ("mapped", "Mapped"),
            ("not_crop", "Not a Crop"),
        ],
        compute="_compute_state",
        store=True,
    )
    note = fields.Text()

    _sql_constraints = [
        (
            "crop_company_name_unique",
            "unique(company_id, normalized_name)",
            "A mapping already exists for this Geofolia crop and company.",
        ),
    ]

    @api.model
    def _normalize_name(self, name):
        value = unicodedata.normalize("NFKD", name or "")
        return " ".join(
            "".join(char for char in value if not unicodedata.combining(char))
            .upper()
            .split()
        )

    @api.depends("name")
    def _compute_normalized_name(self):
        for record in self:
            record.normalized_name = self._normalize_name(record.name)

    @api.depends("use_type_id", "is_non_crop")
    def _compute_state(self):
        for record in self:
            record.state = (
                "not_crop"
                if record.is_non_crop
                else "mapped" if record.use_type_id else "review"
            )

    @api.constrains("use_type_id", "is_non_crop")
    def _check_non_crop(self):
        for record in self:
            if record.is_non_crop and record.use_type_id:
                raise ValidationError(
                    self.env._("A non-crop entry cannot have an Odoo crop.")
                )

    @api.model
    def _resolve(self, name):
        normalized = self._normalize_name(name)
        if not normalized:
            return self.browse()
        mapping = self.search(
            [
                ("company_id", "=", self.env.company.id),
                ("normalized_name", "=", normalized),
            ],
            limit=1,
        )
        if mapping:
            return mapping
        values = {"name": name.strip(), "is_non_crop": normalized == "FEINES TERCERS"}
        if not values["is_non_crop"]:
            aliases = {"ORDI": "CEBADA", "ALFALS": "ALFALFA"}
            names = {normalized, aliases.get(normalized, normalized)}
            candidates = (
                self.env["ter.use_type"]
                .search([("child_ids", "=", False)])
                .filtered(lambda crop: self._normalize_name(crop.name) in names)
            )
            if len(candidates) == 1:
                values["use_type_id"] = candidates.id
        return self.create(values)
