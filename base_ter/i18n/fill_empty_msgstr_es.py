#!/usr/bin/env python3
"""Fill empty msgstr in es.po with msgid (identity). Use for numeric/data entries."""
from pathlib import Path

PO = Path(__file__).resolve().parent / "es.po"
lines = PO.read_text(encoding="utf-8").split("\n")
out = []
i = 0
filled = 0
while i < len(lines):
    line = lines[i]
    out.append(line)
    # Single-line msgid "VALUE" followed by msgstr "" or by blank line -> fill msgstr
    if line.startswith('msgid "') and line != 'msgid ""':
        rest = line[7:]
        if rest.endswith('"'):
            value = rest[:-1]
            i += 1
            if i < len(lines):
                if lines[i] == 'msgstr ""':
                    out.append('msgstr "' + value + '"')
                    i += 1
                    filled += 1
                elif lines[i].strip() == '' and (i + 1 >= len(lines) or lines[i + 1].startswith('#. module')):
                    # msgid followed by blank then next entry: insert msgstr
                    out.append('msgstr "' + value + '"')
                    filled += 1
    i += 1

PO.write_text("\n".join(out), encoding="utf-8")
print(f"Filled {filled} empty msgstr in es.po")
