import asyncio, logging, warnings, json, sys
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
async def main():
    from mcp_use import MCPClient
    from mcp_use.agents.adapters import LangChainAdapter
    c = MCPClient({"mcpServers": {"s": {"command": sys.executable, "args": ["scripts/schema_server.py"]}}})
    tools = await LangChainAdapter().create_tools(c)
    byname = {t.name: t for t in tools}
    print("adapter produced", len(tools), "of 16 tools; missing:", sorted(set(["nullable_union","type_array","defs_ref","enum_const","oneof","additional","no_props","dollar_schema_2020","dotted_hyphen_name","res_iserror","res_structured","res_structured_only","res_image","res_empty","res_link","res_embedded"]) - set(byname)))
    calls = {"nullable_union":{"q":None},"type_array":{"q":None},"defs_ref":{"a":{"x":1,"y":2},"pts":[{"x":0,"y":0}]},"enum_const":{"mode":"fast","v":3},
             "oneof":{"u":"s"},"additional":{"k":1},"no_props":{},"dollar_schema_2020":{"n":2},"dotted_hyphen_name":{"user-id":"u1","a.b":"z"}}
    for n,a in calls.items():
        if n not in byname: print(f"{n:22s} NOT PRODUCED"); continue
        try:
            out = await byname[n].ainvoke(a); print(f"{n:22s} OK  -> {str(out)[:90]!r}")
        except BaseException as e: print(f"{n:22s} FAIL -> {type(e).__name__}: {str(e)[:150]!r}")
    for n in ["res_iserror","res_structured","res_structured_only","res_image","res_empty","res_link","res_embedded"]:
        if n not in byname: print(f"{n:22s} NOT PRODUCED"); continue
        try:
            out = await byname[n].ainvoke({}); print(f"{n:22s} -> {str(out)[:110]!r}")
        except BaseException as e: print(f"{n:22s} RAISED {type(e).__name__}: {str(e)[:110]!r}")
    await c.close_all_sessions()
asyncio.run(main())
