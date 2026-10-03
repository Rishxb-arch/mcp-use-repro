"""Spec-edge MCP server built on the reference `mcp` SDK (low-level Server).

Features (selected by env/args):
  - paginated tools/list, resources/list, prompts/list, resources/templates/list (page size 2, opaque cursors)
  - tools with edge-case schemas
  - tool results: isError, structuredContent, multiple content blocks
Run: python edge_server.py [--port 8765] [--stateless] [--json]
"""
import argparse, contextlib, json
import mcp.types as t
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
import uvicorn

PAGE = 2
TOOLS = [t.Tool(name=f"tool_{i:02d}", description=f"tool {i}", inputSchema={"type": "object", "properties": {"x": {"type": "integer"}}}) for i in range(7)]
RES = [t.Resource(uri=f"file:///r{i}.txt", name=f"r{i}") for i in range(5)]
TPL = [t.ResourceTemplate(uriTemplate=f"file:///t{i}/{{id}}", name=f"t{i}") for i in range(5)]
PROMPTS = [t.Prompt(name=f"p{i}", description=f"prompt {i}") for i in range(5)]

def page(items, cursor):
    import sys; print('LIST', len(items), 'cursor=', repr(cursor), flush=True)
    start = int(cursor) if cursor else 0
    nxt = str(start + PAGE) if start + PAGE < len(items) else None
    return items[start:start + PAGE], nxt

def build():
    s = Server("edge-server")

    @s.list_tools()
    async def _lt(req: t.ListToolsRequest):
        items, nxt = page(TOOLS, req.params.cursor if req.params else None)
        return t.ListToolsResult(tools=items, nextCursor=nxt)

    @s.list_resources()
    async def _lr(req: t.ListResourcesRequest):
        items, nxt = page(RES, req.params.cursor if req.params else None)
        return t.ListResourcesResult(resources=items, nextCursor=nxt)

    async def _lrt(req: t.ListResourceTemplatesRequest):
        items, nxt = page(TPL, req.params.cursor if req.params else None)
        return t.ServerResult(t.ListResourceTemplatesResult(resourceTemplates=items, nextCursor=nxt))
    s.request_handlers[t.ListResourceTemplatesRequest] = _lrt

    @s.list_prompts()
    async def _lp(req: t.ListPromptsRequest):
        items, nxt = page(PROMPTS, req.params.cursor if req.params else None)
        return t.ListPromptsResult(prompts=items, nextCursor=nxt)

    @s.call_tool(validate_input=False)
    async def _ct(name, arguments):
        return [t.TextContent(type="text", text=f"called {name} {json.dumps(arguments)}")]
    return s

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--stateless", action="store_true"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    mgr = StreamableHTTPSessionManager(app=build(), stateless=a.stateless, json_response=a.json)
    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with mgr.run():
            yield
    app = Starlette(routes=[Mount("/mcp", app=mgr.handle_request)], lifespan=lifespan)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
