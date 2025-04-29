"""MCP server for org-mode files."""

import os
import pathlib
from typing import List, Dict, Any

from mcp.server.fastmcp import FastMCP, Context

# Create an MCP server
mcp = FastMCP("org-mcp")


def get_org_dir() -> str:
    """Get the org directory from environment variable or default to ~/org."""
    org_dir = os.environ.get("ORG_DIR", os.path.expanduser("~/org"))
    return org_dir


@mcp.resource("org://files")
def list_org_files() -> str:
    """List all org files in the configured directory."""
    org_dir = get_org_dir()
    path = pathlib.Path(org_dir)
    
    try:
        org_files = list(path.glob("**/*.org"))
        if not org_files:
            return f"No .org files found in {org_dir}"
        
        files_info = [f"- {file.relative_to(path)}" for file in org_files]
        return f"Org files in {org_dir}:\n\n" + "\n".join(files_info)
    except Exception as e:
        return f"Error accessing org files: {str(e)}"


@mcp.tool()
def list_org_files_tool() -> List[Dict[str, str]]:
    """Get a list of all org files."""
    org_dir = get_org_dir()
    path = pathlib.Path(org_dir)
    
    try:
        org_files = list(path.glob("**/*.org"))
        return [
            {"path": str(file.relative_to(path)), "full_path": str(file)} 
            for file in org_files
        ]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def read_org_file(file_path: str) -> str:
    """Read the content of an org file.
    
    Args:
        file_path: Relative path to the org file
    """
    org_dir = get_org_dir()
    full_path = os.path.join(org_dir, file_path)
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.prompt()
def org_help() -> str:
    """Help prompt for org-mode interactions."""
    return """
I can help you access and work with your org-mode files. Here are some things you can ask me:

- List all your org files
- Read a specific org file
- Search for content in your org files
- Summarize your TODOs and agenda
    """


if __name__ == "__main__":
    mcp.run()