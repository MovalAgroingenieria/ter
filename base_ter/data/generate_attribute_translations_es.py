#!/usr/bin/env python3
# Copyright 2026 Moval Agroingenieria S.L.
# Generates data/attribute_translations_es.json: xmlid -> es_ES name for
# ter.use_type.attribute and ter.use_type.attribute.value (bilingual default en/es).
# Run after the other generate_* scripts. Module prefix: base_ter.

import csv
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

MODULE = "base_ter"

# --- Static (ter_use_type_data.xml) ---
STATIC_ES = {
    f"{MODULE}.ter_attr_cultivable_farming": "Cultivable",
    f"{MODULE}.ter_attr_cultivable_farming_yes": "Sí",
    f"{MODULE}.ter_attr_cultivable_livestock": "Cultivable",
    f"{MODULE}.ter_attr_cultivable_livestock_no": "No",
    f"{MODULE}.ter_attr_cultivable_industrial": "Cultivable",
    f"{MODULE}.ter_attr_cultivable_industrial_no": "No",
    f"{MODULE}.ter_attr_cultivable_urban": "Cultivable",
    f"{MODULE}.ter_attr_cultivable_urban_no": "No",
    f"{MODULE}.ter_attr_cultivable_recreational": "Cultivable",
    f"{MODULE}.ter_attr_cultivable_recreational_no": "No",
    f"{MODULE}.ter_attr_cultivable_water_reservoir": "Cultivable",
    f"{MODULE}.ter_attr_cultivable_water_reservoir_no": "No",
}

# Destino del cultivo: attribute + values (Spanish from CSV)
def _destino_es(base_path):
    out = {f"{MODULE}.ter_attr_crop_destination_farming": "Destino del cultivo"}
    path = base_path / "catalogos_csv" / "Destino del cultivo.csv"
    if not path.exists():
        return out
    with open(path, encoding="latin-1", newline="") as f:
        r = csv.reader(f, delimiter=";", quotechar='"')
        next(r)
        for row in r:
            if len(row) <= 5:
                continue
            if row[5].strip():
                continue
            name = row[1].strip().strip('"')
            if not name:
                continue
            code = re.sub(r"[^a-z0-9]", "_", row[0].strip().strip('"').lower())[:50] or "val"
            out[f"{MODULE}.ter_attr_crop_destination_farming_{code}"] = name
    return out

# Procedencia del material vegetal
def _procedencia_es(base_path):
    out = {f"{MODULE}.ter_attr_plant_material_provenance_farming": "Procedencia del material vegetal"}
    path = base_path / "catalogos_csv" / "Procedencia del material vegetal.csv"
    if not path.exists():
        return out
    with open(path, encoding="latin-1", newline="") as f:
        r = csv.reader(f, delimiter=";", quotechar='"')
        next(r)
        for row in r:
            if len(row) <= 4:
                continue
            if len(row) > 4 and row[4].strip():
                continue
            name = row[1].strip().strip('"')
            if not name:
                continue
            code = row[0].strip().strip('"')
            out[f"{MODULE}.ter_attr_plant_material_provenance_farming_{code}"] = name
    return out

# Sistema de cultivo: attribute + values (Spanish from CSV)
def _sistema_cultivo_es(base_path):
    out = {f"{MODULE}.ter_attr_cultivation_system_farming": "Sistema de cultivo"}
    path = base_path / "catalogos_csv" / "Sistema de cultivo.csv"
    if not path.exists():
        return out
    with open(path, encoding="latin-1", newline="") as f:
        r = csv.reader(f, delimiter=";", quotechar='"')
        next(r)
        for row in r:
            if len(row) <= 5:
                continue
            if row[5].strip():
                continue
            name = row[1].strip().strip('"')
            if not name:
                continue
            code = re.sub(r"[^a-z0-9]", "_", row[0].strip().strip('"').lower())[:50] or "val"
            out[f"{MODULE}.ter_attr_cultivation_system_farming_{code}"] = name
    return out


