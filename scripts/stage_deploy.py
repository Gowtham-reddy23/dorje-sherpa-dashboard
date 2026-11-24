#!/usr/bin/env python3
"""After `pnpm build`: copies what Vercel should serve into vercel-deploy/ (git-ignored):
   out/*  (static dashboard, incl. the ENCRYPTED data.enc.json)  +  vercel.json  +  api/*.mjs (Ask Dorje functions).
Then deploy with the Vercel CLI (prebuilt static files, no build step on Vercel):
   cd vercel-deploy && vercel deploy --prod      (first time: link/create a project, Framework = Other)
Safety checks: no plain data/dashboard.json, no .env, and the DASH_PASSCODE value appears in no deployed file."""
import os, shutil, sys
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT, API, DST = os.path.join(H, 'out'), os.path.join(H, 'api'), os.path.join(H, 'vercel-deploy')
if not os.path.isdir(OUT) or not os.path.exists(os.path.join(API, 'chat.mjs')): sys.exit('Run `pnpm build` first (out/ and api/chat.mjs missing).')
link = os.path.join(DST, '.vercel'); keep = None
if os.path.isdir(link): keep = os.path.join(H, '.vercel-link-tmp'); shutil.rmtree(keep, ignore_errors=True); shutil.move(link, keep)
shutil.rmtree(DST, ignore_errors=True); shutil.copytree(OUT, DST)
shutil.copy(os.path.join(H, 'vercel.json'), DST); os.makedirs(os.path.join(DST, 'api'))
for f in os.listdir(API):
    if f.endswith('.mjs'): shutil.copy(os.path.join(API, f), os.path.join(DST, 'api', f))
if keep: shutil.move(keep, link)   # keep the Vercel project link between deploys
pw = os.environ.get('DASH_PASSCODE', '').strip()
if not pw and os.path.exists(os.path.join(H, '.env')):
    for l in open(os.path.join(H, '.env')):
        if l.strip().startswith('DASH_PASSCODE='): pw = l.split('=', 1)[1].strip().strip('"\'')
n = 0
for root, dirs, files in os.walk(DST):
    dirs[:] = [d for d in dirs if d != '.vercel']
    for f in files:
        p = os.path.join(root, f); rel = os.path.relpath(p, DST); n += 1
        assert f not in ('dashboard.json', '.env') and not f.startswith('.env'), 'refusing to deploy ' + rel
        if pw and len(pw) >= 6: assert pw.encode() not in open(p, 'rb').read(), 'passcode found in ' + rel
print(n, 'files staged in vercel-deploy/. Next: cd vercel-deploy && vercel deploy --prod')
