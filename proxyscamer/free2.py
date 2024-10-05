import requests
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

# تنظیمات اولیه رنگی
init(autoreset=True)

# تنظیمات اولیه
ua = UserAgent()
lock = Lock()

# منابع جستجو و کلمات کلیدی پایه
base_search_terms = [
    "SOCKS5 proxy",
    "free SOCKS5 proxy list",
    "SOCKS5 proxies with authentication",
]

# ترکیب کلمات کلیدی برای افزایش تنوع
def generate_search_terms():
    additional_terms = ["free", "premium", "list", "fast", "best", "auth"]
    return [" ".join(combo) for combo in product(base_search_terms, additional_terms)]

# موتورهای جستجو
search_engines = {
    "google": "https://www.google.com/search?q=",
    "bing": "https://www.bing.com/search?q=",
    "duckduckgo": "https://duckduckgo.com/html/?q=",
    "yandex": "https://yandex.com/search/?text=",
}

# منابع تست پراکسی
test_urls = [
    "https://httpbin.org/ip",
    "https://ifconfig.me/ip",
]

# پراکسی‌ها و فایل‌های لاگ
working_proxies = []
found_proxies = set()

# الگوهای مختلف پراکسی با یوزرنیم و پسورد
proxy_auth_patterns = [
    re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5})")
]

# توابع جستجوی موتورهای مختلف
def search_google(query):
    url = f"{search_engines['google']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(1, 3))
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a['href'] for a in soup.find_all('a', href=True) if "url?q=" in a['href']]
        print(Fore.CYAN + f"Google search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        print(Fore.RED + f"Error searching Google for '{query}': {e}")
        return []

def search_bing(query):
    url = f"{search_engines['bing']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(1, 3))
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a['href'] for a in soup.find_all('a', href=True) if "bing.com" not in a['href']]
        print(Fore.CYAN + f"Bing search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        print(Fore.RED + f"Error searching Bing for '{query}': {e}")
        return []

def search_duckduckgo(query):
    url = f"{search_engines['duckduckgo']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(1, 3))
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a['href'] for a in soup.find_all('a', href=True) if "duckduckgo.com" not in a['href']]
        print(Fore.CYAN + f"DuckDuckGo search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        print(Fore.RED + f"Error searching DuckDuckGo for '{query}': {e}")
        return []

def search_yandex(query):
    url = f"{search_engines['yandex']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(1, 3))
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a['href'] for a in soup.find_all('a', href=True) if "yandex.com" not in a['href']]
        print(Fore.CYAN + f"Yandex search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        print(Fore.RED + f"Error searching Yandex for '{query}': {e}")
        return []

# تابع جامع جستجو
def perform_search(engine, query):
    if engine == "google":
        return search_google(query)
    elif engine == "bing":
        return search_bing(query)
    elif engine == "duckduckgo":
        return search_duckduckgo(query)
    elif engine == "yandex":
        return search_yandex(query)
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
        print(Fore.MAGENTA + f"Fetched {len(proxies)} proxies from {link}.")
        return proxies
    except Exception as e:
        print(Fore.RED + f"Error fetching proxies from {link}: {e}")
        return []

# تابع تست پراکسی‌ها
def test_proxy(proxy):
    proxy_dict = {
        "http": f"socks5://{proxy}",
        "https": f"socks5://{proxy}"
    }
    for url in test_urls:
        try:
            response = requests.get(url, proxies=proxy_dict, timeout=5)
            if response.status_code == 200:
                print(Fore.GREEN + f"[+] Proxy {proxy} is working.")
                with lock:
                    working_proxies.append(proxy)
                return proxy
        except Exception as e:
            print(Fore.RED + f"[-] Proxy {proxy} failed: {e}")
    return None

# تابع اصلی برای جستجو
def main():
    print(Fore.BLUE + "=== Starting Proxy Scraper ===")
    search_terms = generate_search_terms()
    all_proxies = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # جستجو در تمام موتورهای جستجو برای تمام کلمات کلیدی
        for engine, query in product(search_engines.keys(), search_terms):
            links = perform_search(engine, query)
            # استخراج پراکسی‌ها از لینک‌های پیدا شده
            future_to_link = {executor.submit(fetch_proxies_from_link, link): link for link in links}
            for future in concurrent.futures.as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    proxies = future.result()
                    all_proxies.extend(proxies)
                except Exception as e:
                    print(Fore.RED + f"Error fetching proxies from {link}: {e}")
    
    print(Fore.YELLOW + f"[!] Total proxies found: {len(all_proxies)}")
    
    # تست پراکسی‌های پیدا شده
    print(Fore.BLUE + "[+] Testing found proxies...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(test_proxy, all_proxies)
        for proxy in results:
            if proxy:
                found_proxies.add(proxy)
    
    print(Fore.GREEN + f"[+] Total working proxies: {len(found_proxies)}")

    # ذخیره پراکسی‌های معتبر در فایل
    with open("working_proxies_socks5.txt", "w") as f:
        for proxy in found_proxies:
            f.write(f"socks5://{proxy}\n")
    
    print(Fore.CYAN + "[*] Working proxies saved to 'working_proxies_socks5.txt'.")

if __name__ == "__main__":
    main()
