/** @odoo-module **/

import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {session} from "@web/session";
import {_t} from "@web/core/l10n/translation";

/* global L */

const {Component, onMounted, onWillUnmount, useRef} = owl;

// The original parcel geometry is drawn as a bright dashed outline with no
// fill, always on top, so it stays visible over the orthophoto and over a
// cadastral parcel that overlaps it almost completely.
const PARCEL_STYLE = {
    color: "#ffd500",
    weight: 3,
    opacity: 1,
    dashArray: "6 6",
    fill: false,
};
const CANDIDATE_STYLE = {color: "#1f78ff", weight: 2, fillOpacity: 0.2};
const SELECTED_STYLE = {color: "#2ecc40", weight: 3, fillOpacity: 0.4};
const DEFAULT_TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const DEFAULT_COPYRIGHT =
    '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';

export class CadastreCompareMap extends Component {
    static template = "l10n_es_territory.CadastreCompareMap";
    static props = {...standardFieldProps};

    setup() {
        this.mapRef = useRef("map");
        this.leafletMap = null;
        this.candidateLayers = [];
        this.bounds = null;
        onMounted(() => this.renderMap());
        onWillUnmount(() => {
            if (this.leafletMap) {
                this.leafletMap.remove();
                this.leafletMap = null;
            }
        });
    }

    get mapData() {
        return this.props.record.data.map_data || {};
    }

    get selectedRefcat() {
        return this.props.record.data[this.props.name] || "";
    }

    getTileUrl() {
        // web_leaflet_lib ships "leaflet.tile_url" as the string "False" so an
        // administrator can plug in their own tile server; fall back to OSM
        // whenever the configured value is not a usable tile template.
        const url = session["leaflet.tile_url"];
        if (typeof url === "string" && url.includes("{z}")) {
            return url;
        }
        return DEFAULT_TILE_URL;
    }

    renderMap() {
        const mapDiv = this.mapRef.el;
        if (!mapDiv || typeof L === "undefined") {
            return;
        }
        this.leafletMap = L.map(mapDiv, {minZoom: 1, maxZoom: 19}).setView(
            [40.0, -3.7],
            5
        );
        L.tileLayer(this.getTileUrl(), {
            maxZoom: 19,
            attribution: session["leaflet.copyright"] || DEFAULT_COPYRIGHT,
        }).addTo(this.leafletMap);
        this.drawLayers();
        this.fitToData();
    }

    fitToData() {
        // The map is rendered inside a dialog; wait for the layout to settle
        // so the container has a real size before recomputing zoom/bounds.
        setTimeout(() => {
            if (!this.leafletMap) {
                return;
            }
            this.leafletMap.invalidateSize();
            if (this.bounds && this.bounds.isValid()) {
                this.leafletMap.fitBounds(this.bounds, {
                    padding: [20, 20],
                    maxZoom: 18,
                });
            }
        }, 300);
    }

    drawLayers() {
        const data = this.mapData;
        let bounds = null;
        this.candidateLayers = [];
        this.candidatesGroup = L.layerGroup();
        for (const candidate of data.candidates || []) {
            if (!candidate.geojson) {
                continue;
            }
            const selected = candidate.refcat === this.selectedRefcat;
            const layer = L.geoJSON(JSON.parse(candidate.geojson), {
                style: selected ? SELECTED_STYLE : CANDIDATE_STYLE,
            });
            layer.bindTooltip(`${candidate.refcat} (${candidate.intersection}%)`);
            layer.on("click", () => this.selectCandidate(candidate.refcat));
            this.candidatesGroup.addLayer(layer);
            this.candidateLayers.push({refcat: candidate.refcat, layer});
            const candidateBounds = layer.getBounds();
            bounds = bounds ? bounds.extend(candidateBounds) : candidateBounds;
        }
        this.candidatesGroup.addTo(this.leafletMap);
        this.parcelLayer = null;
        if (data.parcel) {
            this.parcelLayer = L.geoJSON(JSON.parse(data.parcel), {
                style: PARCEL_STYLE,
            });
            this.parcelLayer.addTo(this.leafletMap);
            this.parcelLayer.bringToFront();
            const parcelBounds = this.parcelLayer.getBounds();
            bounds = bounds ? bounds.extend(parcelBounds) : parcelBounds;
        }
        this.bounds = bounds;
        this.addLayerControl();
    }

    addLayerControl() {
        const overlays = {};
        if (this.parcelLayer) {
            overlays[_t("Original geometry")] = this.parcelLayer;
        }
        if (this.candidatesGroup) {
            overlays[_t("Cadastral parcels")] = this.candidatesGroup;
        }
        if (Object.keys(overlays).length) {
            L.control
                .layers(null, overlays, {collapsed: false})
                .addTo(this.leafletMap);
        }
    }

    async selectCandidate(refcat) {
        await this.props.record.update({[this.props.name]: refcat});
        for (const item of this.candidateLayers) {
            item.layer.setStyle(
                item.refcat === refcat ? SELECTED_STYLE : CANDIDATE_STYLE
            );
        }
        if (this.parcelLayer) {
            this.parcelLayer.bringToFront();
        }
    }
}

export const cadastreCompareMap = {
    component: CadastreCompareMap,
    supportedTypes: ["char"],
};

registry.category("fields").add("cadastre_compare_map", cadastreCompareMap);
