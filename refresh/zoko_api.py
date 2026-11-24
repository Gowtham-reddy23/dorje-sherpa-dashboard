"""Read-only Zoko client: GET only. Key from the ZOKO_API_KEY env var (see .env.example), never printed."""
import json, os, time, urllib.request, urllib.parse, urllib.error
from _env import need
KEY=need('ZOKO_API_KEY')
BASE='https://chat.zoko.io/v2'
def get(path, params=None, retries=3):
    url=BASE+path+('?'+urllib.parse.urlencode(params) if params else '')
    for i in range(retries):
        req=urllib.request.Request(url, method='GET', headers={'apikey':KEY,'accept':'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=60) as r: return r.status, json.loads(r.read() or b'null')
        except urllib.error.HTTPError as e:
            body=e.read().decode(errors='replace').replace(KEY,'***')[:300]
            if e.code==429: time.sleep(5*(i+1)); continue
            return e.code, body
        except Exception as e:
            if i==retries-1: return 0, str(e).replace(KEY,'***')[:200]
            time.sleep(1)
    return 429, 'rate limited'
