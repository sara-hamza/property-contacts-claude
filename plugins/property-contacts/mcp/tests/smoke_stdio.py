"""Start the server over stdio exactly as Claude does, check it initialises and lists
its four read-only tools, and check the no-GUID path. No third-party network calls."""
import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parents[1] / "property_data_server.py"
EXPECTED = {"normalise_address", "businesses_at", "abn_search", "abn_details"}


async def main() -> int:
    params = StdioServerParameters(
        command="uv", args=["run", "--quiet", "--script", str(SERVER)],
        env={**os.environ, "ABR_GUID": ""},
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            info = await s.initialize()
            tools = {t.name: t for t in (await s.list_tools()).tools}
            assert set(tools) == EXPECTED, f"tools: {sorted(tools)}"
            assert all(getattr(t.annotations, "read_only_hint", False) for t in tools.values()), "all tools read-only"
            res = json.loads((await s.call_tool("abn_search", {"name": "Example"})).content[0].text)
            assert res["assigned"] is None and "ABR_GUID" in res["error"], res
            res = json.loads((await s.call_tool("abn_details", {"abn": "123"})).content[0].text)
            assert "11 digits" in res["error"], res
            print(f"ok  {info.server_info.name} {info.server_info.version}: {sorted(tools)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
