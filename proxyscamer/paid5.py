import requests
from bs4 import BeautifulSoup
import concurrent.futures
import re
import time
import random
from itertools import product
from threading import Lock
import threading
from fake_useragent import UserAgent
from colorama import Fore, Style, init
import sys

# Initialize colorama for colored output
init(autoreset=True)

# Initialize UserAgent and threading lock
ua = UserAgent()
lock = Lock()

# Flag to control stopping the script
stop_flag = False

# Base search terms for proxy scraping
base_search_terms = [
    "SOCKS5 proxy",
    "premium proxy list",
    "proxy with username password",
    "SOCKS5 authentication proxy",
    "free SOCKS5 proxy account",
]

# Generate diverse search terms by combining base terms with additional keywords
def generate_search_terms():
    additional_terms = ["free", "premium", "list", "login", "auth", "account"]
    return [" ".join(combo) for combo in product(base_search_terms, additional_terms)]

# Define search engines with their respective search URL patterns
search_engines = {
    "google": "https://www.google.com/search?q=",
    "bing": "https://www.bing.com/search?q=",
    "duckduckgo": "https://duckduckgo.com/html/?q=",  # DuckDuckGo provides an HTML version for easier scraping
    "yandex": "https://yandex.com/search/?text=",
    "you": "https://you.com/search?q="
}

# URLs to test the validity of proxies
test_urls = [
    "https://httpbin.org/ip",
    "https://ifconfig.me/ip",
    "https://api.myip.com"
]

# Lists to store working and found proxies, and a set to track used proxies
working_proxies = []
found_proxies = []
used_proxies = set()

# Regex patterns to identify proxies with authentication
proxy_auth_patterns = [
    re.compile(r"(\w+:\w+@(?:\d{1,3}\.){3}\d{1,3}:\d{2,5})"),
    re.compile(r"(socks5:\/\/\w+:\w+@(?:\d{1,3}\.){3}\d{1,3}:\d{2,5})"),
    re.compile(r"(https?:\/\/\w+:\w+@(?:\d{1,3}\.){3}\d{1,3}:\d{2,5})")
]

