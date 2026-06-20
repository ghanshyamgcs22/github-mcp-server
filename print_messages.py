import asyncio
import os
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from agno.models.groq import Groq
from mcp import StdioServerParameters

class DebugGroq(Groq):
    def invoke(self, messages, *args, **kwargs):
        print("\n=== SYSTEM PROMPT / MESSAGES SENT TO GROQ (sync) ===")
        for msg in messages:
            print(f"Role: {msg.role}")
            print(f"Content:\n{msg.content}\n")
            print("-" * 40)
        return super().invoke(messages, *args, **kwargs)

    async def ainvoke(self, messages, *args, **kwargs):
        print("\n=== SYSTEM PROMPT / MESSAGES SENT TO GROQ (async) ===")
        for msg in messages:
            print(f"Role: {msg.role}")
            print(f"Content:\n{msg.content}\n")
            print("-" * 40)
        return await super().ainvoke(messages, *args, **kwargs)

async def main():
    # Set GROQ_API_KEY environment variable before running
    # os.environ["GROQ_API_KEY"] = "your-groq-api-key-here"
    
    server_configuration = StdioServerParameters(
        command="npx.cmd",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={
            **os.environ,
            "GITHUB_PERSONAL_ACCESS_TOKEN": os.environ.get("GITHUB_TOKEN", "")
        }
    )
    
    async with MCPTools(server_params=server_configuration) as tools_interface:
        repository_agent = Agent(
            model=DebugGroq(id="llama-3.3-70b-versatile"),
            tools=[tools_interface],
            instructions="Analyze the repository.",
            markdown=True,
        )
        prompt = "tell me about the readme file in ghanshyamgcs22/ifms-frontend-nitj"
        try:
            await repository_agent.arun(prompt)
        except Exception as e:
            print(f"Error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
