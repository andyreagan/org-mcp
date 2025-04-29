"""Entry point for org-mcp server."""

from org_mcp.server import mcp


def main():
    """Run the org-mcp MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
