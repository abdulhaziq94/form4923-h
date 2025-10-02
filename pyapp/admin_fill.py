#!/usr/bin/env python3
import os, sys, html, urllib.parse

print("Content-Type: text/html; charset=utf-8")
print()

# read query string or POST body into dict q
if os.environ.get("REQUEST_METHOD","GET") == "POST":
    ln = int(os.environ.get("CONTENT_LENGTH","0") or 0)
    raw = sys.stdin.read(ln)
    q = urllib.parse.parse_qs(raw, keep_blank_values=True)
else:
    q = urllib.parse.parse_qs(os.environ.get("QUERY_STRING",""), keep_blank_values=True)

def g(k,d=""): return (q.get(k,[d])[0] or "").strip()

SRC = "/var/www/pyapp/forms/4923-H_2025-2026.pdf"

mode = g("mode","view")          # view | apply
car  = g("car","dodge")          # dodge -> page 2 ; buick -> page 5
page_index = 1 if car=="dodge" else 4
row  = int(g("row","3"))         # rows 3..27 only
vals = [g(f"c{i}","") for i in range(1,8)]

def read_rows(page_index):
    # read current values via PyPDF (same as viewer ordering)
    try:
        from pypdf import PdfReader
    except:
        from PyPDF2 import PdfReader
    r = PdfReader(SRC)
    pg = r.pages[page_index]
    ann = pg.get("/Annots")
    if hasattr(ann,"get_object"): ann = ann.get_object()
    if ann is None: ann=[]
    if not isinstance(ann,list): ann=[ann]
    cells=[]
    for a in ann:
        o=a.get_object()
        if o.get("/Subtype")!="/Widget": continue
        if o.get("/FT") not in ("/Tx","/Ch"): continue
        rect=o.get("/Rect")
        if hasattr(rect,"get_object"): rect=rect.get_object()
        x1,y1,x2,y2=[float(v) for v in rect]
        x=(x1+x2)/2.0; y=(y1+y2)/2.0
        v=o.get("/V"); 
        if hasattr(v,"get_object"): v=v.get_object()
        if v is None: s=""
        else:
            try: s=str(v)
            except: s=""
        cells.append((y,x,s))
    cells.sort(key=lambda t:(-t[0], t[1]))
    rows=[]; tol=4.0
    for y,x,s in cells:
        if rows and abs(rows[-1][0]-y)<=tol and len(rows[-1][1])<7:
            rows[-1][1].append((x,s))
        else:
            rows.append((y,[(x,s)]))
    # normalize left->right 7 cells
    rows=[(y, [s for _,s in sorted(cols,key=lambda z:z[0])[:7]]) for y,cols in rows]
    return rows

def write_row(page_index, row_index_1based, new_vals):
    import fitz, os
    # get target Y using the viewer-style rows from pypdf
    try:
        from pypdf import PdfReader
    except:
        from PyPDF2 import PdfReader
    r=PdfReader(SRC)
    pg=r.pages[page_index]
    ann=pg.get("/Annots")
    if hasattr(ann,"get_object"): ann=ann.get_object()
    if ann is None: ann=[]
    if not isinstance(ann,list): ann=[ann]
    cells=[]
    for a in ann:
        o=a.get_object()
        if o.get("/Subtype")!="/Widget": continue
        if o.get("/FT") not in ("/Tx","/Ch"): continue
        rect=o.get("/Rect")
        if hasattr(rect,"get_object"): rect=rect.get_object()
        x1,y1,x2,y2=[float(v) for v in rect]
        cells.append(((y1+y2)/2.0, (x1+x2)/2.0))
    cells.sort(key=lambda t:(-t[0], t[1]))
    rows=[]; tol=4.0
    for y,x in cells:
        if rows and abs(rows[-1][0]-y)<=tol and len(rows[-1][1])<7:
            rows[-1][1].append(x)
        else:
            rows.append((y,[x]))
    if row_index_1based<1 or row_index_1based>len(rows): 
        return "Bad row index"
    target_y = rows[row_index_1based-1][0]
    # write via MuPDF
    d=fitz.open(SRC); pgm=d[page_index]
    pts=[]
    for w in pgm.widgets():
        if not hasattr(w,"field_value"): continue
        rc=w.rect; y=(rc.y0+rc.y1)/2.0; x=(rc.x0+rc.x1)/2.0
        if abs(y-target_y)<=tol: pts.append((x,w))
    pts.sort(key=lambda z:z[0]); pts=pts[:7]
    # fill / clear (typed)
    for (i,(x,w)) in enumerate(pts):
        v = new_vals[i] if i<len(new_vals) else ""
        w.field_value = v
        w.update()
    tmp=SRC+".new"; d.save(tmp,garbage=3,deflate=True); d.close(); os.replace(tmp,SRC)
    return "OK"

# apply if requested (only rows 3..27)
msg=""
if mode=="apply":
    if row<3 or row>27:
        msg="ERROR"
    else:
        msg = write_row(page_index, row, vals)

# always show form with current values (updated if OK)
rows = read_rows(page_index)
safe_ok = (msg=="OK")
if safe_ok:
    sys.stdout.write('<h3 style="margin:8px 0;color:#060">OK</h3>')
elif msg.startswith("ERROR"):
    sys.stdout.write('<h3 style="margin:8px 0;color:#a00">ERROR</h3>')

# read current row values (default to blanks if missing)
cur = rows[row-1][1] if 0 <= row-1 < len(rows) else [""]*7

# HTML
def opt(val,txt,cur): 
    return f'<option value="{val}"{" selected" if cur==val else ""}>{txt}</option>'

sys.stdout.write('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
sys.stdout.write('<h2 style="margin:8px 0 12px">Admin Fill (rows 3–27 only)</h2>')
sys.stdout.write('<form method="post" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;max-width:820px">')

# car
sys.stdout.write('<label>Car<select name="car">')
sys.stdout.write(opt("dodge","2016 Dodge DART SXT","dodge" if car=="dodge" else ""))
sys.stdout.write(opt("buick","2011 Buick ENCLAVE 2CXL AWD","buick" if car=="buick" else ""))
sys.stdout.write('</select></label>')

# row
sys.stdout.write('<label>Row<select name="row">')
for rno in range(3,28):
    sys.stdout.write(opt(str(rno), f"R{rno}", str(row)))
sys.stdout.write('</select></label>')

# 7 cells
for i in range(7):
    v = html.escape(cur[i] if i<len(cur) else "")
    sys.stdout.write(f'<label>R{row}({i+1})<input name="c{i+1}" value="{v}"></label>')

sys.stdout.write('<input type="hidden" name="mode" value="apply">')
sys.stdout.write('<div style="grid-column:1/-1"><button type="submit">Apply</button></div>')
sys.stdout.write('</form>')
