# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


def _ensure_fsm_prerequisites(env):
    """Guarantee that FSM order creation never fails for lack of setup.

    ``fsm.order._default_stage_id`` raises "You must create an FSM order
    stage first." when there is no default order stage, and
    ``_default_team_id`` raises a similar error without a team.  The
    fieldservice default stages are ``noupdate`` data, so a database that
    lost them (or has them assigned to another company) breaks both the
    manual creation and the Geofolia import.  Recreate the minimum setup.
    """
    stage_obj = env["fsm.stage"]
    order_stages = stage_obj.search(
        [("stage_type", "=", "order")], order="sequence asc"
    )
    if not order_stages:
        stage_obj.create(
            [
                {
                    "name": env._("New"),
                    "sequence": 10,
                    "is_default": True,
                    "stage_type": "order",
                },
                {
                    "name": env._("Completed"),
                    "sequence": 80,
                    "is_default": True,
                    "stage_type": "order",
                    "is_closed": True,
                },
                {
                    "name": env._("Cancelled"),
                    "sequence": 100,
                    "is_default": True,
                    "stage_type": "order",
                    "is_closed": True,
                    "fold": True,
                },
            ]
        )
    elif not order_stages.filtered("is_default"):
        order_stages.write({"is_default": True})
    if not env["fsm.team"].search([], limit=1):
        env["fsm.team"].create({"name": env._("Field Service")})


def post_init_hook(env):
    """Load i18n_extra translations and ensure FSM prerequisites."""
    _ensure_fsm_prerequisites(env)
    module = env["ir.module.module"].search(
        [("name", "=", "ter_analytic_geofolia")], limit=1
    )
    if module:
        module._update_translations(overwrite=True)  # pylint: disable=protected-access
