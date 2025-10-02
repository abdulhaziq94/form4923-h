#!/usr/bin/env python3
import cgitb; cgitb.enable()
import os, html, urllib.parse
try:
    from pypdf import PdfReader
except:
    from PyPDF2 import PdfReader

print("Content-Type: text/html; charset=utf-8")
print()

qs = os.environ.get("QUERY_STRING", "")
page = int(urllib.parse.parse_qs(qs).get("page", [2])[0])

ROWS, CELLS, TOL = 27, 7, 4.0
src = "/var/www/pyapp/forms/4923-H_2025-2026.pdf"

r = PdfReader(src)
pi = page - 1
if pi < 0 or pi >= len(r.pages):
    pi = 1
pg = r.pages[pi]

ann = pg.get("/Annots")
if hasattr(ann, "get_object"):
    ann = ann.get_object()
if ann is None:
    ann = []
if not isinstance(ann, list):
    ann = [ann]

cells = []
for a in ann:
    o = a.get_object()
    if o.get("/Subtype") != "/Widget":
        continue
    if o.get("/FT") not in ("/Tx", "/Ch"):
        continue  # include text and choice (State) widgets
    rect = o.get("/Rect")
    if hasattr(rect, "get_object"):
        rect = rect.get_object()
    x1, y1, x2, y2 = [float(x) for x in rect]
    x = (x1 + x2) / 2.0
    y = (y1 + y2) / 2.0

    v = o.get("/V")
    val = ""
    if v is not None:
        try:
            if hasattr(v, "get_object"):
                v = v.get_object()
            if isinstance(v, list):  # multi-select dropdowns (unlikely here)
                parts = []
                for it in v:
                    if hasattr(it, "get_object"):
                        it = it.get_object()
                    s = str(it)
                    parts.append(s[1:] if s.startswith("/") else s)
                val = ",".join(parts)
            else:
                s = str(v)
                val = s[1:] if s.startswith("/") else s
        except:
            try:
                val = str(v)
            except:
                val = ""

    cells.append((y, x, val))

# sort visual order: top->bottom (by y descending), then left->right (x ascending)
cells.sort(key=lambda t: (-t[0], t[1]))

# group into rows with tolerance on Y
rows = []
for y, x, val in cells:
    placed = False
    for row in rows:
        if abs(row["y"] - y) <= TOL and len(row["cells"]) < CELLS:
            row["cells"].append((x, val))
            placed = True
            break
    if not placed:
        rows.append({"y": y, "cells": [(x, val)]})

for row in rows:
    row["cells"].sort(key=lambda z: z[0])

# pad / clamp to 27 rows × 7 cells
if len(rows) < ROWS:
    rows += [{"y": -1e9, "cells": []} for _ in range(ROWS - len(rows))]
rows = rows[:ROWS]

print(f"""<!doctype html>
<html><head><meta name=viewport content="width=device-width, initial-scale=1">
<title>Fields — page {page}</title>
<style>
body{{font-family:system-ui,Arial,sans-serif;margin:10px}}
.row{{display:flex;gap:6px;margin:3px 0;border-bottom:1px dashed #ccc;padding:4px 0}}
.cell{{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;border:1px solid #eee;padding:4px}}
.tiny{{opacity:.6;font-size:.8em;display:block}}
.hdr{{margin-bottom:8px}}
</style></head><body>
<div class=hdr>PDF: {html.escape(src)} — Page {page}. <b>27 rows</b> × 7 fields inline. Rows 1–2 are informational. Cells labeled Rn(k).</div>
""")
for i, row in enumerate(rows, 1):
    print('<div class="row">')
    cs = row["cells"] + [(0, "")] * (CELLS - len(row["cells"]))
    for j, (_, val) in enumerate(cs[:CELLS], 1):
        txt = html.escape(val) if val else ""
        print(f'<div class="cell"><span class="tiny">R{i}({j})</span>{txt}</div>')
    print("</div>")
print("</body></html>")
