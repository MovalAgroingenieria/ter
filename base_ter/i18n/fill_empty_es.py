#!/usr/bin/env python3
# Copyright 2026 Moval Agroingeniería S.L.
# Fill empty msgstr in base_ter i18n/es.po with Spanish translations.
# Run from base_ter/i18n: python3 fill_empty_es.py
#
# Intentionally left empty in es.po (do not add to FILL):
# - Numeric values (e.g. kc_a, kc_b, kc_c: "-0.125", "0.06", "1.0")
# - Variety/crop codes and technical names (e.g. "007DSB", "1000D188-01")
# - Identifiers (ter_parcel_256, etc.) that are not shown to end users

# Additional translations for strings that appear in es.po with empty msgstr
FILL = {
    "%(company_name)s – Ter Unit": "%(company_name)s – Unidad de Uso Territorial",
    "... and %(more)s more errors.": "... y %(more)s errores más.",
    "... and %(more)s more.": "... y %(more)s más.",
    "<span class=\"o_stat_value\"/>\n                            <span class=\"o_stat_text\">Use Type</span>": "<span class=\"o_stat_value\"/>\n                            <span class=\"o_stat_text\">Tipos de usos</span>",
    "<span class=\"oe_inline\">%</span>": "<span class=\"oe_inline\">%</span>",
    "<span class=\"oe_inline\">EPSG:</span>": "<span class=\"oe_inline\">EPSG:</span>",
    "<span class=\"oe_inline\">ha</span>": "<span class=\"oe_inline\">ha</span>",
    "<span>m</span>": "<span>m</span>",
    "<span>m²</span>": "<span>m²</span>",
    "ARCHIVED": "ARCHIVADO",
    "Aerial Image (GIS preview)": "Imagen aérea (vista SIG)",
    "Aerial image OK. Parcel: %(name)s": "Imagen aérea correcta. Parcela: %(name)s",
    "Aerial image OK. Property: %(name)s": "Imagen aérea correcta. Finca: %(name)s",
    "Alert threshold due to the difference between the official area and the GIS area": "Umbral de aviso por diferencia entre superficie oficial y superficie SIG",
    "Ancestors of %(name)s": "Antecesores de %(name)s",
    "Area GIS": "Superficie SIG",
    "Area Parcels": "Superficie parcelas",
    "Area unit": "Unidad de superficie",
    "Attribute '%(attr)s' is not allowed for use type '%(use)s'.": "El atributo '%(attr)s' no está permitido para el uso '%(use)s'.",
    "Attribute '%(attr)s' is required.": "El atributo '%(attr)s' es obligatorio.",
    "Auto-generated from company sequence when left empty.": "Generado automáticamente por la secuencia de la empresa si se deja vacío.",
    "Available": "Disponible",
    "Campaign Type": "Tipo de campaña",
    "Cannot delete a unit with GIS geometry. Clear the geometry first or archive the record.": "No se puede eliminar una unidad con geometría SIG. Borre la geometría antes o archive el registro.",
    "Cannot validate: Date range is required.": "No se puede validar: el intervalo de fechas es obligatorio.",
    "Cannot validate: Main parcel is required.": "No se puede validar: la parcela principal es obligatoria.",
    "Cultivable": "Cultivable",
    "Could not fetch aerial image from WMS (timeout or connection error). Try again later or check network/IGN service. Parcel: %(code)s": "No se pudo obtener la imagen aérea del WMS (timeout o error de conexión). Inténtelo más tarde o compruebe la red/servicio IGN. Parcela: %(code)s",
    "Could not fetch aerial images for %(count)s parcel(s) (timeout or connection error to WMS). Try again later: %(codes)s": "No se pudieron obtener las imágenes aéreas de %(count)s parcela(s) (timeout o error de conexión con WMS). Inténtelo más tarde: %(codes)s",
    "Created %(count)s record(s): %(names)s": "Creado(s) %(count)s registro(s): %(names)s",
    "Date Range Periods": "Periodos rangos de fecha",
    "Descendants of %(name)s": "Descendientes de %(name)s",
    "Description to provide more information and context about this ter_unit": "Descripción para aportar más información y contexto sobre esta unidad territorial",
    "EPSG": "EPSG",
    "End date": "Fecha fin",
    "End date must be within the date range (%(start)s – %(end)s).": "La fecha fin debe estar dentro del intervalo (%(start)s – %(end)s).",
    "Error getting aerial image (is the WMS url correct?)": "Error al obtener la imagen aérea (¿es correcta la URL del WMS?)",
    "Errors: %(errors)s": "Errores: %(errors)s",
    "Farming": "En cultivo",
    "Industrial": "Industrial",
    "Livestock": "Ganadero",
    "Recreational": "Recreativo",
    "Urban": "Urbano",
    "Water reservoir": "Balsa",
    "For the integrated preview, arguments to add to the GIS viewer URL.": "Para la vista previa integrada, argumentos a añadir a la URL del visor SIG.",
    "Force the parcel manager and the property owner to be the same": "Forzar que el gestor de parcela y el titular de la finca sean el mismo",
    "General": "Base Territorial",
    "Geometry (EWKT)": "Geometría (EWKT)",
    "Geometry in EWKT format (e.g. SRID=25830;POLYGON(...)). If set, parcel is auto-assigned as the parcel with maximum overlap.": "Geometría en formato EWKT (p. ej. SRID=25830;POLYGON(...)). Si se define, la parcela se asigna automáticamente como la de mayor solapamiento.",
    "Getting the aerial images...": "Obteniendo las imágenes aéreas...",
    "Height, in pixels, of images captured from WMS services (the width will be calculated automatically to preserve the original proportions).": "Altura en píxeles de las imágenes obtenidas de servicios WMS (el ancho se calcula para mantener la proporción).",
    "ID": "ID",
    "If a manager is assigned to the parcel, it is mandatory to configure the contact list.": "Si se asigna un gestor a la parcela, es obligatorio configurar la lista de contactos.",
    "If checked, only the central parcel will be displayed; otherwise, all parcels will be displayed.": "Si está marcado, solo se mostrará la parcela central; en caso contrario, todas las parcelas.",
    "If checked, only the central property will be displayed; otherwise, all properties will be displayed.": "Si está marcado, solo se mostrará la finca central; en caso contrario, todas las fincas.",
    "If checked, the area unit will be the ha; otherwise you can choose another unit of area.": "Si está marcado, la unidad de superficie será la ha; en caso contrario puede elegir otra.",
    "If enabled, any parcel associated with a property that has an owner must have that owner as its manager.": "Si está activo, toda parcela asociada a una finca con titular debe tener a ese titular como gestor.",
    "If enabled, date ranges of this type can be used to define periods for territorial unit uses.": "Si está activo, los intervalos de este tipo pueden usarse para definir periodos de uso de unidades de uso territorial.",
    "If the area unit is not the ha, name of the alternative area unit.": "Si la unidad de superficie no es la ha, nombre de la unidad alternativa.",
    "Incorrect value of \"Alert threshold due to the difference between the official area and the GIS area\".": "Valor incorrecto de «Umbral de aviso por diferencia entre superficie oficial y SIG».",
    "Incorrect value of \"Standard area unit: Equivalence in ha\".": "Valor incorrecto de «Unidad de superficie estándar: Equivalencia en ha».",
    "Invalid KML XML: %(error)s": "KML XML no válido: %(error)s",
    "Invalid operator. Use \"=\" or \"ilike\".": "Operador no válido. Use \"=\" o \"ilike\".",
    "It is mandatory to enter the main contact of the parcel (only one).": "Es obligatorio indicar el contacto principal de la parcela (solo uno).",
    "It is mandatory to enter the parcel manager.": "Es obligatorio indicar el gestor de la parcela.",
    "It is not possible to remove a 'STANDARD' partner profile.": "No es posible eliminar un perfil de contacto 'ESTÁNDAR'.",
    "Lock": "Bloquear",
    "Locked": "Bloqueado",
    "Mixin for wizards that operate on the active record from context": "Mixin para asistentes que actúan sobre el registro activo del contexto",
    "Municipality is required.": "El municipio es obligatorio.",
    "Name field is mandatory.": "El campo nombre es obligatorio.",
    "No parcel found intersecting the unit geometry. Ensure parcels exist with geometry in the same area.": "No se encontró parcela que corte la geometría de la unidad. Asegúrese de que existan parcelas con geometría en la misma zona.",
    "No polygons found in KML.": "No se encontraron polígonos en el KML.",
    "Note": "Nota",
    "Official area must be greater than or equal to 0.": "La superficie oficial debe ser mayor o igual a 0.",
    "Optional prefix for record names (e.g. 'PARCEL-' or 'FINCA-').": "Prefijo opcional para nombres de registro (p. ej. 'PARCELA-' o 'FINCA-').",
    "Optional: assign as manager (property) or use for parcel partner link.": "Opcional: asignar como gestor (finca) o usar para enlace de contacto de parcela.",
    "Parcel on the map": "Parcela en el mapa",
    "Percentage (of the official area of a parcel) designated as the maximum allowable threshold for the difference between this official area and the GIS area (if zero, no warning will be displayed).": "Porcentaje (de la superficie oficial de la parcela) que define el umbral máximo de diferencia entre esa superficie oficial y la SIG (si es cero, no se mostrará aviso).",
    "PostGIS could not be enabled in this database. Install PostGIS on PostgreSQL and ensure the DB user can run CREATE EXTENSION.": "No se pudo activar PostGIS en esta base de datos. Instale PostGIS en PostgreSQL y asegúrese de que el usuario pueda ejecutar CREATE EXTENSION.",
    "PostGIS is not available in this database. Install/enable PostGIS and retry.": "PostGIS no está disponible en esta base de datos. Instale o active PostGIS e inténtelo de nuevo.",
    "Property on the map": "Finca en el mapa",
    "Repeated partner code.": "Código de contacto repetido.",
    "Review the profile percentages: there is a percentage profile that does not add up to 100%.": "Revise los porcentajes del perfil: hay un perfil de porcentaje que no suma 100%.",
    "SRID=25830;POLYGON((...))": "SRID=25830;POLYGON((...))",
    "Sequence used to generate ter.use_unit names. Name format: {type_code}-{date_start}-{date_end}-{parcel_code}-{sequence}.": "Secuencia para generar nombres de unidades territoriales. Formato: {type_code}-{date_start}-{date_end}-{parcel_code}-{sequence}.",
    "Spatial reference of the layers stored in the database (if changed, layers will be automatically reprojected).": "Referencia espacial de las capas en la base de datos (si se cambia, se reproyectarán automáticamente).",
    "Start date": "Fecha inicio",
    "Start date must be before or equal to end date.": "La fecha inicio debe ser anterior o igual a la fecha fin.",
    "Start date must be within the date range (%(start)s – %(end)s).": "La fecha inicio debe estar dentro del intervalo (%(start)s – %(end)s).",
    "Status based on activities\nOverdue: Due date is already passed\nToday: Activity date is today\nPlanned: Future activities.": "Estado según actividades\nAtrasado: la fecha límite ya pasó\nHoy: la actividad vence hoy\nPlanificado: actividades futuras.",
    "Ter Use Unit": "Unidad de Uso Territorial",
    "Ter-unit sequence": "Secuencia ter-unit",
    "Territorial Base: Recompute ter.unit validity state": "Base territorial: Recalcular estado de validez de unidades",
    "The contact chosen as main is not a manager.": "El contacto elegido como principal no es gestor.",
    "The holder must be the manager (main contact) of the main parcel.": "El titular debe ser el gestor (contacto principal) de la parcela principal.",
    "The main contact exists, but the contact list of the parcel is empty.": "El contacto principal existe, pero la lista de contactos de la parcela está vacía.",
    "The parcel manager and the main contact must be the same person.": "El gestor de la parcela y el contacto principal deben ser la misma persona.",
    "The parcel manager and the property manager must be the same person.": "El gestor de la parcela y el gestor de la finca deben ser la misma persona.",
    "The place is not in the municipality.": "El lugar no pertenece al municipio.",
    "True if today is within date_start and date_end.": "Verdadero si hoy está entre fecha inicio y fecha fin.",
    "URL of the WMS service used to obtain the base image of the parcels and other GIS elements.": "URL del servicio WMS para obtener la imagen base de parcelas y otros elementos SIG.",
    "URL of the WMS service used to obtain the vectorial image of the parcels.": "URL del servicio WMS para obtener la imagen vectorial de las parcelas.",
    "Unable to update geometry: %(details)s": "No se pudo actualizar la geometría: %(details)s",
    "Unexpected error while processing the request.": "Error inesperado al procesar la petición.",
    "Unlock": "Desbloquear",
    "Unlocked": "Desbloqueado",
    "Unnamed": "Sin nombre",
    "Use Types can be nested in a list. You can search by full path and browse children easily.": "Los tipos de uso pueden anidarse. Puede buscar por ruta completa y explorar los hijos con facilidad.",
    "WMS service layer used to obtain the images of the parcels (vectorial elements).": "Capa de servicio WMS para obtener las imágenes de las parcelas (elementos vectoriales).",
    "WMS service layer used to obtain the images of the properties (vectorial elements).": "Capa de servicio WMS para obtener las imágenes de las fincas (elementos vectoriales).",
    "WMS service layers used to obtain the base image of the parcels and other GIS elements.": "Capas de servicio WMS para obtener la imagen base de parcelas y otros elementos SIG.",
    "You cannot create recursive hierarchies (loops).": "No puede crear jerarquías recursivas (bucles).",
    "You cannot reset the code because the partner has parcels.": "No puede restablecer el código porque el contacto tiene parcelas.",
    "You cannot set a child as parent.": "No puede establecer un hijo como padre.",
    "Zoom applied to images obtained from WMS services: 1 means no zoom; > 1 zoom-out; < 1 zoom-in.": "Zoom aplicado a las imágenes WMS: 1 sin zoom; > 1 alejar; < 1 acercar.",
    "ha": "ha",
    "not assigned": "no asignado",
    "ok": "ok",
    "ter_gis_property layer recreated.": "capa ter_gis_property recreada.",
    "ter_parcel_256": "ter_parcel_256",
    "ter_parcel_avatar": "ter_parcel_avatar",
    "ter_property_256": "ter_property_256",
    "ter_property_avatar": "ter_property_avatar",
    "ter_unit_256": "ter_unit_256",
    "ter_unit_avatar": "ter_unit_avatar",
}

