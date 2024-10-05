import asyncio
import random
import ssl
import json
import time
import uuid
import os
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent

user_agent = UserAgent()
random_user_agent = user_agent.random


async def connect_to_wss(socks5_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(20)

                # asyncio.create_task(send_http_request_every_10_seconds(socks5_proxy, device_id))
                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)
                    if message.get("action") == "AUTH":
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
                        logger.debug(auth_response)
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(pong_response)
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
            logger.error(e)
            logger.error(socks5_proxy)


async def main():
    # پیدا کردن مسیر پویا برای فایل‌ها
    base_path = '/content/getgrass'

    user_id_path = os.path.join(base_path, 'user_id.txt')
    proxy_path = os.path.join(base_path, 'proxy.txt')

    # خواندن یوزر آی‌دی‌ها از فایل
    with open(user_id_path, 'r') as file:
        user_ids = file.read().splitlines()
        
    # خواندن پروکسی‌ها از فایل
    with open(proxy_path, 'r') as file:
        proxies = file.read().splitlines()
    
    # ایجاد تسک‌ها برای هر ترکیب پروکسی و یوزر آی‌دی
    tasks = []
    for proxy in proxies:
        for user_id in user_ids:
            tasks.append(asyncio.ensure_future(connect_to_wss(proxy, user_id)))
    
    # اجرای همزمان تسک‌ها
    await asyncio.gather(*tasks)



if __name__ == '__main__':
    asyncio.run(main())
