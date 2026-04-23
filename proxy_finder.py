# ===== بخش ۱: ایمپورت و تنظیمات =====
import asyncio
import aiohttp
import ipaddress
import re
import time
from pathlib import Path
import resource
from aiohttp_socks import ProxyConnector

INPUT_FILE = "/sdcard/Download/ip.txt"
DEFAULT_PORTS = {80,8080,8081,3128,8888,9090,7070,2080,2095,2052,2053,1080,1081,10808,10809,8291}
MAX_IPS_SAFE = 50000
FINAL_OUTPUT = "/sdcard/Download/final_all_proxies.txt"

CONCURRENCY_STAGE0 = 100
CONCURRENCY_BASE = 50
BATCH_STAGE0 = 500
BATCH_OTHER = 50

STAGES = [
    {"name":"stage0","timeout":2,"urls":[],"latency":2},
    {"name":"stage1","timeout":4,"urls":[
        "http://www.google.com","http://github.com","http://httpbin.org/ip",
        "http://www.cloudflare.com","http://api.ipify.org","http://www.stackoverflow.com",
        "http://www.reddit.com"
    ],"latency":5},
    {"name":"stage2","timeout":6,"urls":[
        "http://httpbin.org/ip","http://api.ipify.org",
        "http://www.stackoverflow.com","http://www.reddit.com"
    ],"latency":7},
    {"name":"stage3","timeout":10,"urls":[
        "http://www.cloudflare.com/cdn-cgi/trace","http://httpbin.org/get"
    ],"latency":10},
    {"name":"stage4","timeout":15,"urls":[
        "https://www.cloudflare.com/cdn-cgi/trace","https://httpbin.org/get","https://t.me",
        "https://speed.cloudflare.com/__down?bytes=500000"
    ],"latency":15}
]

proxy_scores = {}
tested_sites = {}

GREEN="\033[92m"
RESET="\033[0m"

def set_ulimit():
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (4096, hard))
    except:
        pass

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

# ===== بخش ۲: تست پورت و پروکسی =====
async def check_port(ip,port):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=2)
        writer.close(); await writer.wait_closed(); return True
    except: return False

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

# ===== بخش ۳: تست مرحله ۴ با مرتب‌سازی =====
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

# ===== بخش ۴: اجرای استیج‌ها =====
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

# ===== بخش ۵: تابع اصلی =====
async def main():
    set_ulimit()
    text = Path(INPUT_FILE).read_text(errors="ignore")
    ips, ports = parse_input(text)
    print(f"IPs: {len(ips)} | Ports: {len(ports)}")
    ips_ports = [(ip,port) for ip in ips for port in ports]

    for stage in STAGES:
        stage_results = await run_stage(stage, ips_ports)

        # مرتب‌سازی برای مرحله ۴: اول HTTPS و سایت‌های بیشتر
        if stage["name"]=="stage4":
            stage_results.sort(key=lambda x: ((x[3]=="HTTPS"), len(x[4])), reverse=True)

        stage_file = f"/sdcard/Download/{stage['name']}.txt"
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

        # برای مرحله بعد فقط پروکسی‌های موفق باقی می‌مانند
        ips_ports = [(item[0],item[1]) for item in stage_results]

    print("\nALL DONE → final_all_proxies.txt")

if __name__=="__main__":
    asyncio.run(main())