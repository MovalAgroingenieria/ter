#!/usr/bin/env python3
# Copyright 2026 Moval Agroingenieria S.L.
# Reads catalogos_csv/Destino del cultivo.csv and generates ter_destino_cultivo_data.xml:
# One attribute "Crop destination" on Farming with one value per active row.
# Active = Fecha de baja empty. CSV: Latin-1. Output: UTF-8.

import csv
import re
import sys
from pathlib import Path

FECHA_BAJA_COL = 5
DESTINO_COL = 1  # "Destino del cultivo"
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
    csv_path = base / "catalogos_csv" / "Destino del cultivo.csv"
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
            fecha_baja = row[FECHA_BAJA_COL].strip() if row[FECHA_BAJA_COL] else ""
            if fecha_baja:
                continue
            destino = row[DESTINO_COL].strip().strip('"')
            if not destino:
                continue
            code = row[CODIGO_COL].strip().strip('"')
            rows.append((code, destino))

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8" ?>')
    out.append("<!-- Copyright 2026 Moval Agroingenieria S.L. -->")
    out.append("<!-- Crop destination attribute on Farming: values from Destino del cultivo.csv (active only). -->")
    out.append("<odoo>")
    out.append('    <data noupdate="0">')
    out.append("")
    out.append('        <record id="ter_attr_crop_destination_farming" model="ter.use_type.attribute" forcecreate="True">')
    out.append('            <field name="name">Crop destination</field>')
    out.append('            <field name="use_type_id" ref="ter_use_type_farming"/>')
    out.append("        </record>")
    out.append("")

    for code, destino in rows:
        val_id = f"ter_attr_crop_destination_farming_{value_slug(code)}"
        val_esc = escape_xml(destino)
        out.append(f'        <record id="{val_id}" model="ter.use_type.attribute.value" forcecreate="True">')
        out.append(f'            <field name="name">{val_esc}</field>')
        out.append('            <field name="attribute_id" ref="ter_attr_crop_destination_farming"/>')
        out.append("        </record>")
    out.append("")

    out.append("    </data>")
    out.append("</odoo>")

    xml_path = Path(__file__).resolve().parent / "ter_destino_cultivo_data.xml"
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Written {xml_path} (1 attribute, {len(rows)} values)", file=sys.stderr)


if __name__ == "__main__":
    main()
