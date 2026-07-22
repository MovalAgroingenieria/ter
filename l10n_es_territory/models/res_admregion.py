# Copyright 2024-2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResAdmregion(models.Model):
    _inherit = "res.admregion"

    number_of_municipalities = fields.Integer(
        string="Number of municipalities",
        compute="_compute_number_of_municipalities",
    )
    number_of_places = fields.Integer(
        string="Number of places",
        compute="_compute_number_of_places",
    )

    def _compute_number_of_municipalities(self):
        grouped = self.env["res.municipality"].read_group(
            [("region_id", "in", self.ids)],
            ["region_id"],
            ["region_id"],
        )
        count_by_region = {
            item["region_id"][0]: item["region_id_count"]
            for item in grouped
            if item.get("region_id")
        }
        for record in self:
            record.number_of_municipalities = count_by_region.get(record.id, 0)

    def _compute_number_of_places(self):
        grouped = self.env["res.place"].read_group(
            [("region_id", "in", self.ids)],
            ["region_id"],
            ["region_id"],
        )
        count_by_region = {
            item["region_id"][0]: item["region_id_count"]
            for item in grouped
            if item.get("region_id")
        }
        for record in self:
            record.number_of_places = count_by_region.get(record.id, 0)

    def action_show_municipalities(self):
        self.ensure_one()
        tree_view = self.env.ref(
            "base_adi.res_municipality_view_list", raise_if_not_found=False
        )
        form_view = self.env.ref(
            "base_adi.res_municipality_view_form", raise_if_not_found=False
        )
        search_view = self.env.ref(
            "base_adi.res_municipality_view_search", raise_if_not_found=False
        )
        kanban_view = self.env.ref(
            "l10n_es_territory.res_municipality_view_kanban", raise_if_not_found=False
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
            "name": self.env._("Municipalities"),
            "res_model": "res.municipality",
            "view_mode": "kanban,list,form",
            "views": views or [(False, "kanban"), (False, "list"), (False, "form")],
            "search_view_id": search_view.id if search_view else False,
            "target": "current",
            "domain": [("region_id", "=", self.id)],
            "context": {},
        }

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
            "domain": [("region_id", "=", self.id)],
            "context": {},
        }
