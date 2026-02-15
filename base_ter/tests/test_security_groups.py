# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSecurityGroups(TransactionCase):
    def test_groups_exist_and_imply_chain(self):
        group_user = self.env.ref("base_ter.group_ter_user")
        group_manager = self.env.ref("base_ter.group_ter_manager")
        group_director = self.env.ref("base_ter.group_ter_director")

        self.assertIn(self.env.ref("base.group_user"), group_user.implied_ids)
        self.assertIn(group_user, group_manager.implied_ids)
        self.assertIn(group_manager, group_director.implied_ids)
