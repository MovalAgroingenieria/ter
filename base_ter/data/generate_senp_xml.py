#!/usr/bin/env python3
# Copyright 2026 Moval Agroingenieria S.L.
# Reads catalogos_csv/Superficies y elementos no productivos (SENP).csv and
# generates ter_senp_data.xml: one attribute "Non-productive surfaces and elements (SENP)"
# on Farming with one value per active row. Active = Fecha de baja empty. CSV: Latin-1.

import csv
import re
import sys
from pathlib import Path

# CSV: Código SIEX; Código; Tipo; Fecha de alta; Fecha de modificación; Fecha de baja
FECHA_BAJA_COL = 5
TIPO_COL = 2
CODIGO_SIEX_COL = 0


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


def value_slug(code, row_index):
    """Valid xml id for value record (a-z, 0-9, _)."""
    if code:
        s = re.sub(r"[^a-z0-9]", "_", str(code).strip().lower())[:50]
        if s:
            return s
    return f"val_{row_index}"


def main():
    base = Path(__file__).resolve().parent.parent
    csv_path = base / "catalogos_csv" / "Superficies y elementos no productivos (SENP).csv"
    if not csv_path.exists():
        print(f"Error: {csv_path} not found", file=sys.stderr)
        sys.exit(1)

    rows = []
    with open(csv_path, encoding="latin-1", newline="") as f:
        reader = csv.reader(f, delimiter=";", quotechar='"')
        next(reader)
        for idx, row in enumerate(reader):
            if len(row) <= FECHA_BAJA_COL:
                continue
            fecha_baja = row[FECHA_BAJA_COL].strip() if row[FECHA_BAJA_COL] else ""
            if fecha_baja:
                continue
            tipo = row[TIPO_COL].strip().strip('"')
            if not tipo:
                continue
            code = row[CODIGO_SIEX_COL].strip().strip('"')
            slug = value_slug(code, idx + 1)
            rows.append((slug, tipo))

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8" ?>')
    out.append("<!-- Copyright 2026 Moval Agroingenieria S.L. -->")
    out.append("<!-- SENP attribute on Farming: values from Superficies y elementos no productivos (SENP).csv (active only). -->")
    out.append("<odoo>")
    out.append('    <data noupdate="0">')
    out.append("")
    out.append('        <record id="ter_attr_senp_farming" model="ter.use_type.attribute" forcecreate="True">')
    out.append('            <field name="name">Non-productive surfaces and elements (SENP)</field>')
    out.append('            <field name="use_type_id" ref="ter_use_type_farming"/>')
    out.append("        </record>")
    out.append("")

    for slug, tipo in rows:
        val_id = f"ter_attr_senp_farming_{slug}"
        val_esc = escape_xml(tipo)
        out.append(f'        <record id="{val_id}" model="ter.use_type.attribute.value" forcecreate="True">')
        out.append(f'            <field name="name">{val_esc}</field>')
        out.append('            <field name="attribute_id" ref="ter_attr_senp_farming"/>')
        out.append("        </record>")
    out.append("")

    out.append("    </data>")
    out.append("</odoo>")

    xml_path = Path(__file__).resolve().parent / "ter_senp_data.xml"
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Written {xml_path} (1 attribute, {len(rows)} values)", file=sys.stderr)


if __name__ == "__main__":
    main()
