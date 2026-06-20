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
        print("System Prompt:")
        # In Agno, we can access the system prompt after building the message history
        # Let's print the default system instructions
        print(repository_agent.instructions)
        # Let's see if we can get the actual generated system prompt
        print(repository_agent.get_system_prompt())

if __name__ == "__main__":
    asyncio.run(main())
