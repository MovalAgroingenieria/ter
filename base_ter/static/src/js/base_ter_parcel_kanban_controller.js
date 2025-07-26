/** @odoo-module **/

import { registry } from "@web/core/registry";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";

const KANBAN_LIMIT = 20;

export class BaseTerParcelKanbanController extends KanbanController {
    setup() {
        this.props.limit = KANBAN_LIMIT;
        super.setup();
    }
};

registry.category('views').add('ter_parcel_view_kanban', {
    ...kanbanView,
    Controller: BaseTerParcelKanbanController,
});
