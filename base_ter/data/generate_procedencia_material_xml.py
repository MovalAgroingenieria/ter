#!/usr/bin/env python3
# Copyright 2026 Moval Agroingenieria S.L.
# Reads catalogos_csv/Procedencia del material vegetal.csv and generates
# ter_procedencia_material_vegetal_data.xml: one attribute "Plant material provenance"
# on Farming with one value per active row. Active = Fecha de baja empty. CSV: Latin-1.

import csv
import re
import sys
from pathlib import Path

# CSV: Código SIEX; Procedencia del material vegetal; Fecha de alta; Fecha de modificación; Fecha de baja
FECHA_BAJA_COL = 4
PROCEDENCIA_COL = 1
CODIGO_COL = 0


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


def value_slug(code):
    """Valid xml id for value record (a-z, 0-9, _)."""
    return re.sub(r"[^a-z0-9]", "_", str(code).strip().lower())[:50] or "val"


def main():
    base = Path(__file__).resolve().parent.parent
    csv_path = base / "catalogos_csv" / "Procedencia del material vegetal.csv"
    if not csv_path.exists():
        print(f"Error: {csv_path} not found", file=sys.stderr)
        sys.exit(1)

    rows = []
    with open(csv_path, encoding="latin-1", newline="") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        next(reader)
        for row in reader:
            if len(row) <= FECHA_BAJA_COL:
                continue
            fecha_baja = row[FECHA_BAJA_COL].strip() if len(row) > FECHA_BAJA_COL and row[FECHA_BAJA_COL] else ""
            if fecha_baja:
                continue
            procedencia = row[PROCEDENCIA_COL].strip().strip('"')
            if not procedencia:
                continue
            code = row[CODIGO_COL].strip().strip('"')
            rows.append((code, procedencia))

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8" ?>')
    out.append("<!-- Copyright 2026 Moval Agroingenieria S.L. -->")
    out.append("<!-- Plant material provenance attribute on Farming: values from Procedencia del material vegetal.csv (active only). -->")
    out.append("<odoo>")
    out.append('    <data noupdate="0">')
    out.append("")
    out.append('        <record id="ter_attr_plant_material_provenance_farming" model="ter.use_type.attribute" forcecreate="True">')
    out.append('            <field name="name">Plant material provenance</field>')
    out.append('            <field name="use_type_id" ref="ter_use_type_farming"/>')
    out.append("        </record>")
    out.append("")

    for code, procedencia in rows:
        val_id = f"ter_attr_plant_material_provenance_farming_{value_slug(code)}"
        val_esc = escape_xml(procedencia)
        out.append(f'        <record id="{val_id}" model="ter.use_type.attribute.value" forcecreate="True">')
        out.append(f'            <field name="name">{val_esc}</field>')
        out.append('            <field name="attribute_id" ref="ter_attr_plant_material_provenance_farming"/>')
        out.append("        </record>")
    out.append("")

    out.append("    </data>")
    out.append("</odoo>")

    xml_path = Path(__file__).resolve().parent / "ter_procedencia_material_vegetal_data.xml"
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Written {xml_path} (1 attribute, {len(rows)} values)", file=sys.stderr)


if __name__ == "__main__":
    main()
