# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestAllowNonHolderAsManager(TransactionCase):
    """Tests for the per-parcel 'allow_non_holder_as_manager' field."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Ensure the global setting is DISABLED so the per-parcel field
        # is the only thing that can lift the restriction.
        cls.env['ir.config_parameter'].sudo().set_param(
            'base_ter.allow_non_holder_as_manager', False)

        # Region → Province → Municipality (required to create parcels).
        cls.region = cls.env['res.admregion'].create({
            'alphanum_code': 'TESTREG',
        })
        cls.province = cls.env['res.province'].create({
            'alphanum_code': 'TESTPROV',
            'region_id': cls.region.id,
        })
        cls.municipality = cls.env['res.municipality'].create({
            'alphanum_code': 'TESTMUN',
            'province_id': cls.province.id,
        })

        # Profile (needed for partnerlinks).
        cls.profile = cls.env.ref('base_ter.ter_profile_01')

        # Holder partner (partner_code > 0 → is_holder = True).
        cls.holder_partner = cls.env['res.partner'].create({
            'name': 'Holder Partner',
            'partner_code': 100,
        })

        # Non-holder partner (partner_code == 0 → is_holder = False).
        cls.non_holder_partner = cls.env['res.partner'].create({
            'name': 'Non-Holder Partner',
            'partner_code': 0,
        })

    # ------------------------------------------------------------------
    # 1. Default behaviour: field is True, non-holder is accepted
    # ------------------------------------------------------------------
    def test_01_default_value_is_true(self):
        """New parcels must have allow_non_holder_as_manager = True."""
        parcel = self.env['ter.parcel'].create({
            'alphanum_code': 'P-DEF',
            'municipality_id': self.municipality.id,
        })
        self.assertTrue(parcel.allow_non_holder_as_manager)

    def test_02_non_holder_accepted_by_default(self):
        """With the default flag ON, a non-holder manager is accepted."""
        parcel = self.env['ter.parcel'].create({
            'alphanum_code': 'P-DEFOK',
            'municipality_id': self.municipality.id,
            'partner_id': self.non_holder_partner.id,
            'partnerlink_ids': [(0, 0, {
                'partner_id': self.non_holder_partner.id,
                'profile_id': self.profile.id,
                'is_main': True,
                'percentage': 100,
            })],
        })
        self.assertEqual(parcel.partner_id, self.non_holder_partner)

    def test_02b_non_holder_rejected_when_flag_is_false(self):
        """With the flag explicitly OFF, assigning a non-holder must raise."""
        with self.assertRaises(ValidationError):
            self.env['ter.parcel'].create({
                'alphanum_code': 'P-FAIL',
                'municipality_id': self.municipality.id,
                'allow_non_holder_as_manager': False,
                'partner_id': self.non_holder_partner.id,
                'partnerlink_ids': [(0, 0, {
                    'partner_id': self.non_holder_partner.id,
                    'profile_id': self.profile.id,
                    'is_main': True,
                    'percentage': 100,
                })],
            })

    # ------------------------------------------------------------------
    # 2. Per-parcel flag enabled: non-holder is accepted
    # ------------------------------------------------------------------
    def test_03_non_holder_accepted_when_parcel_flag_is_true(self):
        """With the per-parcel flag ON, a non-holder manager is allowed."""
        parcel = self.env['ter.parcel'].create({
            'alphanum_code': 'P-OK',
            'municipality_id': self.municipality.id,
            'allow_non_holder_as_manager': True,
            'partner_id': self.non_holder_partner.id,
            'partnerlink_ids': [(0, 0, {
                'partner_id': self.non_holder_partner.id,
                'profile_id': self.profile.id,
                'is_main': True,
                'percentage': 100,
            })],
        })
        self.assertEqual(parcel.partner_id, self.non_holder_partner)

    # ------------------------------------------------------------------
    # 3. Holder always works, regardless of flag
    # ------------------------------------------------------------------
    def test_04_holder_accepted_when_flag_is_false(self):
        """A holder partner is always valid, even without the flag."""
        parcel = self.env['ter.parcel'].create({
            'alphanum_code': 'P-HOLD',
            'municipality_id': self.municipality.id,
            'allow_non_holder_as_manager': False,
            'partner_id': self.holder_partner.id,
            'partnerlink_ids': [(0, 0, {
                'partner_id': self.holder_partner.id,
                'profile_id': self.profile.id,
                'is_main': True,
                'percentage': 100,
            })],
        })
        self.assertEqual(parcel.partner_id, self.holder_partner)

    # ------------------------------------------------------------------
    # 4. Toggling the flag on an existing parcel
    # ------------------------------------------------------------------
    def test_05_toggle_flag_allows_non_holder_on_existing_parcel(self):
        """Enabling the flag on an existing parcel lets a non-holder in."""
        parcel = self.env['ter.parcel'].create({
            'alphanum_code': 'P-TOG',
            'municipality_id': self.municipality.id,
        })
        # Enable the flag and assign non-holder.
        parcel.write({
            'allow_non_holder_as_manager': True,
            'partner_id': self.non_holder_partner.id,
            'partnerlink_ids': [(0, 0, {
                'partner_id': self.non_holder_partner.id,
                'profile_id': self.profile.id,
                'is_main': True,
                'percentage': 100,
            })],
        })
        self.assertEqual(parcel.partner_id, self.non_holder_partner)

    def test_06_disable_flag_rejects_non_holder(self):
        """Disabling the flag must reject a non-holder manager."""
        parcel = self.env['ter.parcel'].create({
            'alphanum_code': 'P-DIS',
            'municipality_id': self.municipality.id,
            'allow_non_holder_as_manager': True,
            'partner_id': self.non_holder_partner.id,
            'partnerlink_ids': [(0, 0, {
                'partner_id': self.non_holder_partner.id,
                'profile_id': self.profile.id,
                'is_main': True,
                'percentage': 100,
            })],
        })
        with self.assertRaises(ValidationError):
            parcel.write({'allow_non_holder_as_manager': False})

    # ------------------------------------------------------------------
    # 5. Global config still works as fallback
    # ------------------------------------------------------------------
    def test_07_global_config_overrides_parcel_flag(self):
        """If the global setting is ON, non-holders are allowed everywhere,
        even on parcels where the per-parcel flag is OFF."""
        self.env['ir.config_parameter'].sudo().set_param(
            'base_ter.allow_non_holder_as_manager', True)
        try:
            parcel = self.env['ter.parcel'].create({
                'alphanum_code': 'P-GLB',
                'municipality_id': self.municipality.id,
                'allow_non_holder_as_manager': False,
                'partner_id': self.non_holder_partner.id,
                'partnerlink_ids': [(0, 0, {
                    'partner_id': self.non_holder_partner.id,
                    'profile_id': self.profile.id,
                    'is_main': True,
                    'percentage': 100,
                })],
            })
            self.assertEqual(parcel.partner_id, self.non_holder_partner)
        finally:
            # Restore the global setting for other tests.
            self.env['ir.config_parameter'].sudo().set_param(
                'base_ter.allow_non_holder_as_manager', False)