# Search function for Google
def search_google(query):
    url = f"{search_engines['google']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(2, 5))  # Random delay to mimic human behavior
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if "url?q=" in href and not "webcache" in href:
                actual_url = href.split("?q=")[1].split("&sa=U")[0]
                links.append(actual_url)
        print(Fore.CYAN + f"Google search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        print(Fore.RED + f"Error searching Google for '{query}': {e}")
        return []

# Search function for Bing
def search_bing(query):
    url = f"{search_engines['bing']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(2, 5))
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith("http") and "bing.com" not in href:
                links.append(href)
        print(Fore.CYAN + f"Bing search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        print(Fore.RED + f"Error searching Bing for '{query}': {e}")
        return []

# Search function for DuckDuckGo
def search_duckduckgo(query):
    url = f"{search_engines['duckduckgo']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(2, 5))
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith("http") and "duckduckgo.com" not in href:
                links.append(href)
        print(Fore.CYAN + f"DuckDuckGo search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        print(Fore.RED + f"Error searching DuckDuckGo for '{query}': {e}")
        return []

# Search function for Yandex
def search_yandex(query):
    url = f"{search_engines['yandex']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(2, 5))
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith("http") and "yandex.com" not in href:
                links.append(href)
        print(Fore.CYAN + f"Yandex search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        print(Fore.RED + f"Error searching Yandex for '{query}': {e}")
        return []

# Search function for You.com
def search_you(query):
    url = f"{search_engines['you']}{requests.utils.quote(query)}"
    headers = {"User-Agent": ua.random}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        time.sleep(random.uniform(2, 5))
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            # You.com might have different URL patterns, adjust as needed
            if href.startswith("http") and "you.com" not in href:
                links.append(href)
        print(Fore.CYAN + f"You.com search for '{query}' returned {len(links)} links.")
        return links
    except Exception as e:
        print(Fore.RED + f"Error searching You.com for '{query}': {e}")
        return []

# Search functions for AI-based search engines
def search_ai_engine(query, engine_name, api_key):
    """
    Implement search using AI-based search engines like Perplexity AI and You.com
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
            print(Fore.CYAN + f"Perplexity AI search for '{query}' returned {len(links)} links.")
            return links
        except Exception as e:
            print(Fore.RED + f"Error searching Perplexity for '{query}': {e}")
            return []
    elif engine_name.lower() == "you.com":
        return search_you(query)
    else:
        print(Fore.YELLOW + f"Unknown AI search engine: {engine_name}")
        return []

# Comprehensive search function to delegate to specific search functions
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
            print(Fore.YELLOW + f"No API key provided for AI search engine: {engine}. Skipping.")
            return []
    else:
        return []

# Function to extract proxies from a given link
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

# Function to test if a proxy is working
def test_proxy(proxy):
    proxy_auth_pattern = re.compile(r"(\w+):(\w+)@((?:\d{1,3}\.){3}\d{1,3}:\d{2,5})")
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

# Function to perform search with specified depth
def search_unit(engine, query, max_depth=3, api_key=None):
    global stop_flag
    print(Fore.CYAN + f"[*] Starting search on {engine} for query: '{query}' with depth {max_depth}")
    depth = 0
    current_links = perform_search(engine, query, api_key)
    all_extracted_proxies = []
    
    while depth < max_depth and not stop_flag:
        depth += 1
        print(Fore.MAGENTA + f"[+] {engine} - Depth {depth}/{max_depth} for query: '{query}'")
        new_links = []
        
        # Extract proxies from current links
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(fetch_proxies_from_link, current_links)
            for proxies in results:
                all_extracted_proxies.extend(proxies)
        
        # Extract new links for deeper search
        for link in current_links:
            try:
                response = requests.get(link, headers={"User-Agent": ua.random}, timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")
                for sublink in soup.find_all('a', href=True):
                    href = sublink['href']
                    if href.startswith("http") and engine not in href and href not in used_proxies:
                        new_links.append(href)
            except Exception as e:
                print(Fore.RED + f"Error fetching sub-links from {link}: {e}")
        
        current_links = new_links
        # Random delay to prevent being blocked
        time.sleep(random.uniform(1, 3))
    
    with lock:
        found_proxies.extend(all_extracted_proxies)
    print(Fore.YELLOW + f"[!] Completed search on {engine} for query: '{query}'. Found {len(all_extracted_proxies)} proxies.")
    return all_extracted_proxies

# Function to listen for stop signal (two Enter presses)
def listen_for_stop():
    global stop_flag
    enter_count = 0
    print(Fore.YELLOW + "برای توقف اسکریپت، دو بار Enter را فشار دهید.")
    while not stop_flag:
        user_input = input()
        if user_input == '':
            enter_count += 1
            if enter_count >= 2:
                stop_flag = True
                print(Fore.YELLOW + "درخواست توقف دریافت شد. متوقف شدن اسکریپت...")
        else:
            enter_count = 0

# Main function to orchestrate the scraping process
def main():
    global stop_flag
    print(Fore.BLUE + "=== Proxy Scraper Start ===")
    print("Generating search terms...")
    search_terms = generate_search_terms()
    
    # Get API keys for AI-based search engines from user
    api_keys = {}
    print("\nPlease enter API keys for AI-based search engines. Leave blank to skip.")
    for engine in ["perplexity", "you"]:
        key = input(f"Enter API key for {engine.capitalize()} (or press Enter to skip): ").strip()
        if key:
            api_keys[engine] = key
    
    # Start thread to listen for stop signal
    listener_thread = threading.Thread(target=listen_for_stop, daemon=True)
    listener_thread.start()
    
    cycle = 1
    while not stop_flag:
        print(Fore.BLUE + f"\n=== Starting Search Cycle {cycle} ===")
        all_proxies = []
        
        # Perform parallel searches across all search engines and search terms
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for engine, query in product(search_engines.keys(), search_terms):
                futures.append(executor.submit(search_unit, engine, query, max_depth=3, api_key=api_keys.get(engine.lower())))
            # Add AI-based search engines if API keys are provided
            for engine, query in product(["perplexity", "you"], search_terms):
                if engine in api_keys:
                    futures.append(executor.submit(search_unit, engine, query, max_depth=3, api_key=api_keys.get(engine.lower())))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    proxies = future.result()
                    # All found proxies are already stored in 'found_proxies'
                except Exception as e:
                    print(Fore.RED + f"Search unit encountered an error: {e}")
        
        if stop_flag:
            break
        
        # Remove duplicates
        unique_proxies = list(set(found_proxies))
        print(Fore.YELLOW + f"[!] Total unique proxies found: {len(unique_proxies)}")
        
        # Test the extracted proxies
        print(Fore.BLUE + f"[+] Testing {len(unique_proxies)} extracted proxies...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(test_proxy, unique_proxies)
            for proxy in results:
                if proxy:
                    with lock:
                        working_proxies.append(proxy)
        
        print(Fore.GREEN + f"[+] Total working proxies: {len(working_proxies)}")
        
        # Save working proxies to file
        with open("working_premium_proxies_with_auth.txt", "a") as f:
            for proxy in working_proxies:
                f.write(f"socks5://{proxy}\n")
        
        print(Fore.CYAN + "Working proxies have been saved to 'working_premium_proxies_with_auth.txt'.")
        
        # Clear the list for the next cycle
        found_proxies.clear()
        
        # Increment the cycle count
        cycle += 1
        
        # Delay before the next search cycle
        print(Fore.BLUE + "Waiting before starting the next cycle...")
        for _ in range(random.randint(300, 600)):
            if stop_flag:
                break
            time.sleep(1)
    
    # After stopping, print the collected working proxies
    print(Fore.GREEN + "\n=== Scraping Stopped ===")
    print(Fore.GREEN + f"Total working proxies collected: {len(working_proxies)}")
    print(Fore.GREEN + "Proxies:")
    for proxy in working_proxies:
        print(proxy)

if __name__ == "__main__":
    main()
