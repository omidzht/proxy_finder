# =======================
# proxy_finder_windows_ultrafast.py
# =======================

# ===== بخش ۱: ایمپورت‌ها =====
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
import ipaddress
import re
import time
from pathlib import Path
import os
import socket
import psutil
from concurrent.futures import ThreadPoolExecutor

# ===== بخش ۲: مسیر فایل‌ها و پوشه‌ها =====
INPUT_FILE = Path("ip.txt")
RESULTS_FOLDER = Path("results")
RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
FINAL_OUTPUT = RESULTS_FOLDER / "final_all_proxies.txt"

# ===== بخش ۳: پورت‌های دیفالت =====
DEFAULT_PORTS = {
    80,161,443,808,1000,1010,1080,1081,1085,1086,1089,1090,1194,1234,
    2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2052,2053,2056,2080,2082,2083,2086,2087,2095,2096,
    3128,3389,5001,5555,5900,6666,7000,7001,7070,7777,8000,8080,8081,8085,8090,8181,8291,8443,8880,8881,8888,
    9000,9001,9090,9100,9107,9797,9999,10008,10808,10809,11080,16000,44485,52869
}

MAX_IPS_SAFE = 10000000

GREEN="\033[92m"
RESET="\033[0m"

# ===== بخش ۴: مدیریت منابع و concurrency =====
cpu_count = os.cpu_count()
mem_available = psutil.virtual_memory().available

# تعداد کانکشن همزمان و ThreadPool
MAX_CONCURRENCY = min(500, cpu_count*50, mem_available//(10*1024*1024))
sem = asyncio.Semaphore(MAX_CONCURRENCY)
MAX_THREADS = min(64, cpu_count*4)
executor = ThreadPoolExecutor(max_workers=MAX_THREADS)

# ===== بخش ۵: تعریف استیج‌ها =====
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

# ===== بخش ۶: مدیریت محدودیت منابع (ویندوز) =====
def set_ulimit():
    # ویندوز resource نداره، فقط info نمایش می‌ده
    print(f"Max concurrency used: {MAX_CONCURRENCY}, Threads: {MAX_THREADS}")

# ===== بخش ۷: خواندن IP و پورت‌ها =====
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

# ===== بخش ۸: تست پورت باز (async) =====
async def check_port(ip,port):
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=2)
        writer.close(); await writer.wait_closed(); return True
    except (asyncio.TimeoutError, ConnectionResetError, OSError, socket.error):
        return False

# ===== بخش ۹: تست پروکسی‌ها =====
async def test_proxy(ip, port, stage):
    types = ["HTTP","HTTPS","SOCKS4","SOCKS5"]
    results=[]
    urls = stage["urls"]
    key=(ip,port)
    if key not in tested_sites: tested_sites[key]=set()

    for proxy_type in types:
        try:
            if proxy_type in ["HTTP","HTTPS"]:
                proxy=f"{proxy_type.lower()}://{ip}:{port}"
                connector=None
            elif proxy_type=="SOCKS4":
                connector=ProxyConnector.from_url(f"socks4://{ip}:{port}")
                proxy=None
            else:
                connector=ProxyConnector.from_url(f"socks5://{ip}:{port}")
                proxy=None
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
                    except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError, OSError):
                        continue
        except:
            continue
    return results

# ===== بخش ۱۰: تست مرحله ۴ =====
async def test_proxy_stage4(ip, port, stage):
    types = ["HTTP","HTTPS","SOCKS4","SOCKS5"]
    results=[]
    urls = stage["urls"] + [u.replace("https://","http://") for u in stage["urls"]]
    key=(ip,port)
    if key not in tested_sites: tested_sites[key]=set()

    for proxy_type in types:
        try:
            if proxy_type in ["HTTP","HTTPS"]:
                proxy=f"{proxy_type.lower()}://{ip}:{port}"
                connector=None
            elif proxy_type=="SOCKS4":
                connector=ProxyConnector.from_url(f"socks4://{ip}:{port}")
                proxy=None
            else:
                connector=ProxyConnector.from_url(f"socks5://{ip}:{port}")
                proxy=None
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
                    except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError, OSError):
                        continue
        except:
            continue
    results.sort(key=lambda x: ((x[3]=="HTTPS"), len(x[4])), reverse=True)
    return results

