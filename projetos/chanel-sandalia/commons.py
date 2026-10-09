import sys, json, urllib.request, urllib.parse, time
UA = {"User-Agent": "EditorIA-DEEP/1.0 (video editing helper; contact: gabrielaroucaeditor@gmail.com)"}
def api(params):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({**params, "format": "json"})
    for k in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
        except Exception as e:
            time.sleep(2 + 3 * k)
    raise SystemExit("falhou: " + url)
def search(q, n=8):
    r = api({"action": "query", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": n,
             "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime", "iiurlwidth": 1600})
    out = []
    for p in (r.get("query", {}).get("pages", {}) or {}).values():
        ii = p["imageinfo"][0]; m = ii.get("extmetadata", {})
        out.append({"title": p["title"], "w": ii["width"], "h": ii["height"], "thumb": ii.get("thumburl"), "url": ii["url"],
                    "lic": m.get("LicenseShortName", {}).get("value"), "artist": (m.get("Artist", {}).get("value") or "")[:60],
                    "desc": (m.get("ImageDescription", {}).get("value") or "")[:80]})
    return sorted(out, key=lambda x: -x["w"] * x["h"])
if __name__ == "__main__":
    for q in sys.argv[1:]:
        print("##", q)
        for o in search(q): print(f"  {o['w']}x{o['h']} {o['lic']} | {o['title']} | {o['artist']}")
        time.sleep(1)