def unquote(s):
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1].replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")
    return s

def read_string(lines, i):
    if i >= len(lines): return "", i
    line = lines[i]
    if line.startswith("msgid "): raw = line[6:].strip()
    elif line.startswith("msgstr "): raw = line[7:].strip()
    else: return "", i
    i += 1
    parts = [unquote(raw)] if raw else []
    while i < len(lines) and lines[i].strip().startswith('"'):
        parts.append(unquote(lines[i].strip()))
        i += 1
    return "".join(parts), i

def escape_po(s):
    if not s: return '""'
    out = []
    for line in s.split("\n"):
        out.append('"' + line.replace("\\", "\\\\").replace('"', '\\"') + '"')
    return "\n".join(out)

def main():
    path = "es.po"
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    out = []
    i = 0
    filled = 0
    while i < len(lines):
        if lines[i].startswith("msgid "):
            # Output comment block before this entry (already in out) - no, we need to output from last position
            start = i
            msgid, j = read_string(lines, i)
            i = j
            if i < len(lines) and lines[i].startswith("msgstr "):
                msgstr, k = read_string(lines, i)
                if msgid and not msgstr and msgid in FILL:
                    # Output from start to end of msgid (inclusive), then new msgstr
                    for idx in range(start, j):
                        out.append(lines[idx])
                    trans = FILL[msgid]
                    out.append("msgstr " + escape_po(trans) + "\n")
                    filled += 1
                    i = k
                else:
                    for idx in range(start, k):
                        out.append(lines[idx])
                    i = k
            else:
                for idx in range(start, i):
                    out.append(lines[idx])
            continue
        out.append(lines[i])
        i += 1
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)
    print(f"Filled {filled} empty msgstr")

if __name__ == "__main__":
    main()
