"""Server loses the session (restart => unknown Mcp-Session-Id => HTTP 404). Spec: client MUST start a new session
(send a fresh InitializeRequest without a session id). Compare reference mcp ClientSession vs mcp-use."""
import asyncio, subprocess, sys, logging, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
URL = "http://127.0.0.1:8765/mcp/"
def restart(): subprocess.run(["scripts/srv.sh", "start", "8765"], check=True)

async def ref():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    async with streamablehttp_client(URL) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize(); print("  ref: call before restart ok:", (await s.call_tool("tool_00", {})).content[0].text)
            restart()
            try: print("  ref: call after restart:", (await asyncio.wait_for(s.call_tool("tool_00", {}), 15)).content[0].text)
            except BaseException as e: print("  ref: call after restart FAILED:", type(e).__name__, str(e)[:120])

async def mcpuse():
    from mcp_use import MCPClient
    c = MCPClient({"mcpServers": {"edge": {"url": URL}}})
    await c.create_all_sessions(); s = c.get_session("edge")
    print("  mcp-use: call before restart ok:", (await s.call_tool("tool_00", {})).content[0].text)
    restart()
    for i in (1, 2):
        try: print(f"  mcp-use: call #{i} after restart:", (await asyncio.wait_for(s.call_tool("tool_00", {}), 15)).content[0].text)
        except BaseException as e: print(f"  mcp-use: call #{i} after restart FAILED:", type(e).__name__, str(e)[:160])
    try: await asyncio.wait_for(c.close_all_sessions(), 10)
    except BaseException as e: print("  close failed:", type(e).__name__)

async def main():
    print("reference SDK:"); await ref()
    print("mcp-use:"); await mcpuse()
asyncio.run(main())
