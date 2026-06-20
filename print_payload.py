import asyncio
import os
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from agno.models.groq import Groq
from mcp import StdioServerParameters

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
        repository_agent = Agent(
            model=Groq(id="llama-3.3-70b-versatile"),
            tools=[tools_interface],
        )
        
        # Get the tools in the format sent to the model
        model_tools = repository_agent.get_tools_for_api()
        print("Tools sent to model API:")
        print(model_tools)

if __name__ == "__main__":
    asyncio.run(main())
