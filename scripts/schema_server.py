"""Raw low-level server exposing hand-written spec-valid JSON Schemas + varied tool results."""
import asyncio, base64, json, sys
import mcp.types as t
from mcp.server.lowlevel import Server
import mcp.server.stdio

S = {
 "nullable_union": {"type":"object","properties":{"q":{"anyOf":[{"type":"string"},{"type":"null"}]}},"required":["q"]},
 "type_array": {"type":"object","properties":{"q":{"type":["string","null"]}}},
 "defs_ref": {"type":"object","$defs":{"Pt":{"type":"object","properties":{"x":{"type":"number"},"y":{"type":"number"}},"required":["x","y"]}},
              "properties":{"a":{"$ref":"#/$defs/Pt"},"pts":{"type":"array","items":{"$ref":"#/$defs/Pt"}}},"required":["a"]},
 "enum_const": {"type":"object","properties":{"mode":{"enum":["fast","slow"]},"v":{"const":3}},"required":["mode"]},
 "oneof": {"type":"object","properties":{"u":{"oneOf":[{"type":"integer"},{"type":"string"}]}},"required":["u"]},
 "additional": {"type":"object","additionalProperties":{"type":"integer"}},
 "no_props": {"type":"object"},
 "dollar_schema_2020": {"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","properties":{"n":{"type":"integer","minimum":1,"maximum":5}},"required":["n"]},
 "dotted_hyphen_name": {"type":"object","properties":{"user-id":{"type":"string"},"a.b":{"type":"string"}}},
}
RES = {
 "res_iserror": lambda a: t.CallToolResult(content=[t.TextContent(type="text",text="boom: bad input")], isError=True),
 "res_structured": lambda a: t.CallToolResult(content=[t.TextContent(type="text",text="{\"ok\": true}")], structuredContent={"ok": True,"n":3}),
 "res_structured_only": lambda a: t.CallToolResult(content=[], structuredContent={"ok": True,"n":3}),
 "res_image": lambda a: t.CallToolResult(content=[t.TextContent(type="text",text="here"),t.ImageContent(type="image",data=base64.b64encode(b"x"*10).decode(),mimeType="image/png")]),
 "res_empty": lambda a: t.CallToolResult(content=[]),
 "res_link": lambda a: t.CallToolResult(content=[t.ResourceLink(type="resource_link",uri="file:///x.txt",name="x")]),
 "res_embedded": lambda a: t.CallToolResult(content=[t.EmbeddedResource(type="resource",resource=t.TextResourceContents(uri="file:///x.txt",text="embedded text"))]),
}
srv = Server("schema-server")
@srv.list_tools()
async def _lt():
    return [t.Tool(name=k, description=k, inputSchema=v) for k,v in S.items()] + [t.Tool(name=k, description=k, inputSchema={"type":"object"}) for k in RES]
@srv.call_tool(validate_input=False)
async def _ct(name, arguments):
    if name in RES: return RES[name](arguments)
    return [t.TextContent(type="text", text=f"{name} got {json.dumps(arguments)}")]
async def main():
    async with mcp.server.stdio.stdio_server() as (r, w):
        await srv.run(r, w, srv.create_initialization_options())
asyncio.run(main())
