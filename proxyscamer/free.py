import requests
import concurrent.futures
import time

# لیست منابع پراکسی رایگان
proxy_sources = [
    "https://www.proxy-list.download/api/v1/get?type=socks5",
    "https://www.proxyscan.io/download?type=socks5",
    "https://api.proxyscrape.com/?request=getproxies&proxytype=socks5&timeout=5000&country=all",
]

# آدرس برای تست سلامت پراکسی
test_url = "https://httpbin.org/ip"
working_proxies = []

# تابع برای جمع‌آوری پراکسی‌ها از منابع مختلف
def gather_proxies():
    proxies = []
    for source in proxy_sources:
        try:
            response = requests.get(source)
            if response.status_code == 200:
                new_proxies = response.text.splitlines()
                proxies.extend(new_proxies)
        except Exception as e:
            print(f"Error fetching proxies from {source}: {e}")
    return proxies

# تابع برای تست عملکرد پراکسی
def test_proxy(proxy):
    proxy_dict = {
        "http": f"socks5://{proxy}",
        "https": f"socks5://{proxy}"
    }
    try:
        response = requests.get(test_url, proxies=proxy_dict, timeout=5)
        if response.status_code == 200:
            print(f"Proxy {proxy} is working.")
            return proxy
    except Exception as e:
        print(f"Proxy {proxy} failed: {e}")
    return None

# تابع اصلی برای جمع‌آوری و تست پراکسی‌ها
def main():
    print("Gathering proxies...")
    proxies = gather_proxies()
    print(f"Collected {len(proxies)} proxies. Testing...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(test_proxy, proxies)

    for proxy in results:
        if proxy:
            working_proxies.append(proxy)

    print(f"{len(working_proxies)} working proxies found.")

    # ذخیره پراکسی‌های معتبر در یک فایل
    with open("working_proxies.txt", "w") as f:
        for proxy in working_proxies:
            f.write(f"socks5://{proxy}\n")

    print("Working proxies saved to working_proxies.txt")

if __name__ == "__main__":
    main()
