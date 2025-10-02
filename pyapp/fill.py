#!/usr/bin/env python3
import os, sys, urllib.parse, subprocess, datetime, shutil, stat, time

print("Content-Type: text/html; charset=utf-8")
print()

def qs_get(qs, k, d=""):
    return (qs.get(k,[d])[0] or "").strip()

def normalize_date(s):
    s=s.strip()
    if not s:
        # default to today in America/Chicago; server tz is fine for now
        dt=datetime.date.today()
        return dt.strftime("%m%d%Y")
    if len(s)==10 and s[4:5]=="-" and s[7:8]=="-":
        # yyyy-mm-dd -> mmddyyyy
        y,m,d = s.split("-")
        return f"{m}{d}{y}"
    if len(s)==8 and s.isdigit():
        return s
    # last resort: try to parse
    try:
        dt=datetime.datetime.fromisoformat(s).date()
        return dt.strftime("%m%d%Y")
    except:
        return s  # let downstream error out if bad

qs = urllib.parse.parse_qs(os.environ.get("QUERY_STRING",""), keep_blank_values=True)

car   = qs_get(qs,"car","dodge")
mode  = qs_get(qs,"mode","preset")
date  = normalize_date(qs_get(qs,"date"))
name  = qs_get(qs,"name")
addr  = qs_get(qs,"addr")
city  = qs_get(qs,"city")
state = qs_get(qs,"state")
zipc  = qs_get(qs,"zip")
gal   = qs_get(qs,"gal")

if mode=="preset":
    name  = "Default Station"
    addr  = "123 Main St"
    city  = "Anytown"
    state = "MO"
    zipc  = "00000"

# minimal validation so we don't call the filler with blanks
missing = []
if car not in ("dodge","buick"): missing.append("car")
if len(date)!=8 or not date.isdigit(): missing.append("date (mmddyyyy)")
for k,v in (("name",name),("addr",addr),("city",city),("state",state),("zip",zipc),("gal",gal)):
    if not v: missing.append(k)
if missing:
    sys.stdout.write('<h3 style="margin:16px;color:#a00">ERROR</h3>')
    sys.stdout.write('<pre style="color:#a00">Missing/invalid: '+", ".join(missing)+'</pre>')
    sys.exit(0)

cmd = [
    "/usr/local/bin/pdf_fill_safe",
    "--car", car,
    "--date", date,
    "--name", name,
    "--addr", addr,
    "--city", city,
    "--state", state,
    "--zip",  zipc,
    "--gal",  gal,
]

ok=False
try:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    out = (res.stdout or "").strip()
    err = (res.stderr or "").strip()
    ok = (res.returncode==0) and out.startswith("OK")
except Exception as e:
    out=""; err=str(e)

if ok:
    # publish once more (cheap) to ensure latest file is served
    SRC="/var/www/pyapp/forms/4923-H_2025-2026.pdf"
    PUB="/var/www/html/forms/4923-H_2025-2026.pdf"
    try:
        os.makedirs(os.path.dirname(PUB), exist_ok=True)
        shutil.copyfile(SRC, PUB)
        os.chmod(PUB, stat.S_IRUSR|stat.S_IWUSR|stat.S_IRGRP|stat.S_IROTH)
        now=time.time(); os.utime(PUB,(now,now))
    except: pass
    sys.stdout.write('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    sys.stdout.write('<h3 style="margin:16px;color:#060">OK</h3>')
else:
    sys.stdout.write('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    sys.stdout.write('<h3 style="margin:16px;color:#a00">ERROR</h3>')
    if out:
        sys.stdout.write('<pre style="white-space:pre-wrap;color:#a00">'+urllib.parse.quote(out, safe=":/?&=+%@,.- _\n").replace("%0A","\n")+'</pre>')
    if err:
        sys.stdout.write('<pre style="white-space:pre-wrap;color:#a00">'+urllib.parse.quote(err, safe=":/?&=+%@,.- _\n").replace("%0A","\n")+'</pre>')
