import asyncio
import os
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters
import json

async def main():
    server_configuration = StdioServerParameters(
        command="npx.cmd",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={
            **os.environ,
            "GITHUB_PERSONAL_ACCESS_TOKEN": "dummy"
        }
    )
    
    async with MCPTools(server_params=server_configuration) as tools_interface:
        print("MCPTools class:")
        print(tools_interface.__class__)
        print("\nAvailable tools in toolkit:")
        # In Agno, Toolkit has a `tools` list
        for t in tools_interface.tools:
            print(f"- Name: {t.__name__ if hasattr(t, '__name__') else getattr(t, 'name', str(t))}")
            # print tool details
            print(f"  Docstring: {t.__doc__}")

if __name__ == "__main__":
    asyncio.run(main())
