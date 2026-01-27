from unittest import mock

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResPartnerMapping(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Base Mapping Partner",
                "mapped_to_base": True,
                "base_connection_host": "https://example.test/",
                "base_connection_port": 0,
                "base_connection_company_id": 1,
                "base_connection_database": "db_test",
                "base_connection_username": "user_test",
                "base_connection_password": "pwd_test",
                "partner_code": "990001",
            }
        )

    def test_host_constraint_requires_scheme(self):
        partner = self.env["res.partner"].create({"name": "No scheme"})
        with self.assertRaises(ValidationError):
            partner.base_connection_host = "example.test"
            partner._check_base_connection_host()

    def test_host_constraint_strips_trailing_slash(self):
        self.partner.base_connection_host = "https://example.test/"
        self.partner._check_base_connection_host()
        self.assertEqual(self.partner.base_connection_host, "https://example.test")

    def test_port_constraint_range(self):
        with self.assertRaises(ValidationError):
            self.partner.base_connection_port = 70000
            self.partner._check_base_connection_port()

    def test_get_port_defaults(self):
        self.assertEqual(self.partner._get_port("http://a", 0), 80)
        self.assertEqual(self.partner._get_port("https://a", 0), 443)
        self.assertEqual(self.partner._get_port("https://a", 1234), 1234)

    def test_get_connection_params_requires_mandatory(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Missing params",
                "mapped_to_base": True,
                "base_connection_host": "https://example.test",
                "base_connection_database": False,
                "base_connection_username": "u",
                "base_connection_password": "p",
            }
        )
        with self.assertRaises(UserError):
            partner._get_connection_params()

    def test_check_odoo_rpc_connection_handles_oserror(self):
        with mock.patch("socket.create_connection", side_effect=OSError("no route")):
            with self.assertRaises(ValidationError):
                self.partner._check_odoo_rpc_connection("https://example.test", 443)

    def test_check_connection_success(self):
        def fake_execute_kw(database, uid, password, model, method, args, kwargs=None):
            kwargs = kwargs or {}
            if (model, method) == ("res.company", "fields_get"):
                return {"general_code": {"type": "char"}}
            if (model, method) == ("res.company", "search"):
                return [1]
            return []

        class FakeCommon:
            def authenticate(self, database, username, password, context):
                return 7

        class FakeModels:
            def execute_kw(
                self, database, uid, password, model, method, args, kwargs=None
            ):
                return fake_execute_kw(
                    database, uid, password, model, method, args, kwargs
                )

        def fake_server_proxy(url):
            if url.endswith("/xmlrpc/2/common"):
                return FakeCommon()
            return FakeModels()

        with mock.patch("socket.create_connection") as m_conn, mock.patch(
            "xmlrpc.client.ServerProxy", side_effect=fake_server_proxy
        ):
            m_conn.return_value.__enter__.return_value = True
            rpc_models, uid, password, database, company_id = (
                self.partner._check_connection()
            )
            self.assertEqual(uid, 7)
            self.assertEqual(database, "db_test")
            self.assertEqual(company_id, 1)
            self.assertTrue(rpc_models)
            self.assertEqual(password, "pwd_test")
