# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

"""Test helpers for base_ter tests."""


def create_administrative_chain(env):
    """Create region, province, municipality. Returns (region, province, municipality)."""
    region = env["res.admregion"].create({"name": "R1"})
    province = env["res.province"].create({"name": "P1", "region_id": region.id})
    municipality = env["res.municipality"].create(
        {"name": "M1", "province_id": province.id}
    )
    return region, province, municipality
