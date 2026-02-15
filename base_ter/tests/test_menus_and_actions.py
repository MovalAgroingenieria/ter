# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMenusAndActions(TransactionCase):
    def test_global_viewer_server_action_exists(self):
        action = self.env.ref("base_ter.gisviewer_global_serveraction")
        self.assertEqual(action.state, "code")
        self.assertEqual(action.model_id.model, "ter.parcel")

    def test_menus_exist(self):
        self.env.ref("base_ter.menu_census")
        self.env.ref("base_ter.menu_viewer")
        self.env.ref("base_ter.menu_thecnicalactions")

    def test_cron_act_window_domain(self):
        act = self.env.ref("base_ter.ir_cron_action")
        self.assertIn("is_base_ter", act.domain or "")
