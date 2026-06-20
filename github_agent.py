import asyncio
import json
import os
import re
import streamlit as st
from textwrap import dedent
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.mcp import MCPTools
from agno.models.groq import Groq
from mcp import StdioServerParameters

def parse_repo_path(path_input: str) -> str:
    path_input = path_input.strip()
    
    # 1. Check if it's a URL and extract the path part
    match = re.search(r"github\.com/([^\s/]+)/([^\s]+)", path_input)
    if match:
        owner = match.group(1).strip()
        repo = match.group(2).strip()
        # Clean trailing slashes/parameters
        repo = repo.split("?")[0].split("#")[0].rstrip("/")
        # Replace spaces in repo name with hyphens
        repo = repo.replace(" ", "-")
        return f"{owner}/{repo}"
    
    # 2. If it's not a URL but contains a slash
    if "/" in path_input:
        parts = [p.strip() for p in path_input.split("/") if p.strip()]
        if len(parts) >= 2:
            owner = parts[0].replace(" ", "-")
            repo = "-".join(parts[1:])  # rejoin with hyphens if there were more slashes or spaces
            repo = repo.replace(" ", "-")
            return f"{owner}/{repo}"
            
    return path_input.replace(" ", "-")

def extract_clean_output(raw_output: str) -> str:
    """Extract readable content from agent output, handling Groq tool_use_failed errors."""
    if not raw_output:
        return "No output was returned by the agent."
    
    # Try to detect if the output is a JSON error with failed_generation
    stripped = raw_output.strip()
    if stripped.startswith('{') and 'failed_generation' in stripped:
        try:
            error_obj = json.loads(stripped)
            # Extract the actual generated content from the error
            failed_gen = error_obj.get('error', {}).get('failed_generation', '')
            if failed_gen and len(failed_gen) > 20:
                return failed_gen
        except json.JSONDecodeError:
            pass
    
    # Also handle case where the string contains JSON embedded in other text
    json_match = re.search(r'\{"error".*?"failed_generation"\s*:\s*"(.*?)"\s*\}\s*\}', stripped, re.DOTALL)
    if json_match:
        try:
            # Try full JSON parse first
            full_match = re.search(r'(\{"error".*\})', stripped, re.DOTALL)
            if full_match:
                error_obj = json.loads(full_match.group(1))
                failed_gen = error_obj.get('error', {}).get('failed_generation', '')
                if failed_gen and len(failed_gen) > 20:
                    return failed_gen
        except json.JSONDecodeError:
            pass
    
    return raw_output

