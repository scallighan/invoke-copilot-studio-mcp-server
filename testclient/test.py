import asyncio
from fastmcp import Client

client = Client("http://localhost:8000/mcp", auth="oauth")

async def call_tool(name: str):
    async with client:
        result = await client.call_tool("get_user_info", {})
        print("User Info:", result)
        result = await client.call_tool("invoke", {"query": name})
        print(result)

asyncio.run(call_tool("How can I create an Azure Container app?"))