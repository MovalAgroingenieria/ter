# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(cr, version):
    """Rename view xml_ids to follow OCA naming convention."""
    xml_spec = [
        (
            "base_point.view_point_point_tree",
            "base_point.point_point_view_list",
        ),
        (
            "base_point.view_point_pointtag_tree",
            "base_point.point_pointtag_view_list",
        ),
        (
            "base_point.view_point_profile_tree",
            "base_point.point_profile_view_list",
        ),
        (
            "base_point.view_partner_form_inherit_base_point",
            "base_point.view_partner_form",
        ),
    ]
    openupgrade.rename_xmlids(cr.cr if hasattr(cr, "cr") else cr, xml_spec)
