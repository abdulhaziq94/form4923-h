try:
    from pypdf import PdfReader,PdfWriter
    from pypdf.generic import NameObject,BooleanObject
except:
    from PyPDF2 import PdfReader,PdfWriter
    from PyPDF2.generic import NameObject,BooleanObject

src="/var/www/pyapp/forms/4923-H_2025-2026.pdf"
r=PdfReader(src);w=PdfWriter()
for p in r.pages:w.add_page(p)
acro=r.trailer["/Root"].get("/AcroForm")
if acro:
    w._root_object[NameObject("/AcroForm")]=acro
    w._root_object["/AcroForm"].get_object().update({NameObject("/NeedAppearances"):BooleanObject(True)})

pg=r.pages[1]
ann=pg.get("/Annots");ann=ann.get_object() if hasattr(ann,"get_object") else ann
ann=[] if ann is None else ([ann] if not isinstance(ann,list) else ann)

cells=[]
for a in ann:
    o=a.get_object()
    if o.get("/Subtype")!="/Widget" or o.get("/FT")!="/Tx": continue
    x1,y1,x2,y2=[float(x) for x in o.get("/Rect")]
    cells.append((-(y1+y2)/2,(x1+x2)/2,o.get("/T","")))

cells.sort()
rows=[];tol=4.0
for y,x,t in cells:
    if rows and abs(rows[-1][0]-y)<=tol and len(rows[-1][1])<7: rows[-1][1].append(t)
    else: rows.append((y,[t]))

r19=rows[18][1][:6]  # R19 (R1=rows[0], R2=rows[1], …)
vals=["09222025","Default Station","123 Main St","Anytown","00000","9.99"]
w.update_page_form_field_values(w.pages[1],{r19[i]:vals[i] for i in range(6)})

out=src+".new";f=open(out,"wb");w.write(f);f.close()
import os;os.replace(out,src)
print("OK page2 R19")