# ===== بخش ۱۱: اجرای استیج‌ها با asyncio + ThreadPool =====
async def run_stage(stage, ips_ports):
    results=[]
    total=len(ips_ports)
    found_count=0
    progress_count=0
    print(f"\n=== {stage['name'].upper()} ===")
    
    async def bound(ip, port):
        nonlocal progress_count, found_count
        async with sem:
            res=[]
            if stage["name"]=="stage0":
                ok = await check_port(ip, port)
                if ok:
                    proxy_scores[(ip, port)] = 0
                    tested_sites[(ip, port)] = set()
                    found_count += 1
                    res.append((ip, port, 0, None, []))
            elif stage["name"]=="stage4":
                res = await test_proxy_stage4(ip, port, stage)
                if res: found_count += 1
            else:
                res = await test_proxy(ip, port, stage)
                if res: found_count += 1

            progress_count += 1
            if stage["name"]=="stage0":
                print(f"\rprogress {progress_count}/{total} | found {found_count}", end="")
            else:
                for r in res:
                    print(f"\rprogress {progress_count}/{total} | found {found_count} | {GREEN}{r[0]}:{r[1]}{RESET}", end="\n")
            results.extend(res)

    tasks=[bound(ip, port) for ip, port in ips_ports]
    batch_size=1000 if stage["name"]=="stage0" else 100
    for i in range(0, len(tasks), batch_size):
        await asyncio.gather(*tasks[i:i+batch_size])

    print(f"\n{stage['name']} DONE -> found {found_count}")
    return results

# ===== بخش ۱۲: تابع اصلی =====
async def main():
    set_ulimit()
    
    if not INPUT_FILE.exists():
        print(f"Input file {INPUT_FILE} not found!")
        return
    
    text = INPUT_FILE.read_text(errors="ignore")
    ips, ports = parse_input(text)
    print(f"IPs: {len(ips)} | Ports: {len(ports)}")
    ips_ports = [(ip, port) for ip in ips for port in ports]

    # پاک کردن فایل نهایی قبلی
    if FINAL_OUTPUT.exists():
        FINAL_OUTPUT.unlink()

    for stage in STAGES:
        stage_results = await run_stage(stage, ips_ports)

        # مرتب‌سازی مرحله ۴
        if stage["name"]=="stage4":
            stage_results.sort(key=lambda x: ((x[3]=="HTTPS"), len(x[4])), reverse=True)

        stage_file = RESULTS_FOLDER / f"{stage['name']}.txt"
        with open(stage_file, "w", encoding="utf-8") as f:
            for item in stage_results:
                ip, port, score, proto, sites = item
                site_str = " ".join(f"{s[0]}={s[1]:.2f}s" for s in sites)
                proto_str = f"({proto})" if proto else ""
                f.write(f"{ip}:{port} {proto_str} score={score:.2f} | {site_str}\n")

        with open(FINAL_OUTPUT, "a", encoding="utf-8") as f:
            for item in stage_results:
                ip, port, score, proto, sites = item
                site_str = " ".join(f"{s[0]}={s[1]:.2f}s" for s in sites)
                proto_str = f"({proto})" if proto else ""
                f.write(f"{stage['name']} {ip}:{port} {proto_str} score={score:.2f} | {site_str}\n")

        # فقط پروکسی‌های موفق برای مرحله بعد باقی می‌مانند
        ips_ports = [(item[0], item[1]) for item in stage_results]

    print("\nALL DONE → final_all_proxies.txt")

# ===== بخش ۱۳: اجرای برنامه =====
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExecution stopped by user.")