import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent

user_agent = UserAgent()
random_user_agent = user_agent.random

async def connect_to_wss(socks5_proxy, user_id):
    device_id = str(uuid.uuid4())  # استفاده از UUID4
    logger.info(f"Device ID: {device_id}")

    while True:
        try:
            await asyncio.sleep(random.uniform(0.1, 1))  # تاخیر تصادفی بین 0.1 تا 1 ثانیه
            custom_headers = {
                "User-Agent": random_user_agent,
                "Origin": "https://your-origin.com",  # جایگزین با مقدار مناسب
                "Referer": "https://your-referer.com"  # جایگزین با مقدار مناسب
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE  # فقط برای تست، در محیط تولید این را فعال کنید
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)

            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(f"Sending PING: {send_message}")
                        await websocket.send(send_message)
                        await asyncio.sleep(20)

                # ارسال پیام PING به صورت دوره‌ای
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"Received message: {message}")

                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),  # استفاده از timestamp صحیح
                                "device_type": "extension",
                                "version": "4.0.2"
                            }
                        }
                        logger.debug(f"Sending AUTH response: {auth_response}")
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(f"Sending PONG response: {pong_response}")
                        await websocket.send(json.dumps(pong_response))

        except Exception as e:
            logger.error(f"Error: {e}")
            logger.error(f"Proxy: {socks5_proxy}")
            await asyncio.sleep(5)  # تاخیر قبل از تلاش مجدد

async def main():
    # خواندن user_id از فایل
    with open('user_id.txt', 'r') as file:
        user_ids = file.read().splitlines()

    if not user_ids:
        logger.error("No user_id found in user_id.txt")
        return

    # خواندن پروکسی‌ها از فایل
    with open('proxy.txt', 'r') as file:
        proxies = file.read().splitlines()

    if not proxies:
        logger.error("No proxies found in proxy.txt")
        return

    # ایجاد تسک برای هر ترکیب پروکسی و user_id
    tasks = []
    for proxy in proxies:
        for user_id in user_ids:
            tasks.append(asyncio.ensure_future(connect_to_wss(proxy, user_id)))

    # اجرای تسک‌ها به صورت همزمان
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    # تنظیمات لاگ
    logger.add("debug.log", level="DEBUG")
    asyncio.run(main())

