#!/usr/bin/env python3
# Copyright 2026 Moval Agroingenieria S.L.
# Reads catalogos_csv/Cultivo.csv and generates ter_use_type_cultivo_data.xml
# Each crop (ter.use_type) gets its own attributes with only that crop's values.
# Encoding: CSV is ISO-8859-1 / Latin-1. Output XML: UTF-8.

import csv
import re
import sys
from pathlib import Path

# Attribute column index (0-based) -> English name for ter.use_type.attribute
ATTR_COLUMNS = {
    2: "Latin",
    3: "EPPO",
    4: "C. UPOV",
    5: "Horticultural",
    6: "Energetic",
    7: "Fruit tree",
    8: "Shell fruits",
    9: "Aromatic condiment medicinal",
    10: "Direct sowing",
    11: "Improving species",
    12: "Short-cycle forestry",
    13: "Woody",
    14: "Cropland",
    15: "Permanent crops",
    16: "Permanent pasture",
    17: "Forest",
    18: "Legumes",
    19: "Unharvested zone cereals legumes oilseeds",
    20: "Integrated",
}
FECHA_BAJA_COL = 23
CODIGO_COL = 0
CULTIVO_COL = 1
# CSV flags (0-based): 5=Horticultural, 7=Fruit tree, 8=Shell fruits, 14=Cropland,
# 15=Permanent crops, 16=Permanent pasture, 17=Forest, 18=Legumes
COL_HORTICULTURAL = 5
COL_FRUTAL = 7
COL_FRUTOS_CASCARA = 8
COL_CROPLAND = 14
COL_PERMANENT_CROPS = 15
COL_PASTOS_PERMANENTES = 16
COL_FORESTALES = 17
COL_LEGUMINOSAS = 18

# Default family when no rule matches
DEFAULT_FAMILY = "ter_use_type_familia_other"