# SENP: Superficies y elementos no productivos (attribute + values from CSV)
def _senp_es(base_path):
    out = {f"{MODULE}.ter_attr_senp_farming": "Superficies y elementos no productivos (SENP)"}
    path = base_path / "catalogos_csv" / "Superficies y elementos no productivos (SENP).csv"
    if not path.exists():
        return out
    with open(path, encoding="latin-1", newline="") as f:
        r = csv.reader(f, delimiter=";", quotechar='"')
        next(r)
        for idx, row in enumerate(r):
            if len(row) <= 5:
                continue
            if row[5].strip():
                continue
            name = row[2].strip().strip('"')
            if not name:
                continue
            code = row[0].strip().strip('"')
            slug = re.sub(r"[^a-z0-9]", "_", code.lower())[:50] if code else f"val_{idx + 1}"
            if not slug:
                slug = f"val_{idx + 1}"
            out[f"{MODULE}.ter_attr_senp_farming_{slug}"] = name
    return out


# Tipo de cobertura del suelo: attribute + values (Spanish from CSV)
def _cobertura_suelo_es(base_path):
    out = {f"{MODULE}.ter_attr_soil_cover_type_farming": "Tipo de cobertura del suelo"}
    path = base_path / "catalogos_csv" / "Tipo de cobertura del suelo.csv"
    if not path.exists():
        return out
    with open(path, encoding="latin-1", newline="") as f:
        r = csv.reader(f, delimiter=";", quotechar='"')
        next(r)
        for row in r:
            if len(row) <= 4:
                continue
            if row[4].strip():
                continue
            name = row[1].strip().strip('"')
            if not name:
                continue
            code = re.sub(r"[^a-z0-9]", "_", row[0].strip().strip('"').lower())[:50] or "val"
            out[f"{MODULE}.ter_attr_soil_cover_type_farming_{code}"] = name
    return out


# Producto vegetal: attribute "Producto" + values per crop
def _producto_es(base_path):
    out = {}
    cultivo_path = base_path / "catalogos_csv" / "Cultivo.csv"
    producto_path = base_path / "catalogos_csv" / "Producto Vegetal.csv"
    if not cultivo_path.exists() or not producto_path.exists():
        return out
    active_codes = set()
    with open(cultivo_path, encoding="latin-1", newline="") as f:
        r = csv.reader(f, delimiter=";", quotechar='"')
        next(r)
        for row in r:
            if len(row) <= 23:
                continue
            if row[23].strip():
                continue
            code = re.sub(r"[^0-9]", "", row[0].strip().strip('"')) or "0"
            active_codes.add(code)
    by_crop = defaultdict(set)
    with open(producto_path, encoding="latin-1", newline="") as f:
        r = csv.reader(f, delimiter=";", quotechar='"')
        next(r)
        for row in r:
            if len(row) <= 7:
                continue
            if row[7].strip():
                continue
            code = re.sub(r"[^0-9]", "", row[3].strip().strip('"')) or "0"
            if code not in active_codes:
                continue
            name = row[2].strip().strip('"')
            if not name:
                continue
            by_crop[code].add(name)
    for code in sorted(by_crop.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        attr_id = f"{MODULE}.ter_attr_cultivo_{code}_producto"
        out[attr_id] = "Producto"
        for idx, name in enumerate(sorted(by_crop[code]), start=1):
            out[f"{attr_id}_val_{idx}"] = name
    return out


def main():
    base = Path(__file__).resolve().parent.parent
    data = {}
    data.update(STATIC_ES)
    data.update(_destino_es(base))
    data.update(_procedencia_es(base))
    data.update(_sistema_cultivo_es(base))
    data.update(_senp_es(base))
    data.update(_cobertura_suelo_es(base))
    data.update(_tipo_labor_es(base))
    data.update(_producto_es(base))
    out_path = Path(__file__).resolve().parent / "attribute_translations_es.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Written {out_path} ({len(data)} entries)", file=sys.stderr)


if __name__ == "__main__":
    main()
