# =======================
# proxy_finder_kali.py
# =======================

# ===== بخش ۱: ایمپورت و تنظیمات =====
import asyncio
import aiohttp
import ipaddress
import re
import time
from pathlib import Path
import resource
from aiohttp_socks import ProxyConnector

# ==== مسیرهای اصلاح شده برای کالی لینوکس ====
INPUT_FILE = "/home/unknown/Desktop/proxy_finder/ip.txt"
RESULTS_FOLDER = "/home/unknown/Desktop/proxy_finder/results/"
FINAL_OUTPUT = RESULTS_FOLDER + "final_all_proxies.txt"

DEFAULT_PORTS = {80,161,443,808,1000,1010,1080,1081,1085,1086,1089,1090,1194,1234,
    2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2052,2053,2056,2080,2082,2083,2086,2087,2095,2096,
    3128,3389,5001,5555,5900,6666,7000,7001,7070,7777,8000,8080,8081,8085,8090,8181,8291,8443,8880,8881,8888,
    9000,9001,9090,9100,9107,9797,9999,10008,10808,10809,11080,16000,44485,52869}
    
MAX_IPS_SAFE = 100000000

CONCURRENCY_STAGE0 = 250
CONCURRENCY_BASE = 100
BATCH_STAGE0 = 1000
BATCH_OTHER = 100

STAGES = [
    {"name":"stage0","timeout":2,"urls":[],"latency":2},
    {"name":"stage1","timeout":4,"urls":[
        "http://www.google.com","http://github.com","http://httpbin.org/ip",
        "http://www.cloudflare.com","http://api.ipify.org","http://www.stackoverflow.com",
        "http://www.reddit.com"
    ],"latency":4},
    {"name":"stage2","timeout":4,"urls":[
        "http://httpbin.org/ip","http://api.ipify.org",
        "http://www.stackoverflow.com","http://www.reddit.com"
    ],"latency":4},
    {"name":"stage3","timeout":5,"urls":[
        "http://www.cloudflare.com/cdn-cgi/trace","http://httpbin.org/get"
    ],"latency":5},
    {"name":"stage4","timeout":10,"urls":[
        "https://www.cloudflare.com/cdn-cgi/trace","https://httpbin.org/get","https://t.me",
        "https://speed.cloudflare.com/__down?bytes=500000"
    ],"latency":10}
]

proxy_scores = {}
tested_sites = {}

GREEN="\033[92m"
RESET="\033[0m"

# ===== بخش ۲: محدودیت فایل‌ها =====
def set_ulimit():
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (4096, hard))
    except:
        pass

# ===== بخش ۳: خواندن IP و پورت از فایل =====
def parse_input(text):
    ips=set(); ports=set()
    for match in re.findall(r'\d+\.\d+\.\d+\.\d+/\d+', text):
        try: net=ipaddress.ip_network(match, strict=False)
        except: continue
        if net.num_addresses<=65536:
            ips.update(str(ip) for ip in net.hosts())
    for match in re.findall(r'(\d+\.\d+\.\d+\.\d+)-(\d+\.\d+\.\d+\.\d+)', text):
        try: start=int(ipaddress.IPv4Address(match[0])); end=int(ipaddress.IPv4Address(match[1]))
        except: continue
        if end-start<=65536:
            ips.update(str(ipaddress.IPv4Address(ip)) for ip in range(start,end+1))
    for match in re.findall(r'\b\d+\.\d+\.\d+\.\d+\b', text):
        try: ipaddress.IPv4Address(match); ips.add(match)
        except: continue
    for match in re.findall(r':(\d{2,5})', text):
        p=int(match)
        if 1<=p<=65535: ports.add(p)
    if not ports: ports=DEFAULT_PORTS
    ips=list(ips); ports=list(ports)
    if len(ips)>MAX_IPS_SAFE: ips=ips[:MAX_IPS_SAFE]
    return ips,ports

# ===== بخش ۴: تست پورت باز =====
async def check_port(ip,port):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=2)
        writer.close(); await writer.wait_closed(); return True
    except: return False

# ===== بخش ۵: تست پروکسی =====
async def test_proxy(ip, port, stage):
    types = ["HTTP","HTTPS","SOCKS4","SOCKS5"]
    results=[]
    urls = stage["urls"]
    key=(ip,port)
    if key not in tested_sites: tested_sites[key]=set()
    for proxy_type in types:
        try:
            if proxy_type in ["HTTP","HTTPS"]: proxy=f"{proxy_type.lower()}://{ip}:{port}"; connector=None
            elif proxy_type=="SOCKS4": connector=ProxyConnector.from_url(f"socks4://{ip}:{port}"); proxy=None
            else: connector=ProxyConnector.from_url(f"socks5://{ip}:{port}"); proxy=None
            timeout=aiohttp.ClientTimeout(total=stage["timeout"])
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                for url in urls:
                    if url in tested_sites[key]: continue
                    start=time.time()
                    try:
                        async with session.get(url, proxy=proxy, headers={"User-Agent":"Mozilla/5.0"}) as r:
                            if r.status in [200,301,302,403]:
                                latency=time.time()-start
                                tested_sites[key].add(url)
                                proxy_scores.setdefault(key,0)
                                proxy_scores[key]+=1/latency
                                results.append((ip, port, proxy_scores[key], proxy_type, [(url, latency)]))
                                return results
                    except:
                        continue
        except:
            continue
    return results

