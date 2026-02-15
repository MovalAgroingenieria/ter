#!/usr/bin/env python3
# Copyright 2026 Moval Agroingenieria S.L.
# Reads catalogos_csv/Producto Vegetal.csv and generates ter_producto_vegetal_data.xml:
# For each crop (Código SIEX) that exists in Cultivo.csv (active), one attribute "Producto"
# on that crop's use_type with values = distinct Producto names (active rows only).
# CSV: Latin-1. Output: UTF-8. Cuidado con los acentos.

import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

# Producto Vegetal.csv: Id;Código;Producto;Código SIEX;Cultivo SIEX;Fecha de alta;Fecha de modificación;Fecha de baja
PRODUCTO_COL = 2
CODIGO_SIEX_COL = 3
FECHA_BAJA_COL = 7

# Cultivo.csv: Código (0), Cultivo (1), ... Fecha de baja (23)
CULTIVO_CODIGO_COL = 0
CULTIVO_FECHA_BAJA_COL = 23


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


def main():
    base = Path(__file__).resolve().parent.parent
    cultivo_path = base / "catalogos_csv" / "Cultivo.csv"
    producto_path = base / "catalogos_csv" / "Producto Vegetal.csv"

    if not cultivo_path.exists():
        print(f"Error: {cultivo_path} not found", file=sys.stderr)
        sys.exit(1)
    if not producto_path.exists():
        print(f"Error: {producto_path} not found", file=sys.stderr)
        sys.exit(1)

    # Active crop codes from Cultivo.csv (Fecha de baja empty)
    active_codes = set()
    with open(cultivo_path, encoding="latin-1", newline="") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        next(reader)
        for row in reader:
            if len(row) <= CULTIVO_FECHA_BAJA_COL:
                continue
            fecha_baja = row[CULTIVO_FECHA_BAJA_COL].strip() if row[CULTIVO_FECHA_BAJA_COL] else ""
            if fecha_baja:
                continue
            code = row[CULTIVO_CODIGO_COL].strip().strip('"')
            code_clean = re.sub(r"[^0-9]", "", code) or "0"
            active_codes.add(code_clean)

    # Group by crop code: code -> set of Producto names (active only)
    by_crop = defaultdict(set)
    with open(producto_path, encoding="latin-1", newline="") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        next(reader)
        for row in reader:
            if len(row) <= FECHA_BAJA_COL:
                continue
            fecha_baja = row[FECHA_BAJA_COL].strip() if row[FECHA_BAJA_COL] else ""
            if fecha_baja:
                continue
            code = row[CODIGO_SIEX_COL].strip().strip('"')
            code_clean = re.sub(r"[^0-9]", "", code) or "0"
            if code_clean not in active_codes:
                continue
            producto = row[PRODUCTO_COL].strip().strip('"')
            if not producto:
                continue
            by_crop[code_clean].add(producto)

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8" ?>')
    out.append("<!-- Copyright 2026 Moval Agroingenieria S.L. -->")
    out.append("<!-- Producto attribute per crop: values from Producto Vegetal.csv (active only). -->")
    out.append("<odoo>")
    out.append('    <data noupdate="0">')
    out.append("")

    total_attrs = 0
    total_vals = 0
    for code_clean in sorted(by_crop.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        products = sorted(by_crop[code_clean])
        type_id = f"ter_use_type_cultivo_{code_clean}"
        attr_id = f"ter_attr_cultivo_{code_clean}_producto"
        # Avoid id length > 63 or duplicates; Odoo limits external id length
        attr_id = attr_id[:63]

        out.append(f'        <record id="{attr_id}" model="ter.use_type.attribute" forcecreate="True">')
        out.append('            <field name="name">Product</field>')
        out.append(f'            <field name="use_type_id" ref="{type_id}"/>')
        out.append("        </record>")
        out.append("")
        total_attrs += 1

        for idx, product_name in enumerate(products, start=1):
            val_id = f"{attr_id}_val_{idx}"
            val_id = re.sub(r"[^a-z0-9_]", "_", val_id)[:63]
            val_esc = escape_xml(product_name)
            out.append(f'        <record id="{val_id}" model="ter.use_type.attribute.value" forcecreate="True">')
            out.append(f'            <field name="name">{val_esc}</field>')
            out.append(f'            <field name="attribute_id" ref="{attr_id}"/>')
            out.append("        </record>")
            total_vals += 1
        out.append("")

    out.append("    </data>")
    out.append("</odoo>")

    xml_path = Path(__file__).resolve().parent / "ter_producto_vegetal_data.xml"
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Written {xml_path} ({total_attrs} attributes, {total_vals} values)", file=sys.stderr)


if __name__ == "__main__":
    main()