# Configure page metadata
st.set_page_config(
    page_title="GitHub Repository Agent — MCP Powered",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────
# Premium CSS Design System
# ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hide Streamlit default menu & footer */
#MainMenu, footer, header {visibility: hidden;}

/* ── Animated Gradient Header ── */
.hero-title {
    background: linear-gradient(270deg, #6C63FF, #00D2FF, #A855F7, #F472B6);
    background-size: 800% 800%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900;
    font-size: 2.6rem;
    letter-spacing: -1.5px;
    line-height: 1.15;
    animation: gradientShift 8s ease infinite;
}
@keyframes gradientShift {
    0%{background-position:0% 50%}
    50%{background-position:100% 50%}
    100%{background-position:0% 50%}
}

.hero-subtitle {
    color: rgba(255,255,255,0.55);
    font-size: 1.05rem;
    font-weight: 400;
    margin-top: -4px;
    letter-spacing: 0.2px;
}

/* ── Stat Badges ── */
.stat-row {
    display: flex;
    gap: 12px;
    margin: 18px 0 10px 0;
    flex-wrap: wrap;
}
.stat-badge {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 0.78rem;
    color: rgba(255,255,255,0.7);
    display: flex;
    align-items: center;
    gap: 6px;
    backdrop-filter: blur(8px);
    transition: all 0.25s ease;
}
.stat-badge:hover {
    border-color: rgba(108,99,255,0.4);
    background: rgba(108,99,255,0.08);
    transform: translateY(-1px);
}
.stat-badge .dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    display: inline-block;
}
.dot-green { background: #34D399; box-shadow: 0 0 6px #34D399; }
.dot-blue  { background: #60A5FA; box-shadow: 0 0 6px #60A5FA; }
.dot-purple { background: #A78BFA; box-shadow: 0 0 6px #A78BFA; }

/* ── Glassmorphism Card ── */
.glass-card {
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 28px 26px;
    margin: 20px 0;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    position: relative;
    overflow: hidden;
}
.glass-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #6C63FF, #00D2FF, #A855F7);
    border-radius: 16px 16px 0 0;
}
.glass-card h4 {
    color: #00D2FF;
    font-weight: 700;
    margin-top: 6px;
    font-size: 1.15rem;
    letter-spacing: -0.3px;
}
.glass-card li {
    font-size: 0.92rem;
    margin-bottom: 7px;
    color: rgba(255,255,255,0.75);
    line-height: 1.6;
}
.glass-card ol { padding-left: 20px; }
.glass-card ul { padding-left: 18px; list-style: none; }
.glass-card ul li::before {
    content: '→';
    color: #A855F7;
    font-weight: 600;
    margin-right: 8px;
}
.glass-card strong { color: rgba(255,255,255,0.92); }

/* ── Result Output Card ── */
.result-card {
    background: rgba(255,255,255,0.015);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 28px 26px;
    margin: 14px 0;
    box-shadow: 0 4px 24px rgba(108,99,255,0.08);
    position: relative;
}
.result-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #34D399, #00D2FF);
}
.result-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}
.result-header h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 700;
    color: #fff;
}
.result-header .pulse-dot {
    width: 8px; height: 8px;
    background: #34D399;
    border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(52,211,153,0.5); }
    50% { box-shadow: 0 0 0 6px rgba(52,211,153,0); }
}

