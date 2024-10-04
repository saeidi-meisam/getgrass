import os
import requests
import time
import argparse
import asyncio
import socket
from loguru import logger
from aiohttp import ClientSession, ClientTimeout
from tqdm.asyncio import tqdm

# تنظیمات اولیه
ALL_PROXIES_FILE = 'all_proxies.txt'
SOCKS5_PROXIES_FILE = 'proxy.txt'
MYPROXY_FILE = 'myproxy.txt'
MYAD_FILE = 'myad.txt'
LOG_FILE = 'getproxy.log'

# URL برای دانلود لیست پروکسی‌ها
PROXY_SOURCE_URL = 'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt'

# تنظیمات لاگ
logger.add(LOG_FILE, rotation="1 MB")

def log_message(message):
    """ثبت پیام در فایل لاگ و نمایش آن در ترمینال."""
    logger.info(message)

def read_proxies(file_path):
    """خواندن پروکسی‌ها از یک فایل و بازگرداندن آن‌ها به صورت مجموعه."""
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r') as f:
        proxies = set(line.strip() for line in f if line.strip())
    return proxies

def save_proxies(file_path, proxies):
    """ذخیره پروکسی‌ها به یک فایل به صورت مرتب شده."""
    with open(file_path, 'w') as f:
        for proxy in sorted(proxies):
            f.write(f"{proxy}\n")

def filter_socks5_proxies(all_proxies):
    """فیلتر کردن پروکسی‌های SOCKS5 از لیست کلی پروکسی‌ها."""
    socks5_proxies = set()
    for proxy in all_proxies:
        if proxy.lower().startswith('socks5://'):
            socks5_proxies.add(proxy)
    return socks5_proxies

