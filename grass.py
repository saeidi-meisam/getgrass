import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent

# تنظیمات اولیه
user_agent = UserAgent()
random_user_agent = user_agent.random

async def connect_to_wss(socks5_proxy, user_id):
    # ایجاد شناسه دستگاه منحصر به فرد برای هر پراکسی
    device_id = str(uuid.uuid4())  # استفاده از UUID4 برای یکتایی بیشتر
    logger.info(f"Device ID: {device_id} | Proxy: {socks5_proxy}")

    while True:
        try:
            # توقف تصادفی قبل از تلاش برای اتصال
            await asyncio.sleep(random.uniform(0.1, 1.0))
            
            # تنظیم هدرهای سفارشی با User-Agent تصادفی
            custom_headers = {
                "User-Agent": user_agent.random
            }
            
            # تنظیمات SSL با عدم اعتبارسنجی گواهی‌ها
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # URI سرور WebSocket و نام میزبان
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            
            # ایجاد شیء پراکسی از URL پراکسی
            proxy = Proxy.from_url(socks5_proxy)
            
            # اتصال به سرور WebSocket از طریق پراکسی
            async with proxy_connect(
                uri, 
                proxy=proxy, 
                ssl=ssl_context, 
                server_hostname=server_hostname,
                extra_headers=custom_headers
            ) as websocket:
                
                async def send_ping():
                    while True:
                        # ایجاد پیام PING با شناسه منحصر به فرد
                        send_message = json.dumps({
                            "id": str(uuid.uuid4()),
                            "version": "1.0.0",
                            "action": "PING",
                            "data": {}
                        })
                        logger.debug(f"Sending PING: {send_message}")
                        await websocket.send(send_message)
                        # تاخیر تصادفی بین ارسال پیام‌ها
                        await asyncio.sleep(random.uniform(15, 25))
                
                # ایجاد تسک ارسال پینگ به صورت همزمان
                asyncio.create_task(send_ping())
                
                while True:
                    # دریافت پیام از سرور
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"Received message: {message}")
                    
                    if message.get("action") == "AUTH":
                        # پاسخ به درخواست احراز هویت
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "4.0.2"
                            }
                        }
                        logger.debug(f"Sending AUTH response: {auth_response}")
                        await websocket.send(json.dumps(auth_response))
                    
                    elif message.get("action") == "PONG":
                        # پاسخ به پیام PONG دریافتی
                        pong_response = {
                            "id": message["id"],
                            "origin_action": "PONG"
                        }
                        logger.debug(f"Sending PONG response: {pong_response}")
                        await websocket.send(json.dumps(pong_response))
        
        except Exception as e:
            logger.error(f"Error with proxy {socks5_proxy}: {e}")
            # تاخیر قبل از تلاش مجدد برای اتصال
            await asyncio.sleep(random.uniform(5, 15))

async def main():
    # خواندن شناسه‌های کاربری از فایل
    with open('user_id.txt', 'r') as file:
        user_ids = file.read().splitlines()
    
    # خواندن پراکسی‌ها از فایل
    with open('proxy.txt', 'r') as file:
        proxies = file.read().splitlines()
    
    # ایجاد تسک برای هر ترکیب پراکسی و شناسه کاربری
    tasks = []
    for proxy in proxies:
        for user_id in user_ids:
            tasks.append(asyncio.create_task(connect_to_wss(proxy, user_id)))
    
    # اجرای تمام تسک‌ها به صورت همزمان
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    # اجرای حلقه اصلی asyncio
    asyncio.run(main())

