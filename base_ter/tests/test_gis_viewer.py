# pylint: disable=invalid-name,protected-access
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

    def _new_parcel(self, **vals):
        """Create an in-memory parcel record for GIS viewer tests.

        We use `new()` to avoid creating the full administrative chain
        (admregion/province/municipality) which is not relevant for the
        viewer URL logic.
        """
        defaults = {
            "name": "P-001",
            # keep it aligned with expected assertions in tests
            "bounding_box_str": "(0.0,0.0,10.0,10.0)",
        }
        defaults.update(vals)
        return self.env["ter.parcel"].new(defaults)

    def test_compute_gis_code(self):
        rec = self._new_parcel(name="P-001")
        self.assertEqual(rec.gis_code, "P-001")

    def test_get_gis_link_empty_when_not_mapped(self):
        rec = self._new_parcel(name="P-001", mapped_to_polygon=False)
        self.assertEqual(rec._get_gis_link(public=True), "")

    def test_get_encrypted_credentials_returns_base64(self):
        rec = self._new_parcel(name="P-001", mapped_to_polygon=True)

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
        rec = self._new_parcel(name="P-001", mapped_to_polygon=True)
        self.config.set_param("base_ter.gis_viewer_username", "")
        self.config.set_param("base_ter.gis_viewer_password", "")
        self.assertEqual(rec._get_encrypted_credentials(), "")
