#!/usr/bin/env python3
# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# Script to generate base_ter i18n/es.po with Spanish (Spain) translations from base_ter.pot
# Run from base_ter directory: python3 i18n/update_es.py

import re
import sys

# Spanish (Spain) translations for base_ter - es_ES
TRANSLATIONS = {
    "% Participation": "% Participación",
    "'Parcel - %s - %s' % (object.name, object.partner_id.name or '')": "'Parcela - %s - %s' % (object.name, object.partner_id.name or '')",
    "'Parcels Report - %s' % (object.name or '')": "'Informe de parcelas - %s' % (object.name or '')",
    "'Properties Report - %s' % (object.name or '')": "'Informe de fincas - %s' % (object.name or '')",
    "'Property - %s - %s' % (object.name, object.partner_id.name or '')": "'Finca - %s - %s' % (object.name, object.partner_id.name or '')",
    "(VAT:&amp;nbsp;": "(NIF:&amp;nbsp;",
    "(holder)": "(titular)",
    "(parcel code)": "(código de parcela)",
    "(parcel manager)": "(gestor de parcela)",
    "(property name)": "(nombre de finca)",
    "<br/>\n                                Area:": "<br/>\n                                Superficie:",
    "<br/>\n                                Parcels Area:": "<br/>\n                                Superficie parcelas:",
    "<br/>\n                                Place:": "<br/>\n                                Lugar:",
    "<i class=\"fa fa-ter-property fa-lg me-2\" style=\"color:darkgreen;\" "
    'title=\"holder_icon\"/>': "<i class=\"fa fa-ter-property fa-lg me-2\" style=\"color:darkgreen;\" title=\"titular\"/>",
    "<span class=\"fa fa-picture-o\"/>\n                            <span>Aerial Image</span>": "<span class=\"fa fa-picture-o\"/>\n                            <span>Imagen aérea</span>",
    "<span class=\"fa fa-picture-o\"/>\n                            <span>Aerial Images</span>": "<span class=\"fa fa-picture-o\"/>\n                            <span>Imágenes aéreas</span>",
    "<span class=\"fa fa-ter-parcel\"/>\n                            <span>Parcel</span>": "<span class=\"fa fa-ter-parcel\"/>\n                            <span>Parcela</span>",
    "<span class=\"fa fa-ter-parcel\"/>\n                            <span>Parcels</span>": "<span class=\"fa fa-ter-parcel\"/>\n                            <span>Parcelas</span>",
    "<span class=\"fa fa-ter-property\"/>\n                            <span>Properties</span>": "<span class=\"fa fa-ter-property\"/>\n                            <span>Fincas</span>",
    "<span class=\"fa fa-ter-property\"/>\n                            <span>Property</span>": "<span class=\"fa fa-ter-property\"/>\n                            <span>Finca</span>",
    "<span class=\"fa fa-user\"/>\n                            <span>Partner</span>": "<span class=\"fa fa-user\"/>\n                            <span>Contacto</span>",
    "<span class=\"o_stat_value\"/>\n                            <span class=\"o_stat_text\">Use Type</span>": "<span class=\"o_stat_value\"/>\n                            <span class=\"o_stat_text\">Tipos de usos</span>",
    "<span class=\"oe_inline\">%</span>": "<span class=\"oe_inline\">%</span>",
    "<span class=\"oe_inline\">EPSG:</span>": "<span class=\"oe_inline\">EPSG:</span>",
    "<span class=\"oe_inline\">ha</span>": "<span class=\"oe_inline\">ha</span>",
    "<span>Area official parcels</span>": "<span>Superficie oficial parcelas</span>",
    "<span>Area official</span>": "<span>Superficie oficial</span>",
    "<span>Change code</span>": "<span>Cambiar código</span>",
    "<span>GIS Area</span>": "<span>Superficie SIG</span>",
    "<span>GIS Perimeter</span>": "<span>Perímetro SIG</span>",
    "<span>GIS Viewer</span>": "<span>Visor SIG</span>",
    "<span>Municipality</span>": "<span>Municipio</span>",
    "<span>Number of parcels</span>": "<span>Número de parcelas</span>",
    "<span>Number of properties</span>": "<span>Número de fincas</span>",
    "<span>Parcel Viewer</span>": "<span>Visor de parcelas</span>",
    "<span>Place</span>": "<span>Lugar</span>",
    "<span>Printing date</span>": "<span>Fecha de impresión</span>",
    "<span>Prop. Viewer</span>": "<span>Visor fincas</span>",
    "<span>Tags</span>": "<span>Etiquetas</span>",
    "<span>Total Area</span>": "<span>Superficie total</span>",
    "<span>m</span>": "<span>m</span>",
    "<span>m²</span>": "<span>m²</span>",
    "<span>parcel</span>": "<span>parcela</span>",
    "<span>parcels</span>": "<span>parcelas</span>",
    "<strong>Area</strong>": "<strong>Superficie</strong>",
    "<strong>Municipality</strong>": "<strong>Municipio</strong>",
    "<strong>Parcel</strong>": "<strong>Parcela</strong>",
    "<strong>Property</strong>": "<strong>Finca</strong>",
    "<strong>Total Parcel Area</strong>": "<strong>Superficie total parcelas</strong>",
    "AERIAL IMAGE AND GIS DATA": "IMAGEN AÉREA Y DATOS SIG",
    "Action Needed": "Acción requerida",
    "Active": "Activo",
    "Activities": "Actividades",
    "Activity Exception Decoration": "Decoración de excepción de actividad",
    "Activity State": "Estado de actividad",
    "Activity Type Icon": "Icono de tipo de actividad",
    "Address Data": "Datos de dirección",
    "Aerial Image": "Imagen aérea",
    "Aerial Image (GIS preview)": "Imagen aérea (vista SIG)",
    "Aerial Image (medium size)": "Imagen aérea (tamaño medio)",
    "Aerial Image (medium size, non-persistent)": "Imagen aérea (tamaño medio, no persistente)",
    "Aerial Image (non-persistent)": "Imagen aérea (no persistente)",
    "Aerial Image (small size)": "Imagen aérea (tamaño pequeño)",
    "Aerial Image (zoom)": "Imagen aérea (zoom)",
    "Aerial Image Key": "Clave de imagen aérea",
    "Aerial Image shown (base64)": "Imagen aérea mostrada (base64)",
    "Aerial Images": "Imágenes aéreas",
    "Aerial image not found": "Imagen aérea no encontrada",
    "Aggregated Values": "Valores agregados",
    "Agregated Values": "Valores agregados",
    "Alert threshold due to the difference between the official area and the GIS area": "Umbral de aviso por diferencia entre superficie oficial y superficie SIG",
    "All Attributes": "Todos los atributos",
    "Allow importing parcels and properties from KML files.": "Permitir importar parcelas y fincas desde archivos KML.",
    "Allowed Values": "Valores permitidos",
    "Alternative area unit name": "Nombre alternativo de la unidad de superficie",
    "Alternative unit equivalence (ha)": "Equivalencia de unidad alternativa (ha)",
    "Analytic Account": "Cuenta analítica",
    "Ancestors": "Antecesores",
    "Apply": "Aplicar",
    "Archive": "Archivar",
    "Archived": "Archivado",
    "Area": "Superficie",
    "Area GIS (ha)": "Superficie SIG (ha)",
    "Area Parcels": "Superficie parcelas",
    "Area unit": "Unidad de superficie",
    "Area unit is hectare": "La unidad de superficie es la hectárea",
    "Area unit name": "Nombre de la unidad de superficie",
    "Areas": "Superficies",
    "Areas OK?": "¿Superficies correctas?",
    "Attachment Count": "Número de adjuntos",
    "Attribute": "Atributo",
    "Attribute Value": "Valor del atributo",
    "Attribute Values": "Valores del atributo",
    "Attributes": "Atributos",
    "Auto-generated from company sequence when left empty.": "Generado automáticamente por la secuencia de la empresa si se deja vacío.",
    "BASIC DATA": "DATOS BÁSICOS",
    "Base WMS URL": "URL base WMS",
    "Base WMS layers": "Capas WMS base",
    "Bounding box as string": "Caja de delimitación como texto",
    "Campaign Type": "Tipo de campaña",
    "Cancel": "Cancelar",
    "Census": "Censo y Territorio",
    "Change parcel code": "Cambiar código de parcela",
    "Check areas!": "¡Comprobar superficies!",
    "Children": "Hijos",
    "Close": "Cerrar",
    "Close preview": "Cerrar vista previa",
    "Code": "Código",
    "Code (name)": "Código (nombre)",
    "Code (numeric)": "Código (numérico)",
    "Color Index": "Índice de color",
    "Companies": "Empresas",
    "Company (y/n)": "Empresa (s/n)",
    "Complete Name": "Nombre completo",
    "Configuration": "Configuración",
    "Contact": "Contacto",
    "Contacts": "Contactos",
    "Contacts of parcel": "Contactos de la parcela",
    "Create a new manager": "Crear un nuevo gestor",
    "Create a new parcel": "Crear una nueva parcela",
    "Create a new parcel tag": "Crear una nueva etiqueta de parcela",
    "Create a new partner profile": "Crear un nuevo perfil de contacto",
    "Create a new property": "Crear una nueva finca",
    "Create a new property tag": "Crear una nueva etiqueta de finca",
    "Create parcels or use filters to analyze existing data.": "Cree parcelas o use filtros para analizar los datos existentes.",
    "Create your first use type": "Cree su primer tipo de uso",
    "Created by": "Creado por",
    "Created on": "Creado el",
    "Data of the parcel": "Datos de la parcela",
    "Data of the partner": "Datos del contacto",
    "Date Range": "Intervalo de fechas",
    "Date Range Type": "Tipo de intervalo de fechas",
    "Date Ranges": "Intervalos de fechas",
    "Date Ranges Ter": "Intervalos de fechas (Ter)",
    "Date Ranges Types Ter": "Tipos de intervalos de fechas (Ter)",
    "Dates": "Fechas",
    "Date Range Periods": "Periodos rangos de fecha",
    "Delete aerial image": "Eliminar imagen aérea",
    "Descendants": "Descendientes",
    "Description": "Descripción",
    "Description to provide more information and context about this ter_unit": "Descripción para aportar más información y contexto sobre esta unidad territorial",
    "Detail Models": "Modelos de detalle",
    "Dialog box to set a parcel code": "Diálogo para establecer el código de parcela",
    "Dialog box to set a partner code": "Diálogo para establecer el código de contacto",
    "Director": "Director",
    "Display Name": "Nombre a mostrar",
    "Done": "Hecho",
    "Draft": "Borrador",
    "EPSG": "EPSG",
    "EWKT Centroid": "Centroide EWKT",
    "EWKT Geometry": "Geometría EWKT",
    "EWKT Geometry for oriented envelope": "Geometría EWKT del contorno orientado",
    "Each attribute can only appear once per unit.": "Cada atributo solo puede aparecer una vez por unidad.",
    "End date": "Fecha fin",
    "End date must be within the date range (%(start)s – %(end)s).": "La fecha fin debe estar dentro del intervalo (%(start)s – %(end)s).",
    "Equivalence, in ha, of the chosen area unit.": "Equivalencia en ha de la unidad de superficie elegida.",
    "Farm/Property": "Finca",
    "Farming": "En cultivo",
    "File": "Archivo",
    "Industrial": "Industrial",
    "Livestock": "Ganadero",
    "Recreational": "Recreativo",
    "Urban": "Urbano",
    "Water reservoir": "Balsa",
    "ha": "ha",
    "parcel logo": "logotipo parcela",
    "ter_parcel_256": "ter_parcel_256",
    "ter_parcel_avatar": "ter_parcel_avatar",
    "ter_property_256": "ter_property_256",
    "ter_property_avatar": "ter_property_avatar",
    "ter_unit_256": "ter_unit_256",
    "ter_unit_avatar": "ter_unit_avatar",
    "Validate": "Validar",
    "Validated": "Validado",
    "Validity State": "Estado de validez",
    "Value": "Valor",
    "Vector WMS URL": "URL WMS vectorial",
    "Viewer URL": "URL del visor",
    "WMS Services: Height of the images": "Servicios WMS: Altura de las imágenes",
    "WMS Services: Zoom": "Servicios WMS: Zoom",
    "WMS of the base image: Layers": "WMS de la imagen base: Capas",
    "WMS of the base image: URL": "WMS de la imagen base: URL",
    "WMS of the vectorial image: Filtered parcels (y/n)": "WMS de la imagen vectorial: Parcelas filtradas (s/n)",
    "WMS of the vectorial image: Filtered properties (y/n)": "WMS de la imagen vectorial: Fincas filtradas (s/n)",
    "WMS of the vectorial image: Name of the parcels layer": "WMS de la imagen vectorial: Nombre de la capa de parcelas",
    "WMS of the vectorial image: Name of the properties layer": "WMS de la imagen vectorial: Nombre de la capa de fincas",
    "WMS of the vectorial image: URL": "WMS de la imagen vectorial: URL",
    "WMS service layer used to obtain the images of the parcels (vectorial elements).": "Capa de servicio WMS para obtener las imágenes de las parcelas (elementos vectoriales).",
    "WMS service layer used to obtain the images of the properties (vectorial elements).": "Capa de servicio WMS para obtener las imágenes de las fincas (elementos vectoriales).",
    "WMS service layers used to obtain the base image of the parcels and other GIS elements.": "Capas de servicio WMS para obtener la imagen base de parcelas y otros elementos SIG.",
    "Warnings": "Avisos",
    "With GIS link: No": "Con enlace SIG: No",
    "With GIS link: Yes": "Con enlace SIG: Sí",
    "With parcel manager: No": "Con gestor de parcela: No",
    "With parcel manager: Yes": "Con gestor de parcela: Sí",
    "Writer User": "Usuario editor",
    "Wrong partner code.": "Código de contacto incorrecto.",
    "Zoom applied to images obtained from WMS services: 1 means no zoom; > 1 zoom-out; < 1 zoom-in.": "Zoom aplicado a las imágenes WMS: 1 sin zoom; > 1 alejar; < 1 acercar.",
    "e.g. Industrial vehicle": "p. ej. Vehículo industrial",
    "e.g. PARCEL- or FINCA-": "p. ej. PARCELA- o FINCA-",
    "Filename": "Nombre de archivo",
    "Followers": "Seguidores",
    "Followers (Partners)": "Seguidores (contactos)",
    "Font awesome icon e.g. fa-tasks": "Icono Font Awesome p. ej. fa-tasks",
    "For the integrated preview, arguments to add to the GIS viewer URL.": "Para la vista previa integrada, argumentos a añadir a la URL del visor SIG.",
    "Force parcel manager to be property owner": "Forzar que el gestor de parcela sea el titular de la finca",
    "Force the parcel manager and the property owner to be the same": "Forzar que el gestor de parcela y el titular de la finca sean el mismo",
    "Frame": "Marco",
    "Frame for the preview": "Marco de la vista previa",
    "GIS": "SIG",
    "GIS Area (m²)": "Superficie SIG (m²)",
    "GIS Code": "Código SIG",
    "GIS Data": "Datos SIG",
    "GIS Link (minimal version)": "Enlace SIG (versión mínima)",
    "GIS Link (public)": "Enlace SIG (público)",
    "GIS Link (technical)": "Enlace SIG (técnico)",
    "GIS Parcel": "Parcela SIG",
    "GIS Parcels": "Parcelas SIG",
    "GIS Perimeter (m)": "Perímetro SIG (m)",
    "GIS Preview": "Vista previa SIG",
    "GIS Preview: Additional URL arguments": "Vista previa SIG: Argumentos adicionales de URL",
    "GIS Viewer": "Visor SIG",
    "GIS Viewer: Password for the technical mode": "Visor SIG: Contraseña del modo técnico",
    "GIS Viewer: Spatial Reference": "Visor SIG: Referencia espacial",
    "GIS Viewer: URL": "Visor SIG: URL",
    "GIS Viewer: User name for the technical mode": "Visor SIG: Usuario del modo técnico",
    "General": "Base Territorial",
    "GeoJSON Geometry": "Geometría GeoJSON",
    "Geometry (EWKT)": "Geometría (EWKT)",
    "Geometry in EWKT format (e.g. SRID=25830;POLYGON(...)). If set, parcel is "
    "auto-assigned as the parcel with maximum overlap.": "Geometría en formato EWKT (p. ej. SRID=25830;POLYGON(...)). Si se define, la parcela se asigna automáticamente como la de mayor solapamiento.",
    "Global Viewer": "Visor global",
    "Group By": "Agrupar por",
    "Has Message": "Tiene mensaje",
    "Height, in pixels, of images captured from WMS services (the width will be "
    "calculated automatically to preserve the original proportions).": "Altura en píxeles de las imágenes obtenidas de servicios WMS (el ancho se calcula para mantener la proporción).",
    "Holder": "Titular",
    "ID": "ID",
    "Icon": "Icono",
    "Icon to indicate an exception activity.": "Icono que indica una actividad excepcional.",
    "Identification": "Identificación",
    "Identifier of partnerlink": "Identificador del enlace de contacto",
    "If checked, new messages require your attention.": "Si está marcado, los nuevos mensajes requieren su atención.",
    "If checked, some messages have a delivery error.": "Si está marcado, algunos mensajes tienen error de envío.",
    "If the area unit is not the ha, name of the alternative area unit.": "Si la unidad de superficie no es la ha, nombre de la unidad alternativa.",
    "If checked, only the central parcel will be displayed; otherwise, all "
    "parcels will be displayed.": "Si está marcado, solo se mostrará la parcela central; en caso contrario, todas las parcelas.",
    "If checked, only the central property will be displayed; otherwise, all "
    "properties will be displayed.": "Si está marcado, solo se mostrará la finca central; en caso contrario, todas las fincas.",
    "If checked, the area unit will be the ha; otherwise you can choose another unit of area.": "Si está marcado, la unidad de superficie será la ha; en caso contrario puede elegir otra.",
    "If enabled, any parcel associated with a property that has an owner must have that owner as its manager.": "Si está activo, toda parcela asociada a una finca con titular debe tener a ese titular como gestor.",
    "If enabled, date ranges of this type can be used to define periods for territorial unit uses.": "Si está activo, los intervalos de este tipo pueden usarse para definir periodos de uso de unidades de uso territorial.",
    "Image": "Imagen",
    "Image height (px)": "Altura de imagen (px)",
    "Image zoom": "Zoom de imagen",
    "Images of parcels (global)": "Imágenes de parcelas (global)",
    "Images of properties (global)": "Imágenes de fincas (global)",
    "Images of territorial units (all)": "Imágenes de unidades de uso territorial (todas)",
    "Import": "Importar",
    "Import KML": "Importar KML",
    "Import KML file to Parcels or Properties": "Importar archivo KML a Parcelas o Fincas",
    "Import to": "Importar a",
    "In Range": "Dentro del intervalo",
    "Incorrect value for \"Official Area\".": "Valor incorrecto de «Superficie oficial».",
    "Incorrect value of \"Alert threshold due to the difference between the "
    "official area and the GIS area\".": "Valor incorrecto de «Umbral de aviso por diferencia entre superficie oficial y SIG».",
    "Incorrect value of \"GIS Viewer: Spatial Reference\".": "Valor incorrecto de «Visor SIG: Referencia espacial».",
    "Incorrect value of \"Percentage\".": "Valor incorrecto de «Porcentaje».",
    "Incorrect value of \"Standard area unit: Equivalence in ha\".": "Valor incorrecto de «Unidad de superficie estándar: Equivalencia en ha».",
    "Incorrect value of \"WMS Services: Height of the images\".": "Valor incorrecto de «Servicios WMS: Altura de las imágenes».",
    "Incorrect value of \"WMS Services: Zoom\".": "Valor incorrecto de «Servicios WMS: Zoom».",
    "Individuals": "Particulares",
    "Internal Notes": "Notas internas",
    "Internal notes...": "Notas internas...",
    "Is Follower": "Es seguidor",
    "Is Main": "Es principal",
    "Is manager": "Es gestor",
    "Is manager: No": "Es gestor: No",
    "Is manager: Yes": "Es gestor: Sí",
    "Is this a base_ter action?": "¿Es una acción de base_ter?",
    "KML File": "Archivo KML",
    "KML Importer": "Importador KML",
    "KML file with Placemarks containing Polygon geometries (WGS84).": "Archivo KML con marcadores con geometrías Polígono (WGS84).",
    "Last Updated by": "Última actualización por",
    "Last Updated on": "Última actualización el",
    "Layer of properties": "Capa de fincas",
    "Localization": "Localización",
    "Location": "Ubicación",
    "Lock": "Bloquear",
    "Locked": "Bloqueado",
    "Main Parcel": "Parcela principal",
    "Manage managers.": "Gestionar gestores.",
    "Manage parcel tags.": "Gestionar etiquetas de parcela.",
    "Manage parcels.": "Gestionar parcelas.",
    "Manage profiles.": "Gestionar perfiles.",
    "Manage properties.": "Gestionar fincas.",
    "Manage property tags.": "Gestionar etiquetas de finca.",
    "Management": "Gestión",
    "Manager": "Gestor",
    "Manager / Holder": "Gestor / Titular",
    "Managers": "Gestores",
    "Mapped to polygon": "Asignado a polígono",
    "Maximum GIS area difference (%)": "Diferencia máxima de superficie SIG (%)",
    "Message Delivery error": "Error de envío de mensaje",
    "Messages": "Mensajes",
    "Municipalities": "Municipios",
    "Municipality": "Municipio",
    "Municipality assigned to all imported records.": "Municipio asignado a todos los registros importados.",
    "Municipality:": "Municipio:",
    "My Activity Deadline": "Fecha límite de mi actividad",
    "Name": "Nombre",
    "Name cannot be empty.": "El nombre no puede estar vacío.",
    "Name of the technical user.": "Nombre del usuario técnico.",
    "Name prefix": "Prefijo del nombre",
    "Next Activity Calendar Event": "Próximo evento de actividad",
    "Next Activity Deadline": "Fecha límite de la próxima actividad",
    "Next Activity Summary": "Resumen de la próxima actividad",
    "Next Activity Type": "Tipo de próxima actividad",
    "No parcel data to analyze": "No hay datos de parcelas para analizar",
    "No territorial units yet": "Aún no hay unidades de uso territorial",
    "Not Started": "No iniciado",
    "Not modifiable": "No modificable",
    "Notes": "Notas",
    "Number of Actions": "Número de acciones",
    "Number of errors": "Número de errores",
    "Number of messages requiring action": "Número de mensajes que requieren acción",
    "Number of messages with delivery error": "Número de mensajes con error de envío",
    "Number of parcels": "Número de parcelas",
    "Number of properties": "Número de fincas",
    "Official Area": "Superficie oficial",
    "Official Area (m²)": "Superficie oficial (m²)",
    "Official Code": "Código oficial",
    "Official area must be greater than or equal to 0.": "La superficie oficial debe ser mayor o igual a 0.",
    "Only central parcel": "Solo parcela central",
    "Only central property": "Solo finca central",
    "Optional prefix for record names (e.g. 'PARCEL-' or 'FINCA-').": "Prefijo opcional para nombres de registro (p. ej. 'PARCELA-' o 'FINCA-').",
    "Optional: assign as manager (property) or use for parcel partner link.": "Opcional: asignar como gestor (finca) o usar para enlace de contacto de parcela.",
    "Options": "Opciones",
    "Out of Range": "Fuera del intervalo",
    "Owner": "Titular",
    "Parcel": "Parcela",
    "Parcel (DB)": "Parcela (BD)",
    "Parcel (GIS)": "Parcela (SIG)",
    "Parcel Area": "Superficie de parcela",
    "Parcel Area (m²)": "Superficie de parcela (m²)",
    "Parcel Code": "Código de parcela",
    "Parcel Holder": "Titular de parcela",
    "Parcel Manager": "Gestor de parcela",
    "Parcel Partner": "Contacto de parcela",
    "Parcel Partner Link": "Enlace contacto parcela",
    "Parcel Partner Report": "Informe contacto parcela",
    "Parcel Report": "Informe de parcela",
    "Parcel Tag": "Etiqueta de parcela",
    "Parcel Tags": "Etiquetas de parcela",
    "Parcel vector layer": "Capa vectorial de parcelas",
    "Parcels": "Parcelas",
    "Parcels Area": "Superficie de parcelas",
    "Parcels Report": "Informe de parcelas",
    "Parcels of the property": "Parcelas de la finca",
    "Parcels |": "Parcelas |",
    "Parent": "Padre",
    "Parent Path": "Ruta del padre",
    "Partner Code": "Código de contacto",
    "Partner Code (as string)": "Código de contacto (como texto)",
    "Partner Profile": "Perfil de contacto",
    "Partner-Links": "Enlaces de contacto",
    "Password of the technical user.": "Contraseña del usuario técnico.",
    "Path": "Ruta",
    "Percentage": "Porcentaje",
    "Percentage (of the official area of a parcel) designated as the maximum "
    "allowable threshold for the difference between this official area and the "
    "GIS area (if zero, no warning will be displayed).": "Porcentaje (de la superficie oficial de la parcela) que define el umbral máximo de diferencia entre esa superficie oficial y la SIG (si es cero, no se mostrará aviso).",
    "Place": "Lugar",
    "Places": "Lugares",
    "Please, enter a positive partner code (or clear data)": "Introduzca un código de contacto positivo (o borre los datos)",
    "Please, update the parcel code": "Actualice el código de parcela",
    "Preview": "Vista previa",
    "Preview URL arguments": "Argumentos URL de vista previa",
    "Printing date": "Fecha de impresión",
    "Profile": "Perfil",
    "Profile:": "Perfil:",
    "Profiles": "Perfiles",
    "Properties": "Fincas",
    "Properties Report": "Informe de fincas",
    "Property": "Finca",
    "Property Area": "Superficie de finca",
    "Property Area (m²)": "Superficie de finca (m²)",
    "Property Data": "Datos de finca",
    "Property Manager": "Gestor de finca",
    "Property Name": "Nombre de finca",
    "Property Partner Report": "Informe contacto finca",
    "Property Report": "Informe de finca",
    "Property Tag": "Etiqueta de finca",
    "Property Tags": "Etiquetas de finca",
    "Property vector layer": "Capa vectorial de fincas",
    "Property:": "Finca:",
    "Province": "Provincia",
    "Provinces": "Provincias",
    "Ratings": "Valoraciones",
    "Reader User": "Usuario lector",
    "Reference": "Referencia",
    "Refresh": "Actualizar",
    "Refresh aerial image": "Actualizar imagen aérea",
    "Regenerate Image": "Regenerar imagen",
    "Region": "Región",
    "Regions": "Regiones",
    "Reports": "Informes",
    "Required": "Obligatorio",
    "Required 100%": "Requerido 100%",
    "Responsible User": "Usuario responsable",
    "Result Message": "Mensaje de resultado",
    "SRID=25830;POLYGON((...))": "SRID=25830;POLYGON((...))",
    "Scheduled Actions": "Acciones programadas",
    "Search Territorial Units": "Buscar unidades de uso territorial",
    "Search Use Types": "Buscar tipos de usos",
    "Search parcels": "Buscar parcelas",
    "Search partner-links": "Buscar enlaces de contacto",
    "Search partners": "Buscar contactos",
    "Search profiles": "Buscar perfiles",
    "Search properties": "Buscar fincas",
    "Search tags": "Buscar etiquetas",
    "See in GIS viewer": "Ver en visor SIG",
    "See parcels in GIS viewer": "Ver parcelas en visor SIG",
    "See properties in GIS viewer": "Ver fincas en visor SIG",
    "Sequence": "Secuencia",
    "Sequence used to generate ter.unit names. Name format: "
    "{type_code}-{date_start}-{date_end}-{parcel_code}-{sequence}.": "Secuencia para generar nombres de unidades territoriales. Formato: {type_code}-{date_start}-{date_end}-{parcel_code}-{sequence}.",
    "Set to Draft": "Establecer a borrador",
    "Settings": "Ajustes",
    "Spatial reference of the layers stored in the database (if changed, layers "
    "will be automatically reprojected).": "Referencia espacial de las capas en la base de datos (si se cambia, se reproyectarán automáticamente).",
    "Standard Type (y/n)": "Tipo estándar (s/n)",
    "Standard area unit: Equivalence in ha": "Unidad de superficie estándar: Equivalencia en ha",
    "Standard area unit: Name": "Unidad de superficie estándar: Nombre",
    "Standard area unit: ha (y/n)": "Unidad de superficie estándar: ha (s/n)",
    "Start date": "Fecha inicio",
    "Start date must be within the date range (%(start)s – %(end)s).": "La fecha inicio debe estar dentro del intervalo (%(start)s – %(end)s).",
    "State": "Estado",
    "Status based on activities\n"
    "Overdue: Due date is already passed\n"
    "Today: Activity date is today\n"
    "Planned: Future activities.": "Estado según actividades\nAtrasado: la fecha límite ya pasó\nHoy: la actividad vence hoy\nPlanificado: actividades futuras.",
    "Street type settings": "Configuración de tipos de vía",
    "TER-UNIT": "UNIDAD-TER",
    "Tag Name": "Nombre de etiqueta",
    "Tags": "Etiquetas",
    "Tags...": "Etiquetas...",
    "Technical Actions": "Acciones técnicas",
    "Technical password": "Contraseña técnica",
    "Technical user": "Usuario técnico",
    "Ter Unit": "Unidad de Uso Territorial",
    "Ter Unit Attribute Value": "Valor de atributo de unidad de uso territorial",
    "Ter Unit Sequence": "Secuencia de unidad de uso territorial",
    "Ter Use Type": "Uso territorial",
    "Cultivable": "Cultivable",
    "Territorial use type": "Tipo de uso territorial",
    "Territorial Base: Recompute ter.unit validity state": "Base territorial: Recalcular estado de validez de unidades",
    "Territorial Base: Refresh all aerial images of the parcels": "Base territorial: Actualizar todas las imágenes aéreas de parcelas",
    "Territorial Base: Refresh all aerial images of the properties": "Base territorial: Actualizar todas las imágenes aéreas de fincas",
    "Territorial Base: Refresh layer of properties": "Base territorial: Actualizar capa de fincas",
    "Territorial Unit": "Unidad de Uso Territorial",
    "Territorial Units": "Unidades de Uso Territorial",
    "Territory": "Territorio",
    "Threshold exceeded (difference between official and GIS areas)": "Umbral superado (diferencia entre superficies oficial y SIG)",
    "Threshold exceeded (difference between official and GIS areas) -str-": "Umbral superado (diferencia entre superficies oficial y SIG)",
    "Top level": "Nivel superior",
    "Total Area": "Superficie total",
    "True if today is within date_start and date_end.": "Verdadero si hoy está entre fecha inicio y fecha fin.",
    "Type": "Tipo",
    "Type of the exception activity on record.": "Tipo de actividad excepcional del registro.",
    "URL of the integrated GIS viewer.": "URL del visor SIG integrado.",
    "URL of the WMS service used to obtain the base image of the parcels and other GIS elements.": "URL del servicio WMS para obtener la imagen base de parcelas y otros elementos SIG.",
    "URL of the WMS service used to obtain the vectorial image of the parcels.": "URL del servicio WMS para obtener la imagen vectorial de las parcelas.",
    "Use Types can be nested in a list. You can search by full path and browse children easily.": "Los tipos de uso pueden anidarse. Puede buscar por ruta completa y explorar los hijos con facilidad.",
    "Unit": "Unidad",
    "Units": "Unidades",
    "Unlock": "Desbloquear",
    "Unlocked": "Desbloqueado",
    "Usable for Unit Use": "Utilizable para uso de unidad",
    "Use Type": "Tipo de uso",
    "Use Type Attribute": "Atributo de tipo de uso",
    "Use Type Attribute Value": "Valor de atributo de tipo de uso",
    "Use Types": "Tipos de usos",
    "Use of GIS viewers": "Uso de visores SIG",
    "Usufructuary": "Usufructuario",
    "VAT": "NIF",
}

