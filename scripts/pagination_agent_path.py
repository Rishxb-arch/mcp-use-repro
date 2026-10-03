"""What does the LangChain adapter (the path MCPAgent uses) hand the LLM for a paginated server?"""
import asyncio, logging, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
async def main():
    from mcp_use import MCPClient
    from mcp_use.agents.adapters import LangChainAdapter
    c = MCPClient({"mcpServers": {"edge": {"url": "http://127.0.0.1:8765/mcp/"}}})
    tools = await LangChainAdapter().create_tools(c)
    print("tools the agent would see:", sorted(t.name for t in tools), "(server exposes tool_00..tool_06)")
    await c.close_all_sessions()
asyncio.run(main())
