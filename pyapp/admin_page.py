#!/usr/bin/env python3
import os, sys, html, urllib.parse, shutil, stat, time, traceback
print("Content-Type: text/html; charset=utf-8"); print()

SRC="/var/www/pyapp/forms/4923-H_2025-2026.pdf"
PUB="/var/www/html/forms/4923-H_2025-2026.pdf"

def parse():
    if os.environ.get("REQUEST_METHOD","GET")=="POST":
        n=int(os.environ.get("CONTENT_LENGTH","0") or 0)
        return urllib.parse.parse_qs(sys.stdin.read(n), keep_blank_values=True)
    return urllib.parse.parse_qs(os.environ.get("QUERY_STRING",""), keep_blank_values=True)

def open_reader():
    try:
        from pypdf import PdfReader
    except:
        from PyPDF2 import PdfReader
    return PdfReader(SRC)

def pypdf_grid_from_reader(reader, pindex):
    pg = reader.pages[pindex]
    ann = pg.get("/Annots")
    if hasattr(ann,"get_object"): ann = ann.get_object()
    if ann is None: ann=[]
    if not isinstance(ann,list): ann=[ann]
    items=[]
    for a in ann:
        o=a.get_object()
        if o.get("/Subtype")!="/Widget": continue
        if o.get("/FT") not in ("/Tx","/Ch"): continue
        rc=o.get("/Rect")
        if hasattr(rc,"get_object"): rc=rc.get_object()
        x1,y1,x2,y2=[float(v) for v in rc]
        x=(x1+x2)/2.0; y=(y1+y2)/2.0
        v=o.get("/V")
        if hasattr(v,"get_object"): v=v.get_object()
        s="" if v is None else f"{v}".lstrip("/")
        items.append((y,x,s,o))
    items.sort(key=lambda t:(-t[0], t[1]))
    tol=4.0; rows=[]
    for y,x,s,o in items:
        if rows and abs(rows[-1][0]-y)<=tol and len(rows[-1][1])<7:
            rows[-1][1].append((x,s,o))
        else:
            rows.append((y,[(x,s,o)]))
    grid=[(y, sorted(cols, key=lambda z:z[0])[:7]) for y,cols in rows]
    return grid

def apply_page(pindex, form):
    from pypdf import PdfWriter
    from pypdf.generic import NameObject, TextStringObject, BooleanObject
    r=open_reader()
    grid=pypdf_grid_from_reader(r, pindex)
    changed=0
    for r_idx,(y, cols) in enumerate(grid, start=1):
        if r_idx<3: continue
        for k,(x,cur,annot) in enumerate(cols, start=1):
            key=f"r{r_idx}_{k}"
            if key not in form: continue
            new=(form[key][0] or "")
            if new==cur: continue
            ft=annot.get("/FT")
            if ft=="/Tx":
                annot.update({NameObject("/V"): TextStringObject(new)})
                ap=annot.get("/AP"); 
                if ap and hasattr(ap,"get_object"): ap.get_object().clear()
                changed+=1
            elif ft=="/Ch":
                # dropdown: set /V and /DV to string matching an option
                opt=annot.get("/Opt")
                if hasattr(opt,"get_object"): opt=opt.get_object()
                options=[]
                if isinstance(opt,list):
                    for it in opt:
                        if hasattr(it,"get_object"): it=it.get_object()
                        if isinstance(it,list) and len(it)>=1:
                            exp=f"{it[0]}"; disp=f"{(it[1] if len(it)>=2 else it[0])}"
                            options.append((exp,disp))
                        else:
                            s=f"{it}"; options.append((s,s))
                target=None
                if new:
                    for exp,disp in options:
                        if new.lower()==exp.lower() or new.lower()==disp.lower():
                            target=exp or disp; break
                if not target and new: target=new
                annot.update({
                    NameObject("/V"): TextStringObject(target),
                    NameObject("/DV"): TextStringObject(target),
                })
                ap=annot.get("/AP")
                if ap and hasattr(ap,"get_object"): ap.get_object().clear()
                changed+=1
    # NeedAppearances to re-render
    root=r.trailer["/Root"]; acro=root.get("/AcroForm")
    if acro and hasattr(acro,"get_object"):
        acro=acro.get_object()
        acro.update({NameObject("/NeedAppearances"): BooleanObject(True)})

    w=PdfWriter(); w.clone_reader_document_root(r)
    tmp=SRC+".new"
    with open(tmp,"wb") as f: w.write(f)
    os.replace(tmp,SRC)

    os.makedirs(os.path.dirname(PUB), exist_ok=True)
    shutil.copyfile(SRC, PUB)
    os.chmod(PUB, stat.S_IRUSR|stat.S_IWUSR|stat.S_IRGRP|stat.S_IROTH)
    now=time.time(); os.utime(PUB,(now,now))
    return changed

# -------- controller / UI --------
q=parse()
page=int((q.get("p",["2"])[0] or "2")); page=max(2, min(11, page)); pidx=page-1

msg=""; changed=0
try:
    if (q.get("mode",["view"])[0] or "view")=="upload":
        changed=apply_page(pidx, q); msg="OK"
except Exception as e:
    msg="ERROR"
    sys.stdout.write('<h3 style="margin:10px 0;color:#a00">ERROR</h3>')
    sys.stdout.write('<pre style="white-space:pre-wrap;color:#a00">')
    sys.stdout.write(html.escape(f"{e}\n\n"+traceback.format_exc()))
    sys.stdout.write('</pre>')

r=open_reader()
vals=[(y,[s for _,s,_ in cols]) for (y,cols) in pypdf_grid_from_reader(r, pidx)]

if msg=="OK":
    sys.stdout.write(f'<h3 style="margin:10px 0;color:#060">OK</h3><div style="color:#060;margin:-6px 0 8px">changed: {changed}</div>')

sys.stdout.write('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
sys.stdout.write('<h2 style="margin:8px 0 12px">Admin Page Editor</h2>')

# GET form for page change (instant)
sys.stdout.write('<form method="get" style="margin:0 0 10px 0;display:inline-block">')
sys.stdout.write('<input type="hidden" name="mode" value="view">')
sys.stdout.write('<label>Page <select name="p" onchange="this.form.submit()">')
for pp in range(2,12):
    sel=" selected" if pp==page else ""
    sys.stdout.write(f'<option value="{pp}"{sel}>{pp}</option>')
sys.stdout.write('</select></label>')
sys.stdout.write('</form>')

# POST form for edits (keeps current page)
sys.stdout.write('<form method="post">')
sys.stdout.write('<input type="hidden" name="mode" value="upload">')
sys.stdout.write(f'<input type="hidden" name="p" value="{page}">')

sys.stdout.write('<div style="margin:10px 0;overflow:auto;max-width:100%"><table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse;min-width:760px">')
sys.stdout.write('<tr><th>Row</th>' + ''.join(f'<th>C{k}</th>' for k in range(1,8)) + '</tr>')
for rno in range(1,28):
    cur = vals[rno-1][1] if rno-1<len(vals) else [""]*7
    ro = ' readonly' if rno<=2 else ''
    sys.stdout.write(f'<tr><td>R{rno}</td>')
    for k in range(1,8):
        v=html.escape(cur[k-1] if k-1<len(cur) else "")
        sys.stdout.write(f'<td><input name="r{rno}_{k}" value="{v}"{ro}></td>')
    sys.stdout.write('</tr>')
sys.stdout.write('</table></div><div style="margin:10px 0"><button type="submit">Upload</button></div></form>')