def unquote_po(s):
    """Extract and unescape content from a PO quoted string (one line)."""
    s = s.strip()
    if not s.startswith('"') or not s.endswith('"'):
        return s
    inner = s[1:-1].replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")
    return inner


def read_po_string(lines, start_idx):
    """Read one msgid or msgstr value from lines starting at start_idx.
    Returns (decoded_string, next_line_index).
    """
    idx = start_idx
    if idx >= len(lines):
        return "", idx
    line = lines[idx]
    if line.startswith("msgid "):
        first = line[6:].strip()
    elif line.startswith("msgstr "):
        first = line[7:].strip()
    else:
        return "", idx
    idx += 1
    parts = []
    if first:
        parts.append(unquote_po(first))
    while idx < len(lines) and lines[idx].strip().startswith('"'):
        parts.append(unquote_po(lines[idx].strip()))
        idx += 1
    return "".join(parts), idx


def parse_pot(content):
    """Parse POT content into list of (comment_block, msgid, msgstr)."""
    lines = content.splitlines(keepends=True)
    blocks = []
    i = 0
    while i < len(lines):
        if i < len(lines) and not lines[i].startswith("#"):
            i += 1
            continue
        comments = []
        while i < len(lines) and lines[i].startswith("#"):
            comments.append(lines[i])
            i += 1
        if i >= len(lines) or not lines[i].startswith("msgid "):
            continue
        msgid_val, i = read_po_string(lines, i)
        if i >= len(lines) or not lines[i].startswith("msgstr "):
            blocks.append((comments, msgid_val, None))
            continue
        msgstr_val, i = read_po_string(lines, i)
        blocks.append((comments, msgid_val, msgstr_val))
    return blocks