# ===== بخش ۶: تست مرحله ۴ =====
async def test_proxy_stage4(ip, port, stage):
    types = ["HTTP","HTTPS","SOCKS4","SOCKS5"]
    results=[]
    urls = stage["urls"] + [u.replace("https://","http://") for u in stage["urls"]]
    key=(ip,port)
    if key not in tested_sites: tested_sites[key]=set()
    for proxy_type in types:
        try:
            if proxy_type in ["HTTP","HTTPS"]: proxy=f"{proxy_type.lower()}://{ip}:{port}"; connector=None
            elif proxy_type=="SOCKS4": connector=ProxyConnector.from_url(f"socks4://{ip}:{port}"); proxy=None
            else: connector=ProxyConnector.from_url(f"socks5://{ip}:{port}"); proxy=None
            timeout=aiohttp.ClientTimeout(total=stage["timeout"])
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                for url in urls:
                    if url in tested_sites[key]: continue
                    start=time.time()
                    try:
                        async with session.get(url, proxy=proxy, headers={"User-Agent":"Mozilla/5.0"}) as r:
                            if r.status in [200,301,302,403]:
                                latency=time.time()-start
                                tested_sites[key].add(url)
                                proxy_scores.setdefault(key,0)
                                proxy_scores[key]+=1/latency
                                results.append((ip, port, proxy_scores[key], proxy_type, [(url, latency)]))
                    except:
                        continue
        except:
            continue
    results.sort(key=lambda x: ((x[3]=="HTTPS"), len(x[4])), reverse=True)
    return results

# ===== بخش ۷: اجرای استیج‌ها =====
async def run_stage(stage, ips_ports):
    results=[]
    sem=asyncio.Semaphore(CONCURRENCY_STAGE0 if stage["name"]=="stage0" else CONCURRENCY_BASE)
    total=len(ips_ports)
    found_count=0
    progress_count=0
    print(f"\n=== {stage['name'].upper()} ===")
    
    async def bound(ip,port):
        nonlocal progress_count, found_count
        async with sem:
            res=[]
            if stage["name"]=="stage0":
                ok=await check_port(ip,port)
                if ok:
                    proxy_scores[(ip,port)]=0
                    tested_sites[(ip,port)]=set()
                    found_count+=1
                    res.append((ip, port, 0, None, []))
            elif stage["name"]=="stage4":
                res=await test_proxy_stage4(ip,port,stage)
                if res: found_count+=1
            else:
                res=await test_proxy(ip,port,stage)
                if res: found_count+=1

            progress_count+=1
            if stage["name"]=="stage0":
                print(f"\rprogress {progress_count}/{total} | found {found_count}", end="")
            else:
                for r in res:
                    print(f"\rprogress {progress_count}/{total} | found {found_count} | {GREEN}{r[0]}:{r[1]}{RESET}", end="\n")
            results.extend(res)

    tasks=[bound(ip,port) for ip,port in ips_ports]
    batch_size=BATCH_STAGE0 if stage["name"]=="stage0" else BATCH_OTHER
    for i in range(0,len(tasks),batch_size):
        await asyncio.gather(*tasks[i:i+batch_size])

    print(f"\n{stage['name']} DONE -> found {found_count}")
    return results

# ===== بخش ۸: تابع اصلی =====
async def main():
    set_ulimit()
    Path(RESULTS_FOLDER).mkdir(parents=True, exist_ok=True)
    
    text = Path(INPUT_FILE).read_text(errors="ignore")
    ips, ports = parse_input(text)
    print(f"IPs: {len(ips)} | Ports: {len(ports)}")
    ips_ports = [(ip,port) for ip in ips for port in ports]

    for stage in STAGES:
        stage_results = await run_stage(stage, ips_ports)

        # مرتب‌سازی مرحله ۴
        if stage["name"]=="stage4":
            stage_results.sort(key=lambda x: ((x[3]=="HTTPS"), len(x[4])), reverse=True)

        stage_file = f"{RESULTS_FOLDER}{stage['name']}.txt"
        with open(stage_file, "w") as f:
            for item in stage_results:
                ip,port,score,proto,sites = item
                site_str = " ".join(f"{s[0]}={s[1]:.2f}s" for s in sites)
                proto_str = f"({proto})" if proto else ""
                f.write(f"{ip}:{port} {proto_str} score={score:.2f} | {site_str}\n")

        with open(FINAL_OUTPUT, "a") as f:
            for item in stage_results:
                ip,port,score,proto,sites = item
                site_str = " ".join(f"{s[0]}={s[1]:.2f}s" for s in sites)
                proto_str = f"({proto})" if proto else ""
                f.write(f"{stage['name']} {ip}:{port} {proto_str} score={score:.2f} | {site_str}\n")

        # فقط پروکسی‌های موفق برای مرحله بعد باقی می‌مانند
        ips_ports = [(item[0],item[1]) for item in stage_results]

    print("\nALL DONE → final_all_proxies.txt")

# ===== بخش ۹: اجرای برنامه =====
if __name__ == "__main__":
    # اجرای تابع اصلی asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExecution stopped by user.")
