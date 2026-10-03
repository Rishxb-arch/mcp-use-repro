import { MCPClient } from "@mcp-use/client";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
const URL_ = process.argv[2] ?? "http://127.0.0.1:8765/mcp/";
// reference SDK
const ref = new Client({ name: "ref", version: "1" });
await ref.connect(new StreamableHTTPClientTransport(new URL(URL_)));
let n = 0, cur, first;
do { const r = await ref.listTools(cur ? { cursor: cur } : undefined); first ??= r.tools.length; n += r.tools.length; cur = r.nextCursor } while (cur);
console.log("reference TS SDK: first page", first, "all pages", n);
await ref.close();
// mcp-use TS
const c = new MCPClient({ mcpServers: { edge: { url: URL_ } } });
await c.createAllSessions();
const s = c.getSession("edge");
console.log("@mcp-use/client session.tools (cache):", s.tools.length, " session.listTools():", (await s.listTools()).length);
await c.closeAllSessions();
process.exit(0);
