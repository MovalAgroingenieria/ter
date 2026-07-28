# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

PNOA_TILE_URL = (
    "https://www.ign.es/wmts/pnoa-ma?service=WMTS&request=GetTile"
    "&version=1.0.0&layer=OI.OrthoimageCoverage&style=default"
    "&format=image/jpeg&tilematrixset=GoogleMapsCompatible"
    "&TileMatrix={z}&TileCol={x}&TileRow={y}"
)
PNOA_COPYRIGHT = (
    "© <a href='https://www.ign.es'>Instituto Geográfico Nacional</a> (PNOA)"
)


def set_default_leaflet_pnoa(env):
    """Use the PNOA orthophoto as the default Leaflet base layer.

    ``web_leaflet_lib`` ships ``leaflet.tile_url`` as the string ``"False"`` so
    each installation plugs in its own tile server. Only that default value is
    replaced, never a custom URL an administrator may have configured.
    """
    params = env["ir.config_parameter"].sudo()
    current = (params.get_param("leaflet.tile_url") or "").strip()
    if current in ("", "False", "false"):
        params.set_param("leaflet.tile_url", PNOA_TILE_URL)
        params.set_param("leaflet.copyright", PNOA_COPYRIGHT)


def post_init_hook(env):
    # Initialize default company parameters for the main company.
    company = env.company
    company.write(
        {
            "aerial_image_wmsbase_url": "https://www.ign.es/wms-inspire/pnoa-ma",
            "aerial_image_wmsbase_layers": "OI.OrthoimageCoverage",
        }
    )
    set_default_leaflet_pnoa(env)
