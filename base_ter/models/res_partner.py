# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    _size_partner_code = 6
    _area_fields = [
        ("area_official_parcels", "Parcel Area"),
        ("area_official_properties", "Property Area"),
    ]
    _ha_name = "ha"

    def _default_partner_code(self):
        if not self.env.context.get("context_default_partner_code"):
            return 0

        self.env.cr.execute("SELECT max(partner_code) FROM res_partner")
        result = self.env.cr.dictfetchone()
        max_code = result.get("max") if result else None
        return (max_code or 0) + 1 if max_code is not None else 0

    partner_code = fields.Integer(
        # pylint: disable=protected-access
        default=lambda self: self._default_partner_code(),
        required=False,
        index=True,
    )
    partner_code_asstr = fields.Char(
        string="Partner Code (as string)",
        store=True,
        compute="_compute_partner_code_asstr",
    )
    is_holder = fields.Boolean(
        string="Parcel Holder",
        default=False,
        store=True,
        compute="_compute_is_holder",
    )

    parcel_ids = fields.One2many(
        string="Parcels",
        comodel_name="ter.parcel",
        inverse_name="partner_id",
    )
    number_of_parcels = fields.Integer(
        string="Number of parcels",
        store=True,
        index=True,
        compute="_compute_number_of_parcels",
    )
    partnerlink_ids = fields.One2many(
        string="Parcel Partner-Links",
        comodel_name="ter.parcel.partnerlink",
        inverse_name="partner_id",
    )
    number_of_partnerlinks = fields.Integer(
        string="Number of partner-links",
        store=True,
        index=True,
        compute="_compute_number_of_partnerlinks",
    )
    area_official_parcels = fields.Float(
        string="Parcel Area",
        digits=(32, 4),
        store=True,
        index=True,
        compute="_compute_area_official_parcels",
    )
    area_official_parcels_m2 = fields.Integer(
        string="Parcel Area (m²)",
        compute="_compute_area_official_parcels_m2",
    )

    property_ids = fields.One2many(
        string="Properties",
        comodel_name="ter.property",
        inverse_name="partner_id",
    )
    number_of_properties = fields.Integer(
        string="Number of properties",
        store=True,
        index=True,
        compute="_compute_number_of_properties",
    )
    area_official_properties = fields.Float(
        string="Property Area",
        digits=(32, 4),
        store=True,
        index=True,
        compute="_compute_area_official_properties",
    )
    area_official_properties_m2 = fields.Integer(
        string="Property Area (m²)",
        compute="_compute_area_official_properties_m2",
    )

    area_unit_name = fields.Char(
        string="Area unit name",
        compute="_compute_area_unit_name",
    )

    unit_use_ids = fields.One2many(
        string="Territorial Units",
        comodel_name="ter.use_unit",
        inverse_name="partner_id",
    )
    unit_use_count = fields.Integer(
        string="Units",
        compute="_compute_unit_use_count",
    )

    phones = fields.Char(string="Phone(s)", store=True, compute="_compute_phones")

    _sql_constraints = [
        ("partner_code_ok", "CHECK (partner_code >= 0)", "Wrong partner code."),
        (
            "partner_code_uniq",
            "UNIQUE(partner_code) WHERE partner_code IS NOT NULL",
            "Repeated partner code.",
        ),
    ]

    @api.depends("partner_code")
    def _compute_partner_code_asstr(self):
        for record in self:
            record.partner_code_asstr = (
                str(record.partner_code).zfill(self._size_partner_code)
                if record.partner_code
                else ""
            )

    @api.depends("partner_code")
    def _compute_is_holder(self):
        for record in self:
            record.is_holder = bool(record.partner_code and record.partner_code > 0)

    def _refresh_computed_fields(self):
        self._compute_number_of_parcels()
        self._compute_area_official_parcels()

    @api.depends("parcel_ids")
    def _compute_number_of_parcels(self):
        for record in self:
            record.number_of_parcels = len(record.parcel_ids)

    @api.depends("partnerlink_ids", "partnerlink_ids.active")
    def _compute_number_of_partnerlinks(self):
        for record in self:
            record.number_of_partnerlinks = len(record.partnerlink_ids)

    @api.depends("parcel_ids.area_official")
    def _compute_area_official_parcels(self):
        for record in self:
            record.area_official_parcels = sum(
                record.parcel_ids.mapped("area_official")
            )

    @api.depends("area_official_parcels")
    def _compute_area_official_parcels_m2(self):
        company = self.env.company
        is_ha, _, value_in_ha = company._get_area_unit_params()
        factor = 10000.0
        if not is_ha and value_in_ha and value_in_ha != 1:
            factor = value_in_ha * 10000.0
        for record in self:
            record.area_official_parcels_m2 = round(
                (record.area_official_parcels or 0.0) * factor
            )

    @api.depends("property_ids")
    def _compute_number_of_properties(self):
        for record in self:
            record.number_of_properties = len(record.property_ids)

    @api.depends("unit_use_ids")
    def _compute_unit_use_count(self):
        for record in self:
            record.unit_use_count = len(record.unit_use_ids)

    @api.depends("property_ids.area_official_parcels")
    def _compute_area_official_properties(self):
        for record in self:
            record.area_official_properties = sum(
                record.property_ids.mapped("area_official_parcels")
            )

    @api.depends("area_official_properties")
    def _compute_area_official_properties_m2(self):
        company = self.env.company
        is_ha, _, value_in_ha = company._get_area_unit_params()
        factor = 10000.0
        if not is_ha and value_in_ha and value_in_ha != 1:
            factor = value_in_ha * 10000.0
        for record in self:
            record.area_official_properties_m2 = round(
                (record.area_official_properties or 0.0) * factor
            )

    @api.depends_context("lang")
    def _compute_area_unit_name(self):
        company = self.env.company
        is_ha, unit_name, _ = company._get_area_unit_params()
        if is_ha:
            unit_name = self.env._("ha")
        for record in self:
            record.area_unit_name = unit_name

    @api.depends("phone", "mobile")
    def _compute_phones(self):
        for record in self:
            phones = []
            if record.mobile:
                phones.append(record.mobile)
            if record.phone:
                phones.append(record.phone)
            record.phones = ", ".join(phones)

    @api.constrains("partner_code")
    def _check_partner_code(self):
        for record in self:
            if not record.partner_code or record.partner_code <= 0:
                continue
            count = self.search_count(
                [("partner_code", "=", record.partner_code), ("id", "!=", record.id)]
            )
            if count:
                raise exceptions.ValidationError(self.env._("Repeated partner code."))

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

        if view_type not in ("form", "list"):
            return arch, view

        area_fields = self._add_area_fields() or []
        if not area_fields:
            return arch, view

        seen = {}
        for field_name, label in area_fields:
            seen[field_name] = label
        field_labels = self.fields_get(list(seen.keys()))

        measure_name = (
            self._get_measure_name_for_view()
        )  # pylint: disable=protected-access

        for field_name, label in seen.items():
            translated_label = field_labels.get(field_name, {}).get(
                "string"
            ) or self.env._(label)
            for node in arch.xpath(f"//field[@name='{field_name}']"):
                node.set("string", "%s (%s)" % (translated_label, measure_name))

        return arch, view

    display_name = fields.Char(compute="_compute_display_name")

    @api.depends("partner_code")
    def _compute_display_name(self):
        result = super()._compute_display_name()
        for rec in self.filtered(lambda r: r.partner_code and r.partner_code > 0):
            parts = (rec.display_name or "").split("\n")
            parts[0] = "%s [%s]" % (parts[0], rec.partner_code)
            rec.display_name = "\n".join(parts)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("parent_id"):
                vals["partner_code"] = 0
        return super().create(vals_list)

    def action_gis_viewer_parcel(self):
        parcel_ids = list(set(self.mapped("partnerlink_ids.parcel_id").ids))
        parcels = self.env["ter.parcel"].browse(parcel_ids)
        return parcels.action_gis_viewer() if parcels else None

    def action_gis_viewer_property(self):
        properties = self.mapped("property_ids")
        return properties.action_gis_viewer() if properties else None

    def action_set_partner_code(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "wizard.set.partner.code",
            "view_mode": "form",
            "target": "new",
        }

    def action_show_parcels(self):
        self.ensure_one()
        tree_view = self.env.ref("base_ter.ter_parcel_view_list")
        form_view = self.env.ref("base_ter.ter_parcel_view_form")
        kanban_view = self.env.ref("base_ter.ter_parcel_view_kanban")
        search_view = self.env.ref("base_ter.ter_parcel_view_search")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Parcels (Manager)"),
            "res_model": "ter.parcel",
            "view_mode": "list,form,kanban",
            "views": [
                (tree_view.id, "list"),
                (form_view.id, "form"),
                (kanban_view.id, "kanban"),
            ],
            "search_view_id": search_view.id,
            "target": "current",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }

    def action_show_partnerlinks(self):
        self.ensure_one()
        tree_view = self.env.ref("base_ter.ter_parcel_partnerlink_view_tree_by_partner")
        search_view = self.env.ref("base_ter.ter_parcel_partnerlink_view_search")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Parcels"),
            "res_model": "ter.parcel.partnerlink",
            "view_mode": "list",
            "views": [(tree_view.id, "list")],
            "search_view_id": search_view.id,
            "target": "current",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }

    def action_show_unit_uses(self):
        self.ensure_one()
        list_view = self.env.ref("base_ter.ter_use_unit_view_list")
        form_view = self.env.ref("base_ter.ter_use_unit_view_form")
        search_view = self.env.ref("base_ter.ter_use_unit_view_search")
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
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }

    def action_show_properties(self):
        self.ensure_one()
        tree_view = self.env.ref("base_ter.ter_property_view_list")
        form_view = self.env.ref("base_ter.ter_property_view_form")
        kanban_view = self.env.ref("base_ter.ter_property_view_kanban")
        search_view = self.env.ref("base_ter.ter_property_view_search")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Properties"),
            "res_model": "ter.property",
            "view_mode": "list,form,kanban",
            "views": [
                (tree_view.id, "list"),
                (form_view.id, "form"),
                (kanban_view.id, "kanban"),
            ],
            "search_view_id": search_view.id,
            "target": "current",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }

    @api.model
    def _add_area_fields(self):
        return self._area_fields
