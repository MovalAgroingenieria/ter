# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


def _ensure_fsm_order_stages(env):
    """Ensure at least one default FSM order stage exists (shared by all
    companies).

    ``fsm.order._default_stage_id`` raises "You must create an FSM order
    stage first." when there is no default order stage.  The fieldservice
    default stages are ``noupdate`` data, so a database that lost them (or
    has them assigned to another company) breaks both manual creation and
    the Geofolia import.  Recreate the minimum setup with
    ``company_id = False`` so every company can use them.
    """
    stage_obj = env["fsm.stage"].sudo()
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
                    "company_id": False,
                },
                {
                    "name": env._("Completed"),
                    "sequence": 80,
                    "is_default": True,
                    "stage_type": "order",
                    "is_closed": True,
                    "company_id": False,
                },
                {
                    "name": env._("Cancelled"),
                    "sequence": 100,
                    "is_default": True,
                    "stage_type": "order",
                    "is_closed": True,
                    "fold": True,
                    "company_id": False,
                },
            ]
        )
    elif not order_stages.filtered("is_default"):
        order_stages.write({"is_default": True})


def _ensure_fsm_teams(env):
    """Ensure every company has at least one FSM team.

    ``fsm.order._default_team_id`` searches for a team of the active company
    (or a company-less one).  ``fsm.team.company_id`` is ``required`` and the
    team name is globally unique, so a single shared team is impossible: we
    must create one team per company.  Without this, importing Geofolia in a
    company that has no team fails with "You must create an FSM team first.".
    """
    team_obj = env["fsm.team"].sudo()
    multi_company = env["res.company"].sudo().search_count([]) > 1
    for company in env["res.company"].sudo().search([], limit=None):
        if team_obj.search([("company_id", "=", company.id)], limit=1):
            continue
        name = env._("Field Service")
        if multi_company:
            name = "%s - %s" % (name, company.name)
        # Guarantee the globally-unique team name constraint is satisfied.
        if team_obj.search([("name", "=", name)], limit=1):
            name = "%s (%s)" % (name, company.id)
        team_obj.create({"name": name, "company_id": company.id})


def _ensure_fsm_prerequisites(env):
    """Guarantee that FSM order creation never fails for lack of setup."""
    _ensure_fsm_order_stages(env)
    _ensure_fsm_teams(env)


def post_init_hook(env):
    """Load i18n_extra translations and ensure FSM prerequisites."""
    _ensure_fsm_prerequisites(env)
    module = env["ir.module.module"].search(
        [("name", "=", "ter_analytic_geofolia")], limit=1
    )
    if module:
        module._update_translations(overwrite=True)  # pylint: disable=protected-access
