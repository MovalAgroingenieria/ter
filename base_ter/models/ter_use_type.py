# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class UseType(models.Model):
    _name = "ter.use_type"
    _description = "Ter Use Type"
    _parent_name = "parent_id"
    _parent_store = True
    _order = "parent_path, sequence, name"
    _rec_name = "complete_name"

    name = fields.Char(required=True, index=True, translate=True)
    sequence = fields.Integer(default=10, index=True)
    active = fields.Boolean(default=True)

    parent_id = fields.Many2one(
        comodel_name="ter.use_type",
        index=True,
        ondelete="restrict",
        domain="[('id', '!=', id), ('id', 'not child_of', id)]",
    )
    child_ids = fields.One2many(
        comodel_name="ter.use_type",
        inverse_name="parent_id",
        string="Children",
    )
    parent_path = fields.Char(index=True)

    complete_name = fields.Char(
        compute="_compute_complete_name",
        store=True,
        recursive=True,
        index=True,
        readonly=True,
    )

    color = fields.Integer(string="Color Index")
    unit_ids = fields.One2many(
        "ter.use_unit",
        "use_type_id",
        string="Territorial Units",
    )
    date_range_ids = fields.One2many(
        "date.range",
        "use_type_id",
        string="Assigned Date Ranges",
    )
    unit_count = fields.Integer(
        string="Units",
        compute="_compute_unit_count",
    )
    parcel_count = fields.Integer(
        string="Parcels",
        compute="_compute_parcel_count",
    )
    date_range_count = fields.Integer(
        string="Date Ranges",
        compute="_compute_date_range_count",
    )
    attribute_ids = fields.One2many(
        comodel_name="ter.use_type.attribute",
        inverse_name="use_type_id",
        string="Attributes",
    )

    _sql_constraints = [
        ("name_not_empty", "CHECK(name <> '')", "Name cannot be empty."),
    ]

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for record in self:
            if record.parent_id:
                record.complete_name = (
                    f"{record.parent_id.complete_name} / {record.name}"
                )
            else:
                record.complete_name = record.name

    @api.depends(
        "unit_ids",
        "child_ids.unit_ids",
        "child_ids.child_ids.unit_ids",
        "child_ids.child_ids.child_ids.unit_ids",
        "child_ids.child_ids.child_ids.child_ids.unit_ids",
    )
    def _compute_unit_count(self):
        unit_model = self.env["ter.use_unit"]
        for record in self:
            if not isinstance(record.id, int):
                record.unit_count = 0
                continue
            record.unit_count = unit_model.search_count(
                [("use_type_id", "child_of", record.id)]
            )

    @api.depends(
        "unit_ids",
        "unit_ids.parcel_id",
        "child_ids.unit_ids",
        "child_ids.unit_ids.parcel_id",
        "child_ids.child_ids.unit_ids",
        "child_ids.child_ids.unit_ids.parcel_id",
        "child_ids.child_ids.child_ids.unit_ids",
        "child_ids.child_ids.child_ids.unit_ids.parcel_id",
    )
    def _compute_parcel_count(self):
        unit_model = self.env["ter.use_unit"]
        for record in self:
            if not isinstance(record.id, int):
                record.parcel_count = 0
                continue
            units = unit_model.search([("use_type_id", "child_of", record.id)])
            parcels = units.mapped("parcel_id")
            record.parcel_count = len(parcels)

    @api.depends(
        "date_range_ids",
        "child_ids.date_range_ids",
        "child_ids.child_ids.date_range_ids",
        "child_ids.child_ids.child_ids.date_range_ids",
        "child_ids.child_ids.child_ids.child_ids.date_range_ids",
    )
    def _compute_date_range_count(self):
        date_range_model = self.env["date.range"]
        for record in self:
            if not isinstance(record.id, int):
                record.date_range_count = 0
                continue
            record.date_range_count = date_range_model.search_count(
                [("use_type_id", "child_of", record.id)]
            )

    @api.constrains("parent_id")
    def _check_parent_loop(self):
        for record in self:
            if not record.parent_id:
                continue
            # Prevent cycles: parent cannot be a child of the record
            if record.parent_id in record.child_ids:
                raise ValidationError(self.env._("You cannot set a child as parent."))
            if not isinstance(record.id, int):
                continue
            if record.parent_id in record.search([("id", "child_of", record.id)]):
                # This is a safe generic check; ensures no descendant becomes parent
                raise ValidationError(
                    self.env._("You cannot create recursive hierarchies (loops).")
                )

    def action_view_descendants(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Descendants of %(name)s", name=self.display_name),
            "res_model": "ter.use_type",
            "view_mode": "list,form",
            "domain": [("id", "child_of", self.id), ("id", "!=", self.id)],
            "context": {"search_default_group_by_parent": 1},
        }

    def action_view_ancestors(self):
        self.ensure_one()
        ancestors = self.search([("id", "parent_of", self.id)])
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Ancestors of %(name)s", name=self.display_name),
            "res_model": "ter.use_type",
            "view_mode": "list,form",
            "domain": [("id", "in", ancestors.ids)],
            "context": {"search_default_group_by_parent": 1},
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
            "views": [(list_view.id, "list"), (form_view.id, "form")],
            "search_view_id": search_view.id,
            "domain": [("use_type_id", "child_of", self.id)],
        }

    def action_show_parcels(self):
        self.ensure_one()
        unit_model = self.env["ter.use_unit"]
        units = unit_model.search([("use_type_id", "child_of", self.id)])
        parcel_ids = units.mapped("parcel_id").ids
        tree_view = self.env.ref("base_ter.ter_parcel_view_tree")
        form_view = self.env.ref("base_ter.ter_parcel_view_form")
        search_view = self.env.ref("base_ter.ter_parcel_view_search")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Parcels"),
            "res_model": "ter.parcel",
            "view_mode": "list,form",
            "views": [(tree_view.id, "list"), (form_view.id, "form")],
            "search_view_id": search_view.id,
            "domain": [("id", "in", parcel_ids)] if parcel_ids else [("id", "=", 0)],
        }

    def action_show_date_ranges(self):
        self.ensure_one()
        tree_view = self.env.ref("base_ter.view_date_range_list")
        form_view = self.env.ref("base_ter.view_date_range_form_view")
        search_view = self.env.ref("base_ter.view_date_range_search")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Date Ranges"),
            "res_model": "date.range",
            "view_mode": "list,form",
            "views": [(tree_view.id, "list"), (form_view.id, "form")],
            "search_view_id": search_view.id,
            "domain": [("use_type_id", "child_of", self.id)],
        }

    all_attribute_ids = fields.Many2many(
        comodel_name="ter.use_type.attribute",
        compute="_compute_all_attribute_ids",
        string="All Attributes",
        store=False,
    )

    def _compute_all_attribute_ids(self):
        for record in self:
            if not isinstance(record.id, int):
                record.all_attribute_ids = record.attribute_ids
                continue
            ancestors = self.search(
                [
                    ("id", "parent_of", record.id),
                ]
            )
            record.all_attribute_ids = (
                ancestors.mapped("attribute_ids") | record.attribute_ids
            )
