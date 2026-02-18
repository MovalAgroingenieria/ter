/** @odoo-module **/
// Copyright 2026 Moval Agroingeniería S.L.
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import {registry} from "@web/core/registry";
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {kanbanView} from "@web/views/kanban/kanban_view";

const KANBAN_LIMIT = 20;

export class BaseTerParcelKanbanController extends KanbanController {
}

export const terParcelKanbanView = {
    ...kanbanView,
    Controller: BaseTerParcelKanbanController,
    props: (genericProps, view) => ({
        ...kanbanView.props(genericProps, view),
        limit: KANBAN_LIMIT,
    }),
};

registry.category("views").add("ter_parcel_view_kanban", terParcelKanbanView);
