"""Compare how many items the reference `mcp` ClientSession (manual cursor loop) vs mcp-use's Python client see
from an MCP server that paginates list results (page size 2). Server: edge_server.py."""
import asyncio, sys, logging, warnings
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765/mcp/"

async def ref():
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    out = {}
    async with streamablehttp_client(URL) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for kind, fn, attr in [("tools", s.list_tools, "tools"), ("resources", s.list_resources, "resources"),
                                   ("templates", s.list_resource_templates, "resourceTemplates"), ("prompts", s.list_prompts, "prompts")]:
                first = await fn(); n = len(getattr(first, attr)); cur = first.nextCursor; total = n
                while cur:
                    p = await fn(cursor=cur); total += len(getattr(p, attr)); cur = p.nextCursor
                out[kind] = (n, total)
    return out

async def mcpuse():
    from mcp_use import MCPClient
    c = MCPClient({"mcpServers": {"edge": {"url": URL}}})
    await c.create_all_sessions()
    s = c.get_session("edge")
    out = {}
    out["tools"] = len(await s.list_tools())
    out["resources"] = len(await s.list_resources())
    out["prompts"] = len(await s.list_prompts())
    try:
        out["templates"] = len(await s.connector.client_session.list_resource_templates().resourceTemplates)
    except Exception: pass
    await c.close_all_sessions()
    return out

async def main():
    import mcp, mcp_use, importlib.metadata as m
    print("mcp", m.version("mcp"), "mcp-use", mcp_use.__version__)
    r = await ref(); print("reference SDK (first page, all pages):", r)
    print("mcp-use list_tools/list_resources/list_prompts:", await mcpuse())
    print("server really has: tools=7 resources=5 resource_templates=5 prompts=5")
asyncio.run(main())
