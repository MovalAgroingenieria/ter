# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError


def check_geofolia_protected(records, vals, protected_fields, lock_field):
    """Block manual edits of Geofolia-sourced fields.

    Raises ``UserError`` when *vals* touches a protected field on a record
    that originates from Geofolia (``lock_field`` truthy), unless the write
    runs inside the import process (``geofolia_sync=True`` in the context).

    Args:
        records: recordset being written.
        vals (dict): values passed to ``write``.
        protected_fields (tuple): field names owned by Geofolia.
        lock_field (str): boolean/char field marking Geofolia origin.
    """
    if not protected_fields or records.env.context.get("geofolia_sync"):
        return
    touched = [field for field in protected_fields if field in vals]
    if not touched:
        return
    locked = records.sudo().filtered(
        lambda rec: lock_field in rec._fields and bool(rec[lock_field])
    )
    if locked:
        raise UserError(
            records.env._(
                "These fields come from Geofolia and can only be updated by "
                "re-importing from Geofolia: %(fields)s",
                fields=", ".join(sorted(touched)),
            )
        )
