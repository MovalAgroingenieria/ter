# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResProvince(models.Model):
    _inherit = "res.province"

    image_128 = fields.Image(
        string="Image",
        max_width=128,
        max_height=128,
    )
    number_of_places = fields.Integer(
        string="Number of places",
        compute="_compute_number_of_places",
    )
    cadastral_code = fields.Integer(
        required=True,
        index=True,
    )

    def _compute_number_of_places(self):
        grouped = self.env["res.place"].read_group(
            [("province_id", "in", self.ids)],
            ["province_id"],
            ["province_id"],
        )
        count_by_province = {
            item["province_id"][0]: item["province_id_count"]
            for item in grouped
            if item.get("province_id")
        }
        for record in self:
            record.number_of_places = count_by_province.get(record.id, 0)

    def action_show_places(self):
        self.ensure_one()
        tree_view = self.env.ref(
            "base_adi.res_place_view_list", raise_if_not_found=False
        )
        form_view = self.env.ref(
            "base_adi.res_place_view_form", raise_if_not_found=False
        )
        search_view = self.env.ref(
            "base_adi.res_place_view_search", raise_if_not_found=False
        )
        kanban_view = self.env.ref(
            "l10n_es_territory.res_place_view_kanban", raise_if_not_found=False
        )
        views = []
        if kanban_view:
            views.append((kanban_view.id, "kanban"))
        if tree_view:
            views.append((tree_view.id, "list"))
        if form_view:
            views.append((form_view.id, "form"))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Places"),
            "res_model": "res.place",
            "view_mode": "kanban,list,form",
            "views": views or [(False, "kanban"), (False, "list"), (False, "form")],
            "search_view_id": search_view.id if search_view else False,
            "target": "current",
            "domain": [("province_id", "=", self.id)],
            "context": {},
        }

    @api.constrains("cadastral_code")
    def _check_cadastral_code_positive(self):
        for record in self:
            if record.cadastral_code is not None and record.cadastral_code <= 0:
                raise ValidationError(
                    self.env._("A valid cadastral code of province is required.")
                )

    @api.constrains("cadastral_code")
    def _check_cadastral_code_unique(self):
        for record in self:
            if not record.cadastral_code:
                continue
            if self.search_count(
                [
                    ("id", "!=", record.id),
                    ("cadastral_code", "=", record.cadastral_code),
                ]
            ):
                raise ValidationError(self.env._("Repeated province code."))
