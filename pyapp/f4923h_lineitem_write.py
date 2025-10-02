import fitz,os
SRC="/var/www/pyapp/forms/4923-H_2025-2026.pdf"
d=fitz.open(SRC);pg=d[1]
ws=[w for w in pg.widgets() if hasattr(w,"field_value")]
cells=[(((w.rect.y0+w.rect.y1)/2),((w.rect.x0+w.rect.x1)/2),w) for w in ws];cells.sort(key=lambda t:(t[0],t[1]))
rows=[];tol=4
for y,x,w in cells:
    if rows and abs(rows[-1][0]-y)<=tol and len(rows[-1][1])<7: rows[-1][1].append((x,w))
    else: rows.append((y,[(x,w)]))
_,cs=rows[18]
cs=[w for _,w in sorted(cs,key=lambda z:z[0])[:7]]
vals=["1","2","3","4","5","6","7"]
for w,v in zip(cs,vals): w.field_value=v; w.update()
tmp=SRC+".new"; d.save(tmp,garbage=3,deflate=True); d.close(); os.replace(tmp,SRC)
print("OK p2 R19 1..7")
