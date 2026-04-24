termux:
pre-requirements:
pkg update && pkg upgrade
pkg install python
pkg install python-pip
pip install --upgrade pip
pip install aiohttp
pip install aiohttp_socks
termux-setup-storage

put your ip.txt & proxy_finder.py in Download folder of your storage & 
run: type below code on termux:

👇
cd /sdcard/Download
python proxy_finder.py
👆

if u want to change parameters:
nano proxy_finder.py

u need only results of stage 4:
ip&port with https urls 100% are global proxies.
ip&port with http urls, idk, test urself with V2rayng or Psiphon
20%-50% working, false positive test results due to ip redirect and dns hijacking.
http ones could be socks! try yorself!

it supports recognizing cidr ips /24 /16 ... 

credit: AvernuS (telegram id: @omidzht)
logic by me (help of chatgpt)
