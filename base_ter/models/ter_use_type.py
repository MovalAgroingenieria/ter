from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class UseType(models.Model):
    _name = "ter.use_type"
    _description = "Ter Use Type"
    _parent_name = "parent_id"
    _parent_store = True
    _order = "parent_path, sequence, name"
    _rec_name = "complete_name"

    name = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10, index=True)
    active = fields.Boolean(default=True)

    parent_id = fields.Many2one(
        comodel_name="ter.use_type",
        string="Parent",
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
        index=True,
        readonly=True,
    )

    color = fields.Integer(string="Color Index")
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
                record.complete_name = f"{record.parent_id.complete_name} / {record.name}"
            else:
                record.complete_name = record.name

    @api.constrains("parent_id")
    def _check_parent_loop(self):
        for record in self:
            if not record.parent_id:
                continue
            # Prevent cycles: parent cannot be a child of the record
            if record.parent_id in record.child_ids:
                raise ValidationError(_("You cannot set a child as parent."))
            if record.parent_id in record.search([("id", "child_of", record.id)]):
                # This is a safe generic check; ensures no descendant becomes parent
                raise ValidationError(_("You cannot create recursive hierarchies (loops)."))

    def action_view_descendants(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Descendants of %s") % self.display_name,
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
            "name": _("Ancestors of %s") % self.display_name,
            "res_model": "ter.use_type",
            "view_mode": "list,form",
            "domain": [("id", "in", ancestors.ids)],
            "context": {"search_default_group_by_parent": 1},
        }

    all_attribute_ids = fields.Many2many(
        comodel_name="ter.use_type.attribute",
        compute="_compute_all_attribute_ids",
        string="All Attributes",
        store=False,
    )

    def _compute_all_attribute_ids(self):
        for record in self:
            ancestors = self.search([
                ("id", "parent_of", record.id),
            ])
            record.all_attribute_ids = (
                    ancestors.mapped("attribute_ids")
                    | record.attribute_ids
            )