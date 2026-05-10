import requests, re, json, gzip, base64, io, os, sys

sites = [
"https://raw.githubusercontent.com/theriturajps/proxy-list/main/proxies.txt",
 "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
 "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/https.txt",
 "https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/main/http.txt",
 "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks5.txt",
 "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Socks4.txt",
 "https://raw.githubusercontent.com/r00tee/Proxy-List/main/Https.txt",
 "https://raw.githubusercontent.com/thenasty1337/free-proxy-list/main/data/latest/types/http/proxies.txt",
 "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
 "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt",
 "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/generated/http_proxies.txt",
 "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
 "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
 "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
 "https://raw.githubusercontent.com/mmpx12/proxy-list/refs/heads/master/http.txt",
 "https://raw.githubusercontent.com/mmpx12/proxy-list/refs/heads/master/socks5.txt",
 "https://raw.githubusercontent.com/mmpx12/proxy-list/refs/heads/master/tor-exit-nodes.txt",
 "https://raw.githubusercontent.com/mmpx12/proxy-list/refs/heads/master/proxies.txt",
 "https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/protocols/http/data.txt",
 "https://proxylist.geonode.com/api/proxy-list?protocols=socks5%2Chttp&limit=500&page=1&sort_by=lastChecked&sort_type=desc",
 "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text",
 "https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/countries/IR/data.txt",
 "https://raw.githubusercontent.com/proxifly/free-proxy-list/refs/heads/main/proxies/all/data.txt",
 "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt",
 "https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/http.txt",
 "https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/socks4.txt",
 "https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/socks5.txt",
 "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/http.txt",
 "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/https.txt",
 "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/socks4.txt",
 "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/refs/heads/master/socks5.txt",
 "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/refs/heads/main/All_proxies.txt",
 "https://raw.githubusercontent.com/ebrasha/abdal-proxy-hub/refs/heads/main/http-proxy-list-by-EbraSha.txt",
 "https://raw.githubusercontent.com/ebrasha/abdal-proxy-hub/refs/heads/main/https-proxy-list-by-EbraSha.txt",
 "https://raw.githubusercontent.com/ebrasha/abdal-proxy-hub/refs/heads/main/socks4-proxy-list-by-EbraSha.txt",
 "https://raw.githubusercontent.com/ebrasha/abdal-proxy-hub/refs/heads/main/socks5-proxy-list-by-EbraSha.txt",
 "https://raw.githubusercontent.com/VPSLabCloud/VPSLab-Free-Proxy-List/refs/heads/main/all_proxies.txt",
 "https://raw.githubusercontent.com/VPSLabCloud/VPSLab-Free-Proxy-List/refs/heads/main/all_elite.txt",
 "https://raw.githubusercontent.com/newbie-learn-coding/free-proxy-list/refs/heads/main/proxies/all/data.txt",
 "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/refs/heads/main/proxies/all.txt",
 "https://raw.githubusercontent.com/itsanwar/proxy-scraper-ak/refs/heads/main/sproxies/ALL.txt",
 "https://raw.githubusercontent.com/gitrecon1455/fresh-proxy-list/refs/heads/main/proxylist.txt",
 "https://raw.githubusercontent.com/anutmagang/Free-HighQuality-Proxy-Socks/refs/heads/main/results/all.txt",
 "https://raw.githubusercontent.com/MrMarble/proxy-list/refs/heads/main/all.txt",
 "https://raw.githubusercontent.com/iplocate/free-proxy-list/refs/heads/main/all-proxies.txt",
 "https://raw.githubusercontent.com/watchttvv/free-proxy-list/refs/heads/main/proxy.txt",
 "https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/all.txt",
 "https://raw.githubusercontent.com/Pxys-io/DailyProxyList/refs/heads/master/working_proxies.txt",
 "https://raw.githubusercontent.com/officialputuid/ProxyForEveryone/refs/heads/main/xResults/Proxies.txt",
 "https://raw.githubusercontent.com/Bes-js/public-proxy-list/refs/heads/main/proxies.txt",
 "https://raw.githubusercontent.com/proxygenerator1/ProxyGenerator/refs/heads/main/ALL/ALL.txt",
 "https://raw.githubusercontent.com/Seeh-Saah/awesome-free-proxy-list/refs/heads/main/proxies/all.txt",
 "https://raw.githubusercontent.com/TopChina/proxy-list/refs/heads/main/README.md",
 "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/refs/heads/main/proxies/http.txt",
 "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/refs/heads/main/proxies/socks4.txt",
 "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/refs/heads/main/proxies/socks5.txt",
 "https://raw.githubusercontent.com/andigwandi/free-proxy/refs/heads/main/proxy_list.txt",
 "https://raw.githubusercontent.com/theriturajps/proxy-list/refs/heads/main/proxies.txt"
 ]

path = os.path.expanduser("~/storage/downloads/ip.txt")
proxies = set()
total = len(sites)
ip_port_pattern = re.compile(r"(?:(?:http|https|socks4|socks5|socks)://)?(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})")

def extract_from_json(obj):
    found = set()
    if isinstance(obj, dict):
        for v in obj.values(): found.update(extract_from_json(v))
    elif isinstance(obj, list):
        for item in obj: found.update(extract_from_json(item))
    elif isinstance(obj, str):
        try: obj = base64.b64decode(obj).decode("utf-8")
        except: pass
        try: obj = gzip.decompress(obj.encode("utf-8")).decode("utf-8")
        except: pass
        for m in ip_port_pattern.findall(obj): found.add(f"{m[0]}:{m[1]}")
    return found

for i, site in enumerate(sites, 1):
    print(f"Downloading {int(i/total*100)}% -> {site}")
    sys.stdout.flush()
    try:
        r = requests.get(site, timeout=20)
        text = r.text.strip()
        extracted = set()
        try: extracted.update(extract_from_json(json.loads(text)))
        except: extracted.update(f"{m[0]}:{m[1]}" for m in ip_port_pattern.findall(text))
        proxies.update(extracted)
    except Exception as e:
        print(f"Failed: {site} -> {e}")

os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as f: f.write("\n".join(sorted(proxies)))
print(f"Saved -> {path}\nTotal proxies: {len(proxies)}")