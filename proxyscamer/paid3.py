در اولین اسکریپت که از منابعی سرچ می‌کنه soak5 رایگان اینم بخشی آرشه import requests
from bs4 import BeautifulSoup
import concurrent.futures
import re
import time
import random
from itertools import product
from threading import Lock
from fake_useragent import UserAgent
from requests_html import HTMLSession
from colorama import Fore, Style, init
import sys
import logging

# تنظیمات اولیه رنگی
init(autoreset=True)

# تنظیمات لاگینگ
logging.basicConfig(
    filename='proxy_scraper.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تنظیمات اولیه
ua = UserAgent()
lock = Lock()

# منابع جستجو و کلمات کلیدی پایه
base_search_terms = [
    "SOCKS5 proxy",
    "premium proxy list",
    "proxy with username password",
    "SOCKS5 authentication proxy",
    "free SOCKS5 proxy account",
]

# ترکیب کلمات کلیدی برای افزایش تنوع
def generate_search_terms():
    additional_terms = ["free", "premium", "list", "login", "auth", "account"]
    return [" ".join(combo) for combo in product(base_search_terms, additional_terms)]

# موتورهای جستجو
search_engines = {
    "google": "https://www.google.com/search?q=",
    "bing": "https://www.bing.com/search?q=",
    "duckduckgo": "https://duckduckgo.com/html/?q=",  # DuckDuckGo ارائه نسخه HTML برای آسان‌تر اسکرپینگ
    "yandex": "https://yandex.com/search/?text=",
}

# منابع تست پراکسی
test_urls = [
    "https://httpbin.org/ip",
    "https://ifconfig.me/ip",
    "https://api.myip.com"
]

# پراکسی‌ها و فایل‌های لاگ
working_proxies = []
found_proxies = []
used_proxies = set()

# الگوهای مختلف پراکسی با یوزرنیم و پسورد
proxy_auth_patterns = [
    re.compile(r"(\w+:\w+@(?:\d{1,3}\.){3}\d{1,3}:\d{2,5})"),
    re.compile(r"(socks5:\/\/\w+:\w+@(?:\d{1,3}\.){3}\d{1,3}:\d{2,5})"),
    re.compile(r"(https?:\/\/\w+:\w+@(?:\d{1,3}\.){3}\d{1,3}:\d{2,5})")
]

# توابع جستجوی موتورهای مختلف
def search_google(query):
    url = f"{search_engines['google']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(2, 5))  # تاخیر تصادفی
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if "url?q=" in href and not "webcache" in href:
                actual_url = href.split("?q=")[1].split("&sa=U")[0]
                links.append(actual_url)
        logging.info(f"Google search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        logging.error(f"Error searching Google for '{query}': {e}")
        return []

def search_bing(query):
    url = f"{search_engines['bing']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(2, 5))  # تاخیر تصادفی
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith("http") and "bing.com" not in href:
                links.append(href)
        logging.info(f"Bing search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        logging.error(f"Error searching Bing for '{query}': {e}")
        return []

def search_duckduckgo(query):
    url = f"{search_engines['duckduckgo']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(2, 5))  # تاخیر تصادفی
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith("http") and "duckduckgo.com" not in href:
                links.append(href)
        logging.info(f"DuckDuckGo search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        logging.error(f"Error searching DuckDuckGo for '{query}': {e}")
        return []

def search_yandex(query):
    url = f"{search_engines['yandex']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(2, 5))  # تاخیر تصادفی
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith("http") and "yandex.com" not in href:
                links.append(href)
        logging.info(f"Yandex search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        logging.error(f"Error searching Yandex for '{query}': {e}")
        return []

# موتورهای جستجوی مبتنی بر هوش مصنوعی (در صورت داشتن API)
def search_ai_engine(query, engine_name, api_key):
    """
    پیاده‌سازی جستجو با موتورهای هوش مصنوعی مانند Perplexity AI و You.com
    """
    if engine_name.lower() == "perplexity":
        url = "https://api.perplexity.ai/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {"query": query}
        try:
            response = requests.post(url, headers=headers, json=data, timeout=20)
            response.raise_for_status()
            results = response.json().get("results", [])
            links = [result['url'] for result in results if 'url' in result]
            logging.info(f"Perplexity AI search for '{query}' returned {len(links)} links.")
            return links
        except Exception as e:
            logging.error(f"Error searching Perplexity for '{query}': {e}")
            return []
    elif engine_name.lower() == "you.com":
        url = "https://api.you.com/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {"query": query}
        try:
            response = requests.post(url, headers=headers, json=data, timeout=20)
            response.raise_for_status()
            results = response.json().get("results", [])
            links = [result['url'] for result in results if 'url' in result]
            logging.info(f"You.com AI search for '{query}' returned {len(links)} links.")
            return links
        except Exception as e:
            logging.error(f"Error searching You.com for '{query}': {e}")
            return []
    else:
        logging.warning(f"Unknown AI search engine: {engine_name}")
        return []

# تابع جامع جستجو
def perform_search(engine, query, api_key=None):
    if engine == "google":
        return search_google(query)
    elif engine == "bing":
        return search_bing(query)
    elif engine == "duckduckgo":
        return search_duckduckgo(query)
    elif engine == "yandex":
        return search_yandex(query)
    elif engine.lower() in ["perplexity", "you"]:
        if api_key:
            return search_ai_engine(query, engine, api_key)
        else:
            logging.warning(f"No API key provided for AI search engine: {engine}. Skipping.")
            return []
    else:
        return []

# تابع استخراج پراکسی‌ها از لینک‌ها
def fetch_proxies_from_link(link):
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(link, headers=headers, timeout=10)
        proxies = []
        for pattern in proxy_auth_patterns:
            proxies.extend(pattern.findall(response.text))
        logging.info(f"Fetched {len(proxies)} proxies from {link}.")
        return proxies
    except Exception as e:
        logging.error(f"Error fetching proxies from {link}: {e}")
        return []

# تابع استخراج پراکسی‌ها با رندر کردن جاوااسکریپت (بدون Selenium)
def fetch_proxies_with_js_render(link):
    session = HTMLSession()
    try:
        response = session.get(link)
        response.html.render(timeout=20, sleep=2)
        proxies = []
        for pattern in proxy_auth_patterns:
            proxies.extend(pattern.findall(response.html.html))
        logging.info(f"Fetched {len(proxies)} proxies with JS render from {link}.")
        return proxies
    except Exception as e:
        logging.error(f"Error fetching proxies with JS render from {link}: {e}")
        return []
    finally:
        session.close()

# تابع تست پراکسی‌ها
def test_proxy(proxy):
    proxy_auth_pattern = re.compile(r"(\w+):(\w+@(?:\d{1,3}\.){3}\d{1,3}:\d{2,5})")
    match = proxy_auth_pattern.match(proxy)
    if match:
        username, password_ip_port = match.groups()
        proxy_dict = {
            "http": f"socks5://{username}@{password_ip_port}",
            "https": f"socks5://{username}@{password_ip_port}"
        }
        for url in test_urls:
            try:
                response = requests.get(url, proxies=proxy_dict, timeout=5)
                if response.status_code == 200:
                    print(Fore.GREEN + f"[+] Proxy {proxy} is working for {url}.")
                    with lock:
                        working_proxies.append(proxy)
                    return proxy
            except Exception as e:
                print(Fore.RED + f"[-] Proxy {proxy} failed for {url}: {e}")
    return None

# واحد جستجو با عمق مشخص
def search_unit(engine, query, max_depth=3, api_key=None):
    print(Fore.CYAN + f"[*] Starting search on {engine} for query: '{query}' with depth {max_depth}")
    logging.info(f"Starting search on {engine} for query: '{query}' with depth {max_depth}")
    depth = 0
    current_links = perform_search(engine, query, api_key)
    all_extracted_proxies = []
    
    while depth < max_depth:
        depth += 1
        print(Fore.MAGENTA + f"[+] {engine} - Depth {depth}/{max_depth} for query: '{query}'")
        logging.info(f"{engine} - Depth {depth}/{max_depth} for query: '{query}'")
        new_links = []
        
        # استخراج پراکسی‌ها
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(fetch_proxies_from_link, current_links)
            for proxies in results:
                all_extracted_proxies.extend(proxies)
        
        # استخراج پراکسی‌ها با رندر جاوااسکریپت
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(fetch_proxies_with_js_render, current_links)
            for proxies in results:
                all_extracted_proxies.extend(proxies)
        
        # استخراج لینک‌های جدید برای عمق بیشتر
        for link in current_links:
            try:
                response = requests.get(link, headers={"User-Agent": ua.random}, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")
                for sublink in soup.find_all('a', href=True):
                    href = sublink['href']
                    if href.startswith("http") and engine not in href:
                        new_links.append(href)
            except Exception as e:
                print(Fore.RED + f"Error fetching sub-links from {link}: {e}")
                logging.error(f"Error fetching sub-links from {link}: {e}")
        
        current_links = new_links
        # تاخیر تصادفی برای جلوگیری از بلاک شدن
        time.sleep(random.uniform(1, 3))
    
    with lock:
        found_proxies.extend(all_extracted_proxies)
    print(Fore.YELLOW + f"[!] Completed search on {engine} for query: '{query}'. Found {len(all_extracted_proxies)} proxies.")
    logging.info(f"Completed search on {engine} for query: '{query}'. Found {len(all_extracted_proxies)} proxies.")
    return all_extracted_proxies

# تابع اصلی
def main():
    print(Fore.BLUE + "=== Proxy Scraper Start ===")
    logging.info("=== Proxy Scraper Start ===")
    print("Generating search terms...")
    logging.info("Generating search terms...")
    search_terms = generate_search_terms()
    
    # دریافت API keys از کاربر
    api_keys = {}
    print("\nPlease enter API keys for AI-based search engines. Leave blank to skip.")
    logging.info("Requesting API keys for AI-based search engines.")
    for engine in ["perplexity", "you"]:
        key = input(f"Enter API key for {engine.capitalize()} (or press Enter to skip): ").strip()
        if key:
            api_keys[engine] = key
            logging.info(f"API key provided for {engine.capitalize()}.")
        else:
            logging.info(f"No API key provided for {engine.capitalize()}. Skipping.")
    
    cycle = 1
    while True:
        print(Fore.BLUE + f"\n=== Starting Search Cycle {cycle} ===")
        logging.info(f"=== Starting Search Cycle {cycle} ===")
        all_proxies = []
        
        # جستجوی چندمنبعی موازی
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for engine, query in product(search_engines.keys(), search_terms):
                futures.append(executor.submit(search_unit, engine, query, max_depth=3, api_key=api_keys.get(engine.lower())))
            # اضافه کردن موتورهای هوش مصنوعی در صورت داشتن API
            for engine, query in product(["perplexity", "you"], search_terms):
                if engine in api_keys:
                    futures.append(executor.submit(search_unit, engine, query, max_depth=3, api_key=api_keys.get(engine.lower())))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    proxies = future.result()
                    # تمام پراکسی‌های یافت شده در 'found_proxies' ذخیره شده‌اند
                except Exception as e:
                    print(Fore.RED + f"Search unit encountered an error: {e}")
                    logging.error(f"Search unit encountered an error: {e}")
        
        # حذف تکراری‌ها
        unique_proxies = list(set(found_proxies))
        print(Fore.YELLOW + f"[!] Total unique proxies found: {len(unique_proxies)}")
        logging.info(f"Total unique proxies found: {len(unique_proxies)}")
        
        # تست پراکسی‌های استخراج‌شده
        print(Fore.BLUE + f"[+] Testing {len(unique_proxies)} extracted proxies...")
        logging.info(f"Testing {len(unique_proxies)} extracted proxies.")
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(test_proxy, unique_proxies)
            for proxy in results:
                if proxy:
                    with lock:
                        working_proxies.append(proxy)
        
        print(Fore.GREEN + f"[+] Total working proxies: {len(working_proxies)}")
        logging.info(f"Total working proxies: {len(working_proxies)}")
        
        # ذخیره پراکسی‌های معتبر در فایل
        with open("working_premium_proxies_with_auth.txt", "a") as f:
            for proxy in working_proxies:
                f.write(f"socks5://{proxy}\n")
        
        print(Fore.CYAN + "Working proxies have been saved to 'working_premium_proxies_with_auth.txt'.")
        logging.info("Working proxies have been saved to 'working_premium_proxies_with_auth.txt'.")
        
        # پاکسازی لیست پراکسی‌های یافت شده برای دوره بعدی
        found_proxies.clear()
        
        # افزایش دوره جستجو
        cycle += 1
        
        # تاخیر بین دوره‌ها
        print(Fore.BLUE + "Waiting before starting the next cycle...")
        logging.info("Waiting before starting the next cycle...")
        time.sleep(random.uniform(300, 600))  # انتظار 5 تا 10 دقیقه قبل از شروع دوره جدید

if __name__ == "__main__":
    main() اصلاح کن اینم فرایند کارو نشان بده تعداد پروکسی سالمپت۵G0Y8_bJq1EqhI$G0Y8_bJq1EqhI$g
