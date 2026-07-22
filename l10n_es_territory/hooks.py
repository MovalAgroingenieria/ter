# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
def post_init_hook(env):
    # Initialize default company parameters for the main company.
    company = env.company
    company.write(
        {
            "aerial_image_wmsbase_url": "https://www.ign.es/wms-inspire/pnoa-ma",
            "aerial_image_wmsbase_layers": "OI.OrthoimageCoverage",
        }
    )
