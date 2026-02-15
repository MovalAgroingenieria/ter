#!/usr/bin/env python3
# Copyright 2026 Moval Agroingenieria S.L.
# Reads catalogos_csv/Variedad - Especie - Tipo.csv (active only) and generates
# several ter_variedad_especie_tipo_data_N.xml: for each crop, 4 attributes on
# that crop's use_type. Split into multiple files to avoid one huge XML.
# CSV: Latin-1. Output: UTF-8.

import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

NUM_FILES = 10  # Split into this many XML files

# Variedad CSV columns
CODIGO_CULTIVO_COL = 0
VARIEDAD_NAME_COL = 6
ADMISIBLE_COL = 7
VINIFICABLE_COL = 8
INTEGRADO_COL = 9
FECHA_BAJA_COL = 12

# Cultivo.csv
CULTIVO_CODIGO_COL = 0
CULTIVO_FECHA_BAJA_COL = 23

key_to_sets = [
    ("variedad", "Variedad/ Especie/ Tipo"),
    ("admisible", "Admisible Ayudas Asociadas"),
    ("vinificable", "Vinificable"),
    ("integrado", "Integrado"),
]


def escape_xml(text):
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def slug(s, max_len=35):
    return re.sub(r"[^a-z0-9_]", "_", str(s).strip().lower())[:max_len] or "x"


def write_chunk(lines, xml_path):
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    base = Path(__file__).resolve().parent.parent
    cultivo_path = base / "catalogos_csv" / "Cultivo.csv"
    variedad_path = base / "catalogos_csv" / "Variedad - Especie - Tipo.csv"
    data_dir = Path(__file__).resolve().parent

    if not cultivo_path.exists():
        print("Error: Cultivo.csv not found", file=sys.stderr)
        sys.exit(1)
    if not variedad_path.exists():
        print("Error: Variedad - Especie - Tipo.csv not found", file=sys.stderr)
        sys.exit(1)

    # Active crop codes from Cultivo.csv
    active_cultivos = set()
    with open(cultivo_path, encoding="latin-1", newline="") as f:
        r = csv.reader(f, delimiter=";", quotechar='"')
        next(r)
        for row in r:
            if len(row) <= CULTIVO_FECHA_BAJA_COL:
                continue
            if row[CULTIVO_FECHA_BAJA_COL].strip():
                continue
            code = re.sub(r"[^0-9]", "", row[CULTIVO_CODIGO_COL].strip().strip('"')) or "0"
            active_cultivos.add(code)

    # By crop: 4 sets of values
    by_crop = defaultdict(lambda: defaultdict(set))
    with open(variedad_path, encoding="latin-1", newline="") as f:
        r = csv.reader(f, delimiter=";", quotechar='"')
        next(r)
        for row in r:
            if len(row) <= FECHA_BAJA_COL:
                continue
            if row[FECHA_BAJA_COL].strip():
                continue
            codigo_cultivo = re.sub(r"[^0-9]", "", row[CODIGO_CULTIVO_COL].strip().strip('"')) or "0"
            if codigo_cultivo not in active_cultivos:
                continue
            c = by_crop[codigo_cultivo]
            if len(row) > VARIEDAD_NAME_COL and row[VARIEDAD_NAME_COL].strip():
                c["variedad"].add(row[VARIEDAD_NAME_COL].strip().strip('"'))
            if len(row) > ADMISIBLE_COL and row[ADMISIBLE_COL].strip():
                c["admisible"].add(row[ADMISIBLE_COL].strip().strip('"'))
            if len(row) > VINIFICABLE_COL and row[VINIFICABLE_COL].strip():
                c["vinificable"].add(row[VINIFICABLE_COL].strip().strip('"'))
            if len(row) > INTEGRADO_COL and row[INTEGRADO_COL].strip():
                c["integrado"].add(row[INTEGRADO_COL].strip().strip('"'))

    sorted_codes = sorted(by_crop.keys(), key=lambda x: int(x) if x.isdigit() else 0)
    total_crops = len(sorted_codes)
    crops_per_file = max(1, (total_crops + NUM_FILES - 1) // NUM_FILES)

    # Remove old single file if present
    old_single = data_dir / "ter_variedad_especie_tipo_data.xml"
    if old_single.exists():
        old_single.unlink()

    total_attrs = 0
    total_vals = 0
    written_files = []

    for file_idx in range(NUM_FILES):
        start = file_idx * crops_per_file
        end = min(start + crops_per_file, total_crops)
        chunk_codes = sorted_codes[start:end] if start < total_crops else []

        out = []
        out.append('<?xml version="1.0" encoding="UTF-8" ?>')
        out.append("<!-- Copyright 2026 Moval Agroingenieria S.L. -->")
        out.append(f"<!-- Part {file_idx + 1}/{NUM_FILES}: attributes Variedad/Especie/Tipo, Admisible, Vinificable, Integrado (from Variedad CSV). -->")
        out.append('<odoo noupdate="1">')
        out.append("")

        for code in chunk_codes:
            type_id = f"ter_use_type_cultivo_{code}"
            crop_data = by_crop[code]
            for key, attr_label in key_to_sets:
                values = crop_data.get(key) or set()
                if not values and key == "variedad":
                    continue
                if not values:
                    values = {"NO"}
                attr_slug = slug(attr_label, 25)
                attr_id = f"ter_attr_cultivo_{code}_{attr_slug}"[:63]
                attr_id = re.sub(r"[^a-z0-9_]", "_", attr_id)[:63]

                out.append(f'        <record id="{attr_id}" model="ter.use_type.attribute" forcecreate="True">')
                out.append(f'            <field name="name">{escape_xml(attr_label)}</field>')
                out.append(f'            <field name="use_type_id" ref="{type_id}"/>')
                out.append("        </record>")
                out.append("")
                total_attrs += 1

                for idx, val in enumerate(sorted(values), start=1):
                    val_id = f"{attr_id}_val_{idx}"[:63]
                    val_id = re.sub(r"[^a-z0-9_]", "_", val_id)[:63]
                    out.append(f'        <record id="{val_id}" model="ter.use_type.attribute.value" forcecreate="True">')
                    out.append(f'            <field name="name">{escape_xml(val)}</field>')
                    out.append(f'            <field name="attribute_id" ref="{attr_id}"/>')
                    out.append("        </record>")
                    total_vals += 1
                out.append("")

        out.append("</odoo>")

        part_num = file_idx + 1
        xml_name = f"ter_variedad_especie_tipo_data_{part_num}.xml"
        xml_path = data_dir / xml_name
        write_chunk(out, xml_path)
        written_files.append(xml_name)
        print(f"Written {xml_path.name} ({len(chunk_codes)} crops)", file=sys.stderr)

    print(f"Total: {len(written_files)} files, {total_attrs} attributes, {total_vals} values", file=sys.stderr)


if __name__ == "__main__":
    main()
