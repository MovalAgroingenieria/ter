# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, fields, models


class TerProfile(models.Model):
    _name = "ter.profile"
    _description = "Partner Profile"
    _inherit = "simple.model"

    _set_num_code = False
    _sequence_for_codes = ""
    _size_name = 25
    _minlength = 0
    _maxlength = 25
    _allowed_blanks_in_code = True
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = False
    _size_description = 75

    alphanum_code = fields.Char(string="Profile", required=True, translate=True)

    requires_total = fields.Boolean(string="Required 100%", default=True, required=True)

    is_standard = fields.Boolean(string="Standard Type (y/n)", default=False)

    active = fields.Boolean(default=True)

    @api.model
    def _ensure_ter_profile_01(self):
        """Ensure default profile base_ter.ter_profile_01 exists (e.g. after migration
        or when base_ter was installed without loading ter_profile_data.xml).
        Returns the record. Used by ter.parcel.partnerlink default and
        base_ter_invoicing.
        """
        profile = self.env.ref("base_ter.ter_profile_01", raise_if_not_found=False)
        if profile:
            return profile
        profile = self.create(
            {
                "alphanum_code": "Owner",
                "requires_total": True,
                "is_standard": True,
            }
        )
        self.env["ir.model.data"].create(
            {
                "name": "ter_profile_01",
                "module": "base_ter",
                "model": "ter.profile",
                "res_id": profile.id,
                "noupdate": True,
            }
        )
        return profile

    @api.ondelete(at_uninstall=False)
    def _unlink_except_standard(self):
        if any(self.mapped("is_standard")):
            raise exceptions.UserError(
                self.env._("It is not possible to remove a 'STANDARD' partner profile.")
            )
