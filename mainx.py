import asyncio
import ssl
import json
import time
import uuid
import random
import sys
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent

# تنظیمات لاگ
logger.add("debug.log", level="DEBUG")

# ایجاد یک شیء UserAgent برای تولید User-Agent تصادفی
ua = UserAgent()

# فهرستی از سیستم‌عامل‌ها و مرورگرها برای شبیه‌سازی
OPERATING_SYSTEMS = [
    "Windows NT 10.0; Win64; x64",
    "Macintosh; Intel Mac OS X 10_15_7",
    "X11; Linux x86_64"
]

BROWSERS = [
    "Chrome/90.0.4430.93",
    "Firefox/88.0",
    "Safari/14.0.3"
]

async def async_input(prompt: str, timeout: float):
    """
    تابعی برای دریافت ورودی کاربر به صورت غیرهمزمان با تایم‌اوت.
    اگر کاربر ظرف timeout ثانیه پاسخی ندهد، تابع TimeoutError می‌اندازد.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: input(prompt))

async def get_loop_count():
    """
    دریافت تعداد حلقه‌ها از کاربر با قابلیت تایم‌اوت.
    اگر کاربر ظرف ده ثانیه پاسخی ندهد، مقدار None برمی‌گرداند.
    """
    try:
        user_input = await asyncio.wait_for(
            async_input("لطفاً تعداد تلاش‌ها را وارد کنید (در صورت خالی بودن، حلقه بی‌نهایت ادامه خواهد یافت): ", 10.0),
            timeout=10.0
        )
        user_input = user_input.strip()
        if user_input:
            loop_count = int(user_input)
            if loop_count < 1:
                raise ValueError("تعداد حلقه باید حداقل 1 باشد.")
            return loop_count
        else:
            return None
    except asyncio.TimeoutError:
        logger.info("زمان تایم‌اوت به پایان رسید. ادامه دادن به صورت بی‌نهایت.")
        return None
    except ValueError as ve:
        logger.error(f"ورودی نامعتبر: {ve}")
        return None

def generate_device_fingerprint():
    """
    تولید فنگرپرینت منحصر به فرد برای هر دستگاه.
    شامل browser_id، device_id، و سایر پارامترهای مرتبط.
    """
    browser_id = str(uuid.uuid4())
    device_id = str(uuid.uuid4())
    os = random.choice(OPERATING_SYSTEMS)
    browser = random.choice(BROWSERS)
    user_agent = f"Mozilla/5.0 ({os}) AppleWebKit/537.36 (KHTML, like Gecko) {browser} Safari/537.36"
    return browser_id, device_id, user_agent

async def connect_to_wss(socks5_proxy, user_id, loop_count):
    device_fingerprint = generate_device_fingerprint()
    browser_id, device_id, user_agent = device_fingerprint
    logger.info(f"Device ID: {device_id}, Browser ID: {browser_id}, User-Agent: {user_agent}")

    attempt = 0
    while True:
        if loop_count is not None and attempt >= loop_count:
            logger.info(f"تعداد تلاش‌ها به حد اکثر {loop_count} رسیده است. متوقف کردن تلاش‌ها برای این پروکسی و user_id.")
            break
        attempt += 1
        try:
            logger.info(f"Attempt {attempt} for proxy: {socks5_proxy}, user_id: {user_id}")
            custom_headers = {
                "User-Agent": user_agent,
                "Origin": "https://example.com",  # جایگزین با مقدار مناسب
                "Referer": "https://example.com"  # جایگزین با مقدار مناسب
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE  # فقط برای تست، در محیط تولید این را فعال کنید
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)

            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                logger.info("Connected to WebSocket server.")

                # دریافت اولین پیام از سرور
                response = await websocket.recv()
                message = json.loads(response)
                logger.info(f"Received message: {message}")

                if message.get("action") == "AUTH":
                    # ساختن یک پاسخ AUTH
                    auth_response = {
                        "id": message["id"],
                        "origin_action": "AUTH",
                        "result": {
                            "browser_id": browser_id,
                            "user_id": user_id,
                            "user_agent": user_agent,
                            "timestamp": int(time.time()),  # استفاده از timestamp صحیح
                            "device_type": "extension",
                            "version": "4.0.2"
                        }
                    }
                    logger.debug(f"Sending AUTH response: {auth_response}")
                    await websocket.send(json.dumps(auth_response))
                    logger.info("AUTH response sent.")

                    # انتظار دریافت پاسخ از سرور پس از AUTH
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"Received message after AUTH: {message}")

                    # بررسی وضعیت احراز هویت
                    if "error" in message:
                        logger.error(f"Authentication failed: {message['error']}")
                        if 'code' in message and message['code'] == 4000:
                            logger.error("خطای 4000 دریافت شد. قطع تلاش‌ها برای این پروکسی و user_id.")
                            break  # خروج از حلقه در صورت بروز خطای 4000
                    else:
                        logger.info("Authentication successful.")
                        # اگر احراز هویت موفقیت‌آمیز بود، می‌توانید عملیات دیگری انجام دهید یا حلقه را ادامه دهید
                        break  # خروج از حلقه پس از موفقیت

        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"ConnectionClosedError on attempt {attempt}: {e}")
            if hasattr(e, 'code') and e.code == 4000:
                logger.error("Received error 4000 during authentication. Stopping attempts for this proxy-user_id.")
                break  # خروج از حلقه در صورت بروز خطای 4000
            await asyncio.sleep(random.uniform(5, 10))  # تاخیر تصادفی 5 تا 10 ثانیه قبل از تلاش مجدد
        except Exception as e:
            logger.error(f"Error on attempt {attempt}: {e}")
            logger.error(f"Proxy: {socks5_proxy}")
            await asyncio.sleep(random.uniform(5, 10))  # تاخیر تصادفی 5 تا 10 ثانیه قبل از تلاش مجدد

async def main():
    # دریافت تعداد حلقه‌ها از کاربر با تایم‌اوت
    loop_count = await get_loop_count()

    # خواندن user_id از فایل
    try:
        with open('user_id.txt', 'r') as file:
            user_ids = file.read().splitlines()
    except FileNotFoundError:
        logger.error("فایل user_id.txt پیدا نشد.")
        return

    if not user_ids:
        logger.error("هیچ user_id ای در فایل user_id.txt پیدا نشد.")
        return

    # خواندن پروکسی‌ها از فایل
    try:
        with open('proxy.txt', 'r') as file:
            proxies = file.read().splitlines()
    except FileNotFoundError:
        logger.error("فایل proxy.txt پیدا نشد.")
        return

    if not proxies:
        logger.error("هیچ پروکسی ای در فایل proxy.txt پیدا نشد.")
        return

    # ایجاد تسک برای هر ترکیب پروکسی و user_id
    tasks = []
    for proxy in proxies:
        for user_id in user_ids:
            tasks.append(asyncio.create_task(connect_to_wss(proxy, user_id, loop_count)))

    # اجرای تسک‌ها به صورت همزمان
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("برنامه توسط کاربر متوقف شد.")
        sys.exit()
