"""Tiny env loader for the refresh scripts. Reads ../.env (repo root) if present, then the real environment.
Secrets live ONLY in .env (git-ignored) or your shell. Never hard-code them in these scripts."""
import os
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def _load():
    p = os.path.join(_ROOT, '.env')
    if not os.path.exists(p): return
    for line in open(p):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
_load()
def env(name, default=None):
    v = os.environ.get(name, '').strip()
    return v or default
def need(name):
    v = env(name)
    if not v:
        raise SystemExit(f'Missing {name}. Add it to .env (see .env.example and docs/SETUP.md).')
    return v
