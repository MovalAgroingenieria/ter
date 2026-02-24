# Instructions for Copilot / AI

This repository contains Odoo 18.0 addons (Moval). Follow these guidelines when suggesting or generating code.

## Language

- **Replies to the user**: in Spanish.
- **Source code**: English (docstrings, comments, variable and function names).
- **UI strings** (views, help texts, messages): English in Python/XML. Translations (Spanish, Catalan) go only in `i18n/` (`es.po`, `ca_ES.po`). Do not put visible text in Spanish outside `i18n/`.

## Project and conventions

- **Odoo**: 18.0. Repository modules: territory addons (`base_ter`, `base_ter_analytic`, `l10n_es_territory`, etc.).
- **Code style**: OCA-style conventions.
- **XML (views, data)**: comments only when they explain non-obvious behaviour. Avoid redundant comments on every tree/form/action.
- **File headers**: `# 2026 Moval Agroingeniería` (or year and “Moval Agroingeniería” as per the module).
- In comments and help texts, avoid: references to people (e.g. “jvera”), unnecessary “legacy”, proper names other than the company name.

## Code review

When doing or suggesting a code review:

1. **Readability**: clear code; avoid nested ternaries and overly dense logic.
2. **Security**:
   - Do not build SQL by concatenating strings; use parameters (e.g. `cursor.execute(sql, (param,))`).
   - Passwords and sensitive data: use encryption (AES) and do not expose in logs or UI without permission.
   - Server actions and operational buttons (start/stop instance, odoorc, Restore in Demo, etc.) are usually restricted by groups (e.g. SYS-ADMIN/Manager); do not grant excess permissions.
3. **Consistency**: keep the same style as the rest of the module (names, view structure, permissions).

## Testing and quality

- Tests live in each addon’s `tests/`; use `TransactionCase`, mock `AES_KEY`/`AES_IV` when the code uses encryption.
- Pre-commit: pylint, black, isort, flake8, oca-checks (incl. `oca-checks-po` for `.po`/`.pot`). Do not leave duplicate messages in i18n.

## Useful references

- Conventions and permissions: see each addon’s README (e.g. `base_ter`) and `security/` when applicable.
