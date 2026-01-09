import re
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestGisViewer(TransactionCase):
    def setUp(self):
        super().setUp()
        self.config = self.env["ir.config_parameter"].sudo()

        self.config.set_param("base_ter.gis_viewer_url", "https://example.test/gis")
        self.config.set_param("base_ter.gis_viewer_username", "user")
        self.config.set_param("base_ter.gis_viewer_password", "pass")
        self.config.set_param("base_ter.gis_viewer_cipher_key", "z%C*F-JaNdRgUkXp")
        self.config.set_param("base_ter.gis_viewer_previs_additional_args", "mode=min")

    def _create(self, **vals):
        return self.env["gis.viewer.test.model"].create(vals)

    def test_compute_gis_code(self):
        rec = self._create(name="P-001")
        rec.flush_recordset()
        self.assertEqual(rec.gis_code, "P-001")

    def test_get_gis_link_empty_when_not_mapped(self):
        rec = self._create(name="P-001", mapped_to_polygon=False)
        self.assertEqual(rec._get_gis_link(public=True), "")

    def test_get_gis_link_minimal(self):
        rec = self._create(name="P-001", mapped_to_polygon=True)
        url = rec._get_gis_link(public=True, minimal=True)
        self.assertIn("https://example.test/gis?", url)
        self.assertIn("idparcela=P-001", url)
        self.assertIn("bbox=0.0,0.0,10.0,10.0", url)
        self.assertIn("&mode=min", url)

    def test_action_gis_viewer_builds_url(self):
        rec1 = self._create(name="P-001", mapped_to_polygon=True)
        rec2 = self._create(name="P-002", mapped_to_polygon=True)

        action = (rec1 | rec2).action_gis_viewer()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["target"], "new")

        url = action["url"]
        self.assertIn("https://example.test/gis?arg=", url)
        self.assertIn("&idparcela=P-001,P-002", url)
        self.assertIn("&bbox=0.0,0.0,10.0,10.0", url)

    def test_get_encrypted_credentials_returns_base64(self):
        rec = self._create(name="P-001", mapped_to_polygon=True)

        class _FakeSession:
            sid = "SID123"

        class _FakeRequest:
            session = _FakeSession()

        with patch("odoo.addons.base_ter.models.gis_viewer.request", _FakeRequest()):
            token = rec._get_encrypted_credentials()

        self.assertTrue(token)
        self.assertRegex(token, r"^[A-Za-z0-9+/=]+$")
        self.assertEqual(len(token) % 4, 0)

    def test_get_encrypted_credentials_empty_without_config(self):
        rec = self._create(name="P-001", mapped_to_polygon=True)
        self.config.set_param("base_ter.gis_viewer_username", "")
        self.config.set_param("base_ter.gis_viewer_password", "")
        self.assertEqual(rec._get_encrypted_credentials(), "")
