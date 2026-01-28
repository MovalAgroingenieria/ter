# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
# pylint: disable=protected-access
# pylint: disable=duplicate-code

from unittest import mock

from odoo.tests.common import TransactionCase


class TestTerSigpac(TransactionCase):
    def test_compute_sigpac_link_renders_template(self):
        sigpac = self.env["ter.sigpac"].new({"name": "SIGPAC-001"})
        with mock.patch.object(
            type(self.env["ir.config_parameter"].sudo()),
            "get_param",
            return_value="https://example.com/{{ object.name }}",
        ):
            sigpac._compute_sigpac_link()
        self.assertEqual(sigpac.sigpac_link, "https://example.com/SIGPAC-001")

    def test_compute_sigpac_link_invalid_template_falls_back(self):
        sigpac = self.env["ter.sigpac"].new({"name": "SIGPAC-002"})
        with mock.patch.object(
            type(self.env["ir.config_parameter"].sudo()),
            "get_param",
            return_value="https://example.com/{{ object.name",
        ):
            sigpac._compute_sigpac_link()
        self.assertEqual(sigpac.sigpac_link, "https://example.com/{{ object.name")

    def test_compute_number_of_sigpaclinks(self):
        sigpac = self.env["ter.sigpac"].new({})
        # One2many on new() behaves as empty recordset
        sigpac._compute_number_of_sigpaclinks()
        self.assertEqual(sigpac.number_of_sigpaclinks, 0)

    def test_action_sigpac_viewer_returns_false_without_url(self):
        sigpac = self.env["ter.sigpac"].new({})
        sigpac.sigpac_link = ""
        self.assertFalse(sigpac.action_sigpac_viewer())
