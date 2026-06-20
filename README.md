# 🐙 Repository Management Assistant

A Streamlit-powered dashboard that enables users to query, audit, and analyze GitHub repositories using natural language commands. The application leverages the Model Context Protocol (MCP) to interface directly with GitHub's APIs.

## Features

- **Natural Language Parsing**: Ask questions about repositories in simple English.
- **Repository Analysis**: Inspect active issues, pull requests, files, and recent commits.
- **Workspace Tool Routing**: Integrates the official GitHub MCP server to securely fetch metrics.
- **Structured Outputs**: Formats data, code quality metrics, and list updates in clean markdown tables.

## System Setup

### Prerequisites

- **Python 3.8+**
- **Node.js**: Used to run the official GitHub MCP Server locally. Ensure Node.js is installed.
- **Groq AI Key**: Used to interpret user queries.
- **GitHub Personal Access Token**: Used to fetch data from target repositories.

### Installation

1. Navigate to this agent's folder:
   ```bash
   cd mcp_integrations_agents/github_mcp_agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure Node.js is installed and running:
   ```bash
   node --version
   ```

4. Retrieve access tokens:
   - **Groq AI Key**: From your [Groq Platform](https://console.groq.com/keys).
   - **GitHub Token**: Create a token at `github.com/settings/tokens` with `repo` scope.

## Launching the Console

1. Run the Streamlit console:
   ```bash
   streamlit run github_agent.py
   ```

2. Inside the dashboard:
   - Provide your Groq AI Key and GitHub Token in the credentials section.
   - Provide your target repository name (e.g., `psf/requests`).
   - Select a query category or type a custom command.
   - Click **Run Query** to view results.

## Sample Prompts

### Issue Audits
- `Find issues matching a specific labels`
- `Retrieve highly discussed issues`

### Pull Request Reviews
- `List PRs awaiting review`
- `Fetch recently completed pull requests`

### Codebase Metrics
- `Calculate codebase health indicators`
- `Graph developer action patterns`
