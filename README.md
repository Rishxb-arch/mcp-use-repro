# mcp-use-repro: the Python client reads only the first page of `tools/list`

Hands-on test of the **mcp-use Python client** (`mcp-use` 1.7.1, repo commit `1e14ac9`, 2 Oct 2026) against spec-edge MCP servers built with the reference `mcp` SDK, compared with the reference SDK itself and with mcp-use's own TypeScript client. Run on 2026-10-03 on Linux (CPU only, Python 3.12.14, Node 22.23). Everything here is reproducible with `./run_all.sh`; the logs in `logs/` are the output of that run.

## Headline finding

MCP lets a server paginate `tools/list`, `resources/list`, `resources/templates/list` and `prompts/list` (`nextCursor`). The Python client calls each of them once and drops `nextCursor`, so anything after page 1 is silently missing, including in the list `MCPAgent` hands the LLM.

Server with 7 tools / 5 resources / 5 prompts, page size 2 (`scripts/edge_server.py`, built on the reference SDK):

| client | tools seen |
|---|---|
| reference `mcp` 1.30.0 `ClientSession.list_tools()` (first call) | 2 (caller must follow `nextCursor`; the loop gives 7) |
| **mcp-use Python 1.7.1** `session.list_tools()` | **2 of 7** |
| **mcp-use Python 1.7.1** via `LangChainAdapter.create_tools()` (the `MCPAgent` path) | **2 of 7** (`tool_00`, `tool_01`) |
| mcp-use TypeScript `@mcp-use/client` 2.4.0 | 7 of 7 |

Same result for resources (2 of 5) and prompts (2 of 5), and with the server in stateless/JSON mode (`logs/pagination_probe_stateless_json.out`). Nothing is logged, so the agent just has fewer tools than the server has.

Where: `libraries/python/mcp_use/client/connectors/base.py` (`initialize()` and `list_tools/list_resources/list_prompts()`) and the second copy of `initialize()` in `connectors/http.py` call `client_session.list_*()` with no cursor.

Why I believe it is not already reported: I searched the issue tracker (open and closed) on 2026-10-03. Tool-list pagination is covered only for the TypeScript client (#2460, #2489, #2470; the TS client does paginate today). I found no Python issue or PR.

Reproduce: `logs/pagination_probe.out`, `logs/pagination_agent_path.out`, `logs/pagination_probe_ts.out`.

## Smaller things seen (same run, lower confidence / lower impact)

1. **`additionalProperties` is dropped by the LangChain adapter.** A tool with `inputSchema = {"type":"object","additionalProperties":{"type":"integer"}}` is called with `{"k": 1}` and the server receives `{}`. `jsonschema_pydantic.jsonschema_to_pydantic` builds a model that ignores extra keys, and the adapter uses it as `args_schema`. Same when the schema also declares `properties` plus `additionalProperties: true` (the extra key is dropped). See `logs/schema_probe.out`, line `additional`. I found no existing issue.
2. **A server that loses the session is never recovered from.** After the server restarts, the old `Mcp-Session-Id` gets a 404 and every later call fails with `McpError: Session terminated` (`logs/session_expiry_probe.out`). The reference Python SDK behaves identically, so this is parity, not a regression, but the spec says a client MUST start a new session on 404, and `BaseConnector` has `auto_reconnect` logic that never triggers here because `is_connected` stays true. Not patched.
3. Result handling oddities, low severity: a result with only `structuredContent` (empty `content`) becomes `''` through the adapter; a `resource_link` content block is returned as a Python repr string. (Related to the closed #1604.)

Worked as expected (so you know what was covered): `$defs`/`$ref`, `anyOf` with `null`, `type: ["string","null"]`, `oneOf`, `enum`/`const`, `$schema` 2020-12, property names with `-` and `.`, tool results with `isError`, `structuredContent`, image and embedded-resource blocks, empty content. All 16 tools were created by the adapter and the 9 schema cases were called successfully except item 1.

## Versions

- mcp-use (Python) 1.7.1 at commit `1e14ac9dff03e378853f1546531004d079806c6c` (main, 2026-10-02)
- reference `mcp` 1.30.0 (Python); `@modelcontextprotocol/sdk` 1.32.0 (TS reference); `@mcp-use/client` 2.4.0 (uses `@modelcontextprotocol/client` 2.0.0)
- Python 3.12.14, Node v22.23.3, Linux x86-64, no GPU

## Not tested (limitations)

- OAuth / auth discovery, SSE fallback, `tools/list_changed` refresh, sampling / elicitation / roots, stdio and websocket transports (they share the same `BaseConnector.initialize()` code, but I only exercised streamable HTTP for pagination), Windows/macOS.
- The pagination server is synthetic (reference SDK low-level server with page size 2). I did not check which popular public servers paginate.
- Only the `LangChainAdapter` path was exercised for the agent side; no LLM was called.

## Patches

See `patches/`. They are untested against the upstream CI.

`0001` follows `nextCursor` for `tools/list`, `resources/list`, and `prompts/list`. `0002` keeps `additionalProperties` keys on the LangChain adapter's `args_schema`. Fork branch (no pull request): https://github.com/Rishxb-arch/mcp-use/tree/python-paginate-list-results

## Files

- `scripts/edge_server.py` paginated, spec-valid server (streamable HTTP; `--stateless`, `--json`)
- `scripts/pagination_probe.py`, `pagination_agent_path.py`, `session_expiry_probe.py`, `schema_server.py` + `schema_probe.py`
- `ts-probe/probe.mjs` TypeScript comparison
- `logs/` output of each run
