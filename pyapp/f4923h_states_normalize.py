import fitz, re, os
SRC="/var/www/pyapp/forms/4923-H_2025-2026.pdf"

def infer_state(zipc, city, addr):
    z=(zipc or "").strip()
    if re.match(r"^6[345]\d{3}$", z): return "MO"
    if re.match(r"^66\d{3}$", z): return "KS"
    if re.match(r"^7[34]\d{3}$", z): return "OK"
    if "Anytown" in (city or "") or " MO" in (addr or ""): return "MO"
    return ""

doc=fitz.open(SRC); pg=doc[1]  # page 2
ws=list(pg.widgets())
cells=[(((w.rect.y0+w.rect.y1)/2), ((w.rect.x0+w.rect.x1)/2), w) for w in ws]
cells.sort(key=lambda t:(t[0],t[1]))

rows=[]; tol=4
for y,x,w in cells:
    if rows and abs(rows[-1][0]-y)<=tol and len(rows[-1][1])<7:
        rows[-1][1].append((x,w))
    else:
        rows.append((y,[(x,w)]))

changed=False
for i in range(2, min(27,len(rows))):   # R3..R27
    _, cols = rows[i]
    cols = [w for _,w in sorted(cols, key=lambda z:z[0])[:7]]
    if len(cols) < 7: continue
    state, zipc = cols[4], cols[5]
    sv = (getattr(state, "field_value", "") or "").strip()
    if not sv:
        city = getattr(cols[3], "field_value", "") or ""
        addr = getattr(cols[2], "field_value", "") or ""
        s = infer_state(getattr(zipc,"field_value","") or "", city, addr) or ""
        if s:
            state.field_value = s
            state.update()
            changed=True

if changed:
    TMP=SRC+".new"; doc.save(TMP, garbage=3, deflate=True); doc.close(); os.replace(TMP, SRC); print("OK fixed missing states on p2")
else:
    doc.close(); print("No changes needed on p2")
