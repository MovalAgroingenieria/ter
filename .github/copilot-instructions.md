# Instrucciones para Copilot / AI

Este repositorio contiene addons de Odoo 18.0 (Moval). Sigue estas directrices al sugerir o generar código.

## Idioma

- **Respuestas al usuario**: en español.
- **Código fuente**: inglés (docstrings, comentarios, nombres de variables y funciones).
- **Cadenas de interfaz** (vistas, ayudas, mensajes): en inglés en Python/XML. Las traducciones (español, catalán) van solo en `i18n/` (`es.po`, `ca_ES.po`). No poner texto visible en español fuera de `i18n/`.

## Proyecto y convenciones

- **Odoo**: 18.0. Módulos del repositorio: addons de territorio (`base_ter`, `base_ter_analytic`, `l10n_es_territory`, etc.).
- **Estilo código**: convenciones tipo OCA (OCA-style).
- **XML (vistas, datos)**: comentarios solo cuando expliquen comportamiento no obvio. Evitar comentarios redundantes en cada árbol/formulario/acción.
- **Cabeceras de archivo**: `# 2026 Moval Agroingeniería` (o año y “Moval Agroingeniería” según el módulo).
- Evitar en comentarios y ayudas: referencias a personas (p. ej. “jvera”), “legacy” innecesario, nombres propios que no sean el de la empresa.

## Code review

Cuando hagas o sugieras una revisión de código:

1. **Legibilidad**: código claro; evitar ternarios anidados y lógica excesivamente densa.
2. **Seguridad**:
   - No construir SQL con concatenación de strings; usar parámetros (ej. `cursor.execute(sql, (param,))`).
   - Contraseñas y datos sensibles: usar cifrado (AES) y no exponer en logs ni en UI sin permiso.
   - Acciones de servidor y botones operativos (start/stop instancia, odoorc, Restore in Demo, etc.) suelen estar restringidos por grupos (p. ej. SYS-ADMIN/Manager); no dar permisos de más.
3. **Consistencia**: mantener el mismo estilo que el resto del módulo (nombres, estructura de vistas, permisos).

## Testing y calidad

- Los tests están en `tests/` de cada addon; usar `TransactionCase`, mockear `AES_KEY`/`AES_IV` cuando el código use cifrado.
- Pre-commit: pylint, black, isort, flake8, oca-checks (incl. `oca-checks-po` para `.po`/`.pot`). No dejar mensajes duplicados en i18n.

## Referencias útiles

- Convenciones y permisos: ver README de cada addon (p. ej. `base_ter`) y `security/` cuando aplique.