def escape_po(s):
    if s == "":
        return '""'
    out = []
    for line in s.split("\n"):
        out.append('"' + line.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"')
    return "\n".join(out)

def main():
    pot_path = "i18n/base_ter.pot"
    es_path = "i18n/es.po"
    with open(pot_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    blocks = parse_pot(content)
    header_done = False
    out = []
    for comments, msgid, _ in blocks:
        if msgid == "" and not header_done:
            out.append("".join(comments))
            out.append('msgid ""\n')
            out.append('msgstr ""\n')
            out.append('"Project-Id-Version: Odoo Server 18.0\\n"\n')
            out.append('"Report-Msgid-Bugs-To: \\n"\n')
            out.append('"POT-Creation-Date: 2026-02-04 05:18+0000\\n"\n')
            out.append('"PO-Revision-Date: 2026-02-10 12:00+0000\\n"\n')
            out.append('"Last-Translator: Moval Agroingeniería <info@moval.es>\\n"\n')
            out.append('"Language-Team: Spanish (Spain)\\n"\n')
            out.append('"Language: es_ES\\n"\n')
            out.append('"MIME-Version: 1.0\\n"\n')
            out.append('"Content-Type: text/plain; charset=UTF-8\\n"\n')
            out.append('"Content-Transfer-Encoding: 8bit\\n"\n')
            out.append('"Plural-Forms: nplurals=2; plural=(n != 1);\\n"\n')
            header_done = True
            continue
        out.append("".join(comments))
        out.append("msgid " + escape_po(msgid) + "\n")
        trans = TRANSLATIONS.get(msgid, "")
        if not trans and msgid in TRANSLATIONS:
            trans = TRANSLATIONS[msgid]
        out.append("msgstr " + escape_po(trans) + "\n")
    
    with open(es_path, "w", encoding="utf-8") as f:
        f.write("".join(out))
    print(f"Written {es_path} with {len(blocks)} entries")

if __name__ == "__main__":
    main()