def download_proxies(url):
    """دانلود پروکسی‌ها از URL مشخص شده."""
    try:
        log_message(f"Downloading proxies from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        proxies = set(line.strip() for line in response.text.splitlines() if line.strip())
        log_message(f"Download complete. Total proxies fetched: {len(proxies)}")
        return proxies
    except requests.exceptions.RequestException as e:
        log_message(f"Error downloading proxies: {e}")
        return set()

def extract_proxies_from_url(url):
    """استخراج پروکسی‌ها از یک لینک مشخص شده."""
    try:
        log_message(f"Extracting proxies from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # فرض بر این است که پروکسی‌ها در هر خط از محتوا موجود هستند
        proxies = set(line.strip() for line in response.text.splitlines() if line.strip())
        log_message(f"Extracted {len(proxies)} proxies from {url}.")
        return proxies
    except requests.exceptions.RequestException as e:
        log_message(f"Error extracting proxies from {url}: {e}")
        return set()

def add_proxies(new_proxies):
    """اضافه کردن پروکسی‌های جدید به فایل all_proxies.txt و به‌روزرسانی proxy.txt."""
    # خواندن پروکسی‌های موجود
    existing_proxies = read_proxies(ALL_PROXIES_FILE)
    initial_count = len(existing_proxies)

    # اضافه کردن پروکسی‌های جدید (بدون تکرار)
    updated_proxies = existing_proxies.union(new_proxies)
    added_count = len(updated_proxies) - initial_count

    if added_count > 0:
        save_proxies(ALL_PROXIES_FILE, updated_proxies)
        log_message(f"Added {added_count} new proxies to {ALL_PROXIES_FILE}.")
    else:
        log_message("No new proxies were added (all proxies already exist).")

    # فیلتر کردن پروکسی‌های SOCKS5 و ذخیره در proxy.txt
    socks5_proxies = filter_socks5_proxies(updated_proxies)
    save_proxies(SOCKS5_PROXIES_FILE, socks5_proxies)
    log_message(f"Updated {SOCKS5_PROXIES_FILE} with {len(socks5_proxies)} SOCKS5 proxies.")

async def check_proxy(proxy):
    """بررسی قابلیت اتصال به پراکسی SOCKS5."""
    if not proxy.lower().startswith('socks5://'):
        return False
    try:
        # استخراج IP و پورت
        parts = proxy.split('://')[1].split(':')
        ip = parts[0]
        port = int(parts[1])

        # ایجاد یک سوکت
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        # تلاش برای اتصال به پراکسی
        sock.connect((ip, port))
        sock.close()
        return True
    except:
        return False

async def check_proxies():
    """بررسی تمامی پروکسی‌های SOCKS5 و نگهداری تنها آن‌هایی که قابل اتصال هستند."""
    proxies = read_proxies(SOCKS5_PROXIES_FILE)
    if not proxies:
        log_message("No SOCKS5 proxies found to check.")
        return

    log_message(f"Starting to check {len(proxies)} SOCKS5 proxies...")

    valid_proxies = set()
    tasks = [check_proxy(proxy) for proxy in proxies]

    # استفاده از tqdm برای نمایش نوار پیشرفت
    for proxy, is_valid in tqdm(zip(proxies, await asyncio.gather(*tasks)), total=len(proxies), desc="Checking proxies"):
        if is_valid:
            valid_proxies.add(proxy)
        else:
            log_message(f"Proxy {proxy} failed the check and will be removed.")

    # ذخیره تنها پروکسی‌های معتبر
    save_proxies(SOCKS5_PROXIES_FILE, valid_proxies)
    log_message(f"Check complete. {len(valid_proxies)} out of {len(proxies)} proxies are valid.")

def update_proxies():
    """به‌روزرسانی لیست پروکسی‌ها با دانلود جدید و فیلتر کردن SOCKS5."""
    # دانلود پروکسی‌ها
    downloaded_proxies = download_proxies(PROXY_SOURCE_URL)
    if not downloaded_proxies:
        log_message("No proxies downloaded. Skipping update.")
        return

    # خواندن پروکسی‌های موجود
    existing_proxies = read_proxies(ALL_PROXIES_FILE)
    initial_count = len(existing_proxies)

    # اضافه کردن پروکسی‌های جدید (بدون تکرار)
    updated_proxies = existing_proxies.union(downloaded_proxies)
    added_count = len(updated_proxies) - initial_count

    if added_count > 0:
        save_proxies(ALL_PROXIES_FILE, updated_proxies)
        log_message(f"Added {added_count} new proxies to {ALL_PROXIES_FILE}.")
    else:
        log_message("No new proxies were added (all proxies already exist).")

    # فیلتر کردن پروکسی‌های SOCKS5 و ذخیره در proxy.txt
    socks5_proxies = filter_socks5_proxies(updated_proxies)
    save_proxies(SOCKS5_PROXIES_FILE, socks5_proxies)
    log_message(f"Updated {SOCKS5_PROXIES_FILE} with {len(socks5_proxies)} SOCKS5 proxies.")

def add_proxies_from_files():
    """اضافه کردن پروکسی‌ها از myproxy.txt و myad.txt."""
    new_proxies = set()

    # اضافه کردن پروکسی‌های myproxy.txt
    if os.path.exists(MYPROXY_FILE):
        proxies_from_myproxy = read_proxies(MYPROXY_FILE)
        new_proxies.update(proxies_from_myproxy)
        log_message(f"Loaded {len(proxies_from_myproxy)} proxies from {MYPROXY_FILE}.")
    else:
        log_message(f"{MYPROXY_FILE} not found. Skipping.")

    # استخراج پروکسی‌ها از لینک‌های موجود در myad.txt
    if os.path.exists(MYAD_FILE):
        with open(MYAD_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        log_message(f"Found {len(urls)} URLs in {MYAD_FILE} to extract proxies.")
        for url in urls:
            proxies_from_url = extract_proxies_from_url(url)
            new_proxies.update(proxies_from_url)
    else:
        log_message(f"{MYAD_FILE} not found. Skipping.")

    return new_proxies

def main():
    parser = argparse.ArgumentParser(description='Manage and update proxy lists.')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # دستور add برای اضافه کردن پروکسی‌های جدید
    add_parser = subparsers.add_parser('add', help='Add new proxies')
    add_parser.add_argument('proxies', nargs='*', help='Proxies to add via command line (e.g., socks5://user:pass@host:port)')

    # دستور update برای به‌روزرسانی پروکسی‌ها از منبع
    update_parser = subparsers.add_parser('update', help='Update proxies from the source URL')

    # دستور check برای بررسی پروکسی‌های SOCKS5
    check_parser = subparsers.add_parser('check', help='Check SOCKS5 proxies and keep only valid ones')

    args = parser.parse_args()

    if args.command == 'add':
        # پروکسی‌های جدید از خط فرمان
        new_proxies = set(args.proxies)
        log_message(f"Adding {len(new_proxies)} proxies from command line.")

        # پروکسی‌های جدید از myproxy.txt و myad.txt
        proxies_from_files = add_proxies_from_files()
        new_proxies.update(proxies_from_files)
        log_message(f"Total new proxies to add: {len(new_proxies)}.")

        add_proxies(new_proxies)
    elif args.command == 'update':
        update_proxies()
    elif args.command == 'check':
        asyncio.run(check_proxies())
    else:
        # بدون هیچ دستوری، به‌طور خودکار پروکسی‌ها را به‌روزرسانی می‌کند
        update_proxies()

if __name__ == '__main__':
    main()

