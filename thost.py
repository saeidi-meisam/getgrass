import asyncio
import websockets

async def test_ws():
    uri = "wss://proxy.wynd.network:4650/"
    async with websockets.connect(uri) as websocket:
        await websocket.send("test")
        response = await websocket.recv()
        print(response)

asyncio.run(test_ws())
