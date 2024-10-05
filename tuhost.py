import asyncio
import websockets
import json
import uuid
import time

async def test_ws():
    uri = "wss://proxy.wynd.network:4650/"
    
    # خواندن user_id از فایل
    with open('user_id.txt', 'r') as file:
        user_ids = file.read().splitlines()
    
    # استفاده از اولین user_id در فایل
    if not user_ids:
        print("No user_id found in user_id.txt")
        return
    
    user_id = user_ids[0]
    device_id = str(uuid.uuid4())  # ساخت یک Device ID تصادفی
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, مثل Gecko) Chrome/85.0.4183.121 Safari/537.36"

    async with websockets.connect(uri) as websocket:
        while True:
            response = await websocket.recv()
            message = json.loads(response)
            print(f"Received message: {message}")

            # چک کردن پیام AUTH
            if message.get("action") == "AUTH":
                # ساختن یک پاسخ AUTH
                auth_response = {
                    "id": message["id"],
                    "origin_action": "AUTH",
                    "result": {
                        "browser_id": device_id,
                        "user_id": user_id,
                        "user_agent": user_agent,
                        "timestamp": int(time.time()),
                        "device_type": "extension",
                        "version": "4.0.2"
                    }
                }
                print(f"Sending AUTH response: {auth_response}")
                await websocket.send(json.dumps(auth_response))

asyncio.run(test_ws())
