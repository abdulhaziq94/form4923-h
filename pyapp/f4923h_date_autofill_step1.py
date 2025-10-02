try:
    from pypdf import PdfReader,PdfWriter
    from pypdf.generic import NameObject,BooleanObject
except:
    from PyPDF2 import PdfReader,PdfWriter
    from PyPDF2.generic import NameObject,BooleanObject
from datetime import datetime
src="/var/www/pyapp/forms/4923-H_2025-2026.pdf"
r=PdfReader(src);w=PdfWriter()
for p in r.pages:w.add_page(p)
root=r.trailer["/Root"]
acro=root.get("/AcroForm")
if acro:
    w._root_object[NameObject("/AcroForm")]=acro
    w._root_object["/AcroForm"].get_object().update({NameObject("/NeedAppearances"):BooleanObject(True)})
pg=r.pages[1]
ann=pg.get("/Annots")
if hasattr(ann,"get_object"):ann=ann.get_object()
if ann is None:raise SystemExit("no fields on page 2")
if not isinstance(ann,list):ann=[ann]
c=[]
for a in ann:
    o=a.get_object()
    if o.get("/Subtype")!="/Widget":continue
    if o.get("/FT")!="/Tx":continue
    if o.get("/V") is not None:continue
    rect=o.get("/Rect");x=(rect[0]+rect[2])/2
    if x<120:c.append((float(rect[1]),o.get("/T")))
if not c:raise SystemExit("no empty date cell on page 2")
t=max(c,key=lambda z:z[0])[1]
w.update_page_form_field_values(w.pages[1],{t:datetime.now().strftime("%m%d%Y")})
f=open("/var/www/pyapp/output/4923-H_filled_step1.pdf","wb");w.write(f);f.close()
print("OK",t)
