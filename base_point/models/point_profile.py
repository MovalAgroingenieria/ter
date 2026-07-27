# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, fields, models


class PointProfile(models.Model):
    _name = "point.profile"
    _description = "Point Partner Profile"
    _inherit = "simple.model"

    size_name = 25
    maxlength = 25
    allowed_blanks_in_code = True

    alphanum_code = fields.Char(string="Profile", required=True, translate=True)
    requires_total = fields.Boolean(string="Required 100%", default=True, required=True)
    is_standard = fields.Boolean(default=False)
    active = fields.Boolean(default=True)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_standard(self):
        if any(self.mapped("is_standard")):
            raise exceptions.UserError(
                self.env._("It is not possible to remove a 'STANDARD' partner profile.")
            )