def _norm(s):
    """Normalize for matching: upper, strip, replace common Spanish accents."""
    if not s:
        return ""
    s = s.upper().strip()
    for a, b in [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"), ("Ñ", "N"), ("Ü", "U")]:
        s = s.replace(a, b)
    return s


def get_family_for_crop(row):
    """
    Return ter_use_type_familia_* xml id for this crop (from Cultivo.csv row).
    Uses column flags and name keywords to assign one of the 21 crop families.
    """
    name = _norm(row[CULTIVO_COL].strip().strip('"') if len(row) > CULTIVO_COL else "")
    if len(row) <= 23:
        return DEFAULT_FAMILY
    # Helper: get flag SI/NO
    def si(col):
        return col < len(row) and (row[col].strip().strip('"').upper() == "SI")

    # Unproductive / administrative
    if "BARBECHO" in name or "RETIRADA" in name or "ABANDONO" in name or "DATO HIST" in name:
        return "ter_use_type_familia_unproductive"
    if "NO AGRARIAS" in name or "OTRAS UTILIZACIONES" in name:
        return "ter_use_type_familia_unproductive"

    # Pastures and grasslands
    if si(COL_PASTOS_PERMANENTES) or "PASTO" in name or "PASTIZAL" in name or "PASTOS PERMANENTES" in name:
        return "ter_use_type_familia_pastures"

    # Forest / woody
    if si(COL_FORESTALES) or "FORESTAL" in name or "SUPERFICIES FORESTALES" in name:
        return "ter_use_type_familia_woody_others"
    if any(x in name for x in ("CHOPO", "ENCINA", "ROBLE", "HAYA", "ALCORNOQUE", "ABETO", "ENEBRO", "SABINA", "PINSAPO", "PINOS ", "PAULONIA", "EUCALIPTO", "SAUCE", "ACACIA", "AILANTO", "ROBINIA", "JACARANDA", "CASTAÑO (FORESTAL)", "PINOS PIÑONEROS", "RESTO DE PINOS")):
        return "ter_use_type_familia_woody_others"
    if "ARBOLES DE NAVIDAD" in name:
        return "ter_use_type_familia_woody_others"

    # Fruit trees and permanent fruit crops
    if si(COL_FRUTAL) or si(COL_PERMANENT_CROPS):
        if any(x in name for x in ("NARANJO", "LIMONERO", "MANDARINO", "CLEMENTINA", "SATSUMA", "POMELO", "TORONJA", "CITRUS")):
            return "ter_use_type_familia_citrus"
        if any(x in name for x in ("VIÑA", "VID ", "UVA DE MESA", "UVA PASA")) or name == "VIÃA" or "VITIVINIFERA" in name:
            return "ter_use_type_familia_grapevine"
        if si(COL_FRUTOS_CASCARA) or any(x in name for x in ("ALMENDRO", "AVELLANO", "NOGAL", "PISTACHO", "ALGARROBO", "FRUTOS DE CÁSCARA", "FRUTOS CÁSCARA")):
            return "ter_use_type_familia_orchards_nuts"
        if any(x in name for x in ("FRESA", "FRAMBUESA", "ARÁNDANO", "GROSELLERO", "ZARZAMORA", "FRUTOS DEL BOSQUE", "FRUTOS BOSQUE")):
            return "ter_use_type_familia_berries"
        if "OLIVO" in name or "VIÑA - OLIVAR" in name:
            return "ter_use_type_familia_fruit_trees"
        if any(x in name for x in ("MELOCOTONERO", "NECTARINO", "ALBARICOQUERO", "PERAL", "MANZANO", "CEREZO", "CIRUELO", "OTROS FRUTALES", "MEMBRILLO", "KIWI", "CAQUI", "PALOSANTO", "NÍSPERO", "NISPERO", "GRANADO", "HIGUERA", "PLATERINA", "PARAGUAYO", "ENDRINO", "ARAÑÓN")):
            return "ter_use_type_familia_fruit_trees"
        # Other permanent (e.g. trufa, vivero)
        if "TRUFA" in name:
            return "ter_use_type_familia_woody_others"
        if "VIVERO" in name:
            return "ter_use_type_familia_ornamentals"
        return "ter_use_type_familia_fruit_trees"

    # Legumes: grain vs forage
    if si(COL_LEGUMINOSAS):
        if any(x in name for x in ("GUISANTE", "HABA", "ALUBIA", "GARBANZO", "LENTEJA", "ALTRAMUZ BLANCO", "ALTRAMUZ AMARILLO", "ALMORTA", "TITARROS", "ALGARROBA", "ALVERJA", "ALBERJÓN", "CACAHUETE")) and "FORRAJERO" not in name and "VERDE" not in name:
            return "ter_use_type_familia_legumes_grain"
        if any(x in name for x in ("ALFALFA", "VEZA", "YEROS", "ESPARCETA", "TRÉBOL", "TRÉBOL", "ZULLA", "FESTUCA", "RAYGRASS", "AGROSTIS", "DACTILO", "FLEO", "POA ", "ALHOLVA", "MEZCLA ")):
            return "ter_use_type_familia_forage"
        if "MEZCLA" in name and ("VEZA" in name or "GUISANTE" in name or "ZULLA" in name):
            return "ter_use_type_familia_forage"
        return "ter_use_type_familia_legumes_grain"

    # Cereals
    if any(x in name for x in ("TRIGO", "ESPELTA", "CEBADA", "CENTENO", "MAÍZ", "MAIZ", "SORGO", "AVENA", "ALFORFÓN", "MIJO", "ALPISTE", "TRITICALE", "TRITORDEUM", "TEFF", "ARROZ", "TRANQUILLÓN", "QUINOA", "TRIGO KHORASAN")):
        return "ter_use_type_familia_cereals"

    # Oilseeds and industrial (sunflower, rapeseed, etc.)
    if any(x in name for x in ("GIRASOL", "COLZA", "CAMELINA", "CÁRTAMO", "CARTAMO")):
        return "ter_use_type_familia_oilseeds"
    if "SOJA" in name:
        return "ter_use_type_familia_legumes_grain"

    # Sugar
    if "REMOLACHA" in name and "FORRAJERA" not in name and "DE MESA" not in name:
        return "ter_use_type_familia_sugar"
    if "CAÑA" in name and "AZÚCAR" in name:
        return "ter_use_type_familia_sugar"
    if "CAÑA COMÚN" in name or "CAÑA COMUN" in name:
        return "ter_use_type_familia_industrial"

    # Tubers and roots
    if any(x in name for x in ("PATATA", "PAPA", "BONIATO", "ZANAHORIA", "CHIRIVÍA", "CHIRIVIA", "NABO", "REMOLACHA DE MESA")):
        return "ter_use_type_familia_tubers_roots"

    # Vegetables (horticultural)
    if si(COL_HORTICULTURAL) or any(x in name for x in (
        "TOMATE", "PIMIENTO", "LECHUGA", "CEBOLLA", "SANDÍA", "MELÓN", "MELON", "BRÓCOLI", "BROCOLI", "COLIFLOR", "ROMANESCU",
        "BERENJENA", "CALABACÍN", "CALABACIN", "ALCACHOFA", "PEPINO", "ACELGA", "CEBOLLETA", "CHALOTA", "AJO", "REPOLLO", "COL ",
        "PUERRO", "COLIRRÁBANO", "ENDIVIA", "ESCAROLA", "RÁBANO", "RABANO", "BERRO", "ESPINACA", "CARDO", "CALABAZA", "BORRAJA",
        "GUINDILLA", "ACHICORIA", "HUERTA", "PIMIENTO PARA PIMENTÓN"
    )):
        return "ter_use_type_familia_vegetables"

    # Industrial
    if any(x in name for x in ("TABACO", "ALGODÓN", "ALGODON", "LINO", "CÁÑAMO", "CANAMO", "LÚPULO", "LUPULO", "CÁÑAMO", "ADORMIDERA", "HIERBA CINTA", "KENAF", "YUTE", "SISAL", "ABACA", "JATROPHA", "MISCANTHUS", "CAÑA COMÚN")):
        return "ter_use_type_familia_industrial"

    # Mushrooms
    if "SETAS" in name or "CHAMPIÑÓN" in name or "CHAMPIGNON" in name:
        return "ter_use_type_familia_mushrooms"

    # Ornamentals
    if "FLORES" in name or "VIVERO" in name:
        return "ter_use_type_familia_ornamentals"

    # Aromatic / medicinal woody (lavender, rosemary, etc.) -> ornamentals or industrial
    if any(x in name for x in ("LAVANDA", "LAVANDÍN", "ESPLIEGO", "ROMERO", "ALCAPARRA", "AJENJO", "HELICRISO", "HIERBALUISA", "SANTOLINA", "ALOE VERA", "TOMILLO")):
        return "ter_use_type_familia_ornamentals"

    # Aromatic herbaceous / vegetables
    if any(x in name for x in ("AZAFRÁN", "AZAFRAN", "ESPECIES AROMÁTICAS", "PEREJIL", "ALBAHACA", "MENTA", "ORÉGANO", "SALVIA", "CILANTRO", "ENELDO", "HINOJO", "MEJORANA", "COMINO", "ESTEVIA")):
        return "ter_use_type_familia_vegetables"

    # Woody others (short-cycle forestry, etc.)
    if si(12):  # Short-cycle forestry
        return "ter_use_type_familia_woody_others"

    # Remaining: OPUNTIA -> industrial; CAFÉ -> other; ESPÁRRAGO -> vegetables; QUINOA already cereals
    if "OPUNTIA" in name or "CAFÉ" in name or "CAFE" in name:
        return "ter_use_type_familia_other"
    if "ESPÁRRAGO" in name or "ESPARRAGO" in name:
        return "ter_use_type_familia_vegetables"

    return DEFAULT_FAMILY


def attr_slug(attr_name):
    """Valid short id for attribute (a-z, 0-9, _)."""
    s = attr_name.lower().replace(" ", "_").replace(".", "_")
    return re.sub(r"[^a-z0-9_]", "", s)[:40] or "attr"


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
    csv_path = base / "catalogos_csv" / "Cultivo.csv"
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
            rows.append(row)

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8" ?>')
    out.append("<!-- Copyright 2026 Moval Agroingenieria S.L. -->")
    out.append("<!-- Crops under Family (Farming -> Family -> Crop). Each crop has its own attributes. -->")
    out.append("<odoo>")
    out.append('    <data noupdate="0">')
    out.append("")
    out.append("        <!-- Crops under their crop family (Farming -> Family -> Crop). -->")
    out.append("")

    for row in rows:
        code = row[CODIGO_COL].strip().strip('"')
        cultivo = row[CULTIVO_COL].strip().strip('"')
        if not cultivo:
            continue
        code_clean = re.sub(r"[^0-9]", "", code) or "0"
        type_id = f"ter_use_type_cultivo_{code_clean}"
        name_esc = escape_xml(cultivo)
        family_ref = get_family_for_crop(row)

        # One ter.use_type per crop; parent = family (Farming -> Family -> Crop)
        out.append(f'        <record id="{type_id}" model="ter.use_type" forcecreate="True">')
        out.append(f'            <field name="name">{name_esc}</field>')
        out.append(f'            <field name="parent_id" ref="{family_ref}"/>')
        out.append("        </record>")

        # For this crop: one attribute per column, each with a single value (this row's cell)
        for col, attr_name in ATTR_COLUMNS.items():
            val = row[col].strip().strip('"') if col < len(row) else ""
            slug = attr_slug(attr_name)
            attr_id = f"ter_attr_cultivo_{code_clean}_{slug}"
            attr_id = re.sub(r"_+", "_", attr_id)[:63]

            out.append(f'        <record id="{attr_id}" model="ter.use_type.attribute" forcecreate="True">')
            out.append(f'            <field name="name">{escape_xml(attr_name)}</field>')
            out.append(f'            <field name="use_type_id" ref="{type_id}"/>')
            out.append("        </record>")

            val_id = f"{attr_id}_val"
            val_id = re.sub(r"[^a-z0-9_]", "_", val_id)[:63]
            val_esc = escape_xml(val) if val else ""
            out.append(f'        <record id="{val_id}" model="ter.use_type.attribute.value" forcecreate="True">')
            out.append(f'            <field name="name">{val_esc}</field>')
            out.append(f'            <field name="attribute_id" ref="{attr_id}"/>')
            out.append("        </record>")
        out.append("")

    out.append("    </data>")
    out.append("</odoo>")

    xml_path = Path(__file__).resolve().parent / "ter_use_type_cultivo_data.xml"
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Written {xml_path} ({len(rows)} crops, {len(ATTR_COLUMNS)} attributes per crop)", file=sys.stderr)


if __name__ == "__main__":
    main()
