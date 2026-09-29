import json, os, time, urllib.request, concurrent.futures, sys

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "https://www.nmc.cn/"}

def load_stations():
    out = {}
    for f, prov in [("data/ajs.json", "江苏"), ("data/azj.json", "浙江"), ("data/aah.json", "安徽"), ("data/afj.json", "福建")]:
        for s in json.load(open(f, encoding="utf-8")):
            out[s["code"]] = {"code": s["code"], "city": s["city"], "url": s["url"], "prov": prov}
    return out

def fetch(code):
    path = f"data/wx_{code}.json"
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return code, "cached"
    for attempt in range(3):
        try:
            req = urllib.request.Request(f"https://www.nmc.cn/rest/weather?stationid={code}", headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                data = r.read().decode("utf-8")
            j = json.loads(data)
            if j.get("code") == 0 and j.get("data", {}).get("predict", {}).get("detail"):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(data)
                return code, "ok"
            return code, "bad-payload"
        except Exception as e:
            if attempt == 2:
                return code, f"fail:{type(e).__name__}"
            time.sleep(1.5)

stations = load_stations()
os.makedirs("data", exist_ok=True)
print(f"total {len(stations)} stations", flush=True)
results = {}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    for code, status in ex.map(fetch, stations):
        results[code] = status
        if not status.startswith(("ok", "cached")):
            print(f"  {stations[code]['prov']} {stations[code]['city']} -> {status}", flush=True)
bad = [c for c, s in results.items() if not s.startswith(("ok", "cached"))]
print(f"done: {len(results) - len(bad)} ok, {len(bad)} failed")
sys.exit(1 if bad else 0)