/* ── Primary Button ── */
div.stButton > button:first-child {
    background: linear-gradient(135deg, #6C63FF 0%, #A855F7 50%, #00D2FF 100%) !important;
    background-size: 200% 200% !important;
    color: white !important;
    border: none !important;
    padding: 14px 28px !important;
    border-radius: 14px !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    box-shadow: 0 4px 20px rgba(108,99,255,0.35) !important;
}
div.stButton > button:first-child:hover {
    background-position: right center !important;
    box-shadow: 0 8px 28px rgba(168,85,247,0.45) !important;
    transform: translateY(-3px) !important;
}
div.stButton > button:first-child:active {
    transform: translateY(0px) !important;
    box-shadow: 0 2px 10px rgba(108,99,255,0.3) !important;
}

/* ── Input Fields ── */
div[data-baseweb="input"] {
    background-color: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
}
div[data-baseweb="input"]:focus-within {
    border-color: #6C63FF !important;
    box-shadow: 0 0 0 3px rgba(108,99,255,0.12) !important;
}

div[data-baseweb="textarea"] textarea {
    background-color: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
}
div[data-baseweb="textarea"] textarea:focus {
    border-color: #6C63FF !important;
    box-shadow: 0 0 0 3px rgba(108,99,255,0.12) !important;
}

/* ── Selectbox ── */
div[data-baseweb="select"] {
    background-color: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0c12 0%, #0f1118 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.04) !important;
}
[data-testid="stSidebar"] h2 {
    color: #ffffff;
    font-weight: 700;
    font-size: 1.1rem;
}
.sidebar-section-title {
    color: rgba(255,255,255,0.45);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 600;
    margin: 20px 0 8px 0;
}
.sidebar-example {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.82rem;
    color: rgba(255,255,255,0.65);
    transition: all 0.2s ease;
    cursor: default;
}
.sidebar-example:hover {
    background: rgba(108,99,255,0.08);
    border-color: rgba(108,99,255,0.25);
    color: rgba(255,255,255,0.85);
}
.sidebar-example strong {
    color: #A78BFA;
    font-weight: 600;
}

/* ── Footer ── */
.app-footer {
    text-align: center;
    padding: 24px 0 12px 0;
    border-top: 1px solid rgba(255,255,255,0.04);
    margin-top: 40px;
}
.app-footer p {
    color: rgba(255,255,255,0.3);
    font-size: 0.78rem;
    margin: 2px 0;
}
.footer-tech {
    display: inline-flex;
    gap: 16px;
    margin-top: 8px;
}
.footer-tech span {
    color: rgba(255,255,255,0.25);
    font-size: 0.72rem;
    padding: 4px 10px;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 6px;
}

/* ── Spinner ── */
.stSpinner > div {
    border-top-color: #6C63FF !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.15); }

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────
st.markdown("<h1 class='hero-title'>🐙 GitHub Repository Agent</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-subtitle'>Query, audit, and analyze any GitHub repository using natural language — powered by Model Context Protocol.</p>", unsafe_allow_html=True)

# Status badges
st.markdown("""
<div class='stat-row'>
    <div class='stat-badge'><span class='dot dot-green'></span> MCP Server Active</div>
    <div class='stat-badge'><span class='dot dot-blue'></span> GitHub API Connected</div>
    <div class='stat-badge'><span class='dot dot-purple'></span> LLM Engine Ready</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────
# Sidebar — Credentials & Examples
# ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2>🔐 Authentication</h2>", unsafe_allow_html=True)
    
    groq_key = st.text_input("Groq API Key", type="password",
                               help="Powers the natural language understanding engine")
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    
    github_token = st.text_input("GitHub Token", type="password", 
                                help="Personal access token with repo read scope")
    if github_token:
        os.environ["GITHUB_TOKEN"] = github_token
    
    st.markdown("<p class='sidebar-section-title'>💡 Example Queries</p>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='sidebar-example'><strong>Issues</strong> — Find bugs labeled as critical</div>
    <div class='sidebar-example'><strong>PRs</strong> — List open PRs awaiting review</div>
    <div class='sidebar-example'><strong>README</strong> — Summarize the project overview</div>
    <div class='sidebar-example'><strong>Activity</strong> — Show recent commit trends</div>
    <div class='sidebar-example'><strong>Files</strong> — List the root directory structure</div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p class='sidebar-section-title'>ℹ️ Info</p>", unsafe_allow_html=True)
    st.caption("This agent connects to GitHub via the official MCP server and translates your natural language into precise API queries.")

# ─────────────────────────────────────────────────────
# Input Area
# ─────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    target_repo = st.text_input(
        "📦 Repository", 
        value="psf/requests", 
        help="Enter owner/repo or a full GitHub URL",
        placeholder="e.g. facebook/react or https://github.com/owner/repo"
    )
with col2:
    query_category = st.selectbox("📂 Category", [
        "Custom", "Issues", "Pull Requests", "Repository Activity"
    ])

# Set templates based on query category
if query_category == "Issues":
    query_template = f"Find issues labeled as bugs in {target_repo}"
elif query_category == "Pull Requests":
    query_template = f"Show me recent merged PRs in {target_repo}"
elif query_category == "Repository Activity":
    query_template = f"Analyze code quality trends in {target_repo}"
else:
    query_template = ""

user_prompt = st.text_area(
    "🔍 Your Query", 
    value=query_template, 
    placeholder="Ask anything — e.g. 'Give me the README description' or 'List all open issues'...",
    height=100
)

# ─────────────────────────────────────────────────────
# Agent Execution
# ─────────────────────────────────────────────────────
async def execute_github_query(prompt_text):
    if not os.getenv("GITHUB_TOKEN"):
        return "⚠️ **Missing Authentication** — GitHub token is required. Add it in the sidebar."
    
    if not os.getenv("GROQ_API_KEY"):
        return "⚠️ **Missing Authentication** — Groq API key is required. Add it in the sidebar."
    
    try:
        # Spawn Github MCP server via npx (cross-platform compatible, avoids Docker dependency)
        cmd = "npx.cmd" if os.name == "nt" else "npx"
        server_configuration = StdioServerParameters(
            command=cmd,
            args=[
                "-y",
                "@modelcontextprotocol/server-github"
            ],
            env={
                **os.environ,
                "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv('GITHUB_TOKEN')
            }
        )
        
        # Connect to tools and run agent query
        async with MCPTools(server_params=server_configuration) as tools_interface:
            repository_agent = Agent(
                model=Groq(id="meta-llama/llama-4-scout-17b-16e-instruct"),
                tools=[tools_interface],
                instructions=dedent("""\
                    You are a specialized GitHub repository assistant. Help users analyze repo details.
                    - Offer organized, data-driven feedback on repo states
                    - Base your conclusions directly on GitHub API responses
                    - Format outputs using clear markdown tables and headers
                    - Link to related issues or pull requests to simplify navigation
                """),
                markdown=True,
            )
            
            job: RunOutput = await asyncio.wait_for(repository_agent.arun(prompt_text), timeout=120.0)
            return job.content
                
    except asyncio.TimeoutError:
        return "⏱️ **Request Timed Out** — The operation exceeded 120 seconds. Try a simpler query."
    except Exception as error:
        error_str = str(error)
        # Groq tool_use_failed errors contain the actual content in 'failed_generation'
        if 'failed_generation' in error_str:
            try:
                # Find the JSON payload inside the error string
                json_start = error_str.find('{')
                json_end = error_str.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    error_json = json.loads(error_str[json_start:json_end])
                    failed_gen = error_json.get('error', {}).get('failed_generation', '')
                    if failed_gen and len(failed_gen) > 20:
                        return failed_gen
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        return f"❌ **Error** — {error_str}"

# ─────────────────────────────────────────────────────
# Run Button & Output
# ─────────────────────────────────────────────────────
if st.button("⚡ Run Query", type="primary", use_container_width=True):
    if not groq_key:
        st.error("🔑 Groq API key is required — add it in the sidebar.")
    elif not github_token:
        st.error("🔑 GitHub token is required — add it in the sidebar.")
    elif not user_prompt:
        st.error("📝 Please enter a query before running.")
    else:
        with st.spinner("🔄 Connecting to GitHub MCP server and analyzing..."):
            cleaned_repo = parse_repo_path(target_repo)
            st.info(f"🎯 Target repository: **{cleaned_repo}**")
            if cleaned_repo and cleaned_repo not in user_prompt:
                finalized_prompt = f"{user_prompt} in {cleaned_repo}"
            else:
                finalized_prompt = user_prompt
                
            query_output = asyncio.run(execute_github_query(finalized_prompt))
        
        # Render result in a styled card
        cleaned_output = extract_clean_output(query_output)
        st.markdown("""
        <div class='result-card'>
            <div class='result-header'>
                <div class='pulse-dot'></div>
                <h3>Analysis Complete</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(cleaned_output)

# ─────────────────────────────────────────────────────
# Welcome Card (shown when no query has been run)
# ─────────────────────────────────────────────────────
if 'query_output' not in locals():
    st.markdown(
        """<div class='glass-card'>
        <h4>⚡ Quick Start</h4>
        <ol>
            <li>Enter your <strong>Groq API Key</strong> and <strong>GitHub Token</strong> in the sidebar.</li>
            <li>Type a repository path — e.g. <code>facebook/react</code> or paste a full GitHub URL.</li>
            <li>Select a category or write a custom natural language query.</li>
            <li>Hit <strong>Run Query</strong> and let the agent fetch & analyze the data.</li>
        </ol>
        <strong>What can this agent do?</strong>
        <ul>
            <li>Fetch and summarize README files and project documentation</li>
            <li>List, filter, and analyze issues and pull requests</li>
            <li>Explore repository file structure and contents</li>
            <li>Generate insights on code quality, activity trends, and contributors</li>
            <li>Cross-reference issues, PRs, and commits for deep analysis</li>
        </ul>
        </div>""", 
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────
st.markdown("""
<div class='app-footer'>
    <p>GitHub Repository Agent — Natural Language Repository Intelligence</p>
    <div class='footer-tech'>
        <span>Streamlit</span>
        <span>Agno Framework</span>
        <span>GitHub MCP</span>
        <span>Groq LLM</span>
    </div>
</div>
""", unsafe_allow_html=True)
