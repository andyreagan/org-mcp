"""Command-line interface for org-mcp."""

import argparse
import os
import sys

from org_mcp.server import mcp


def main():
    """Run the org-mcp MCP server."""
    parser = argparse.ArgumentParser(description="org-mcp - MCP server for org mode files")
    parser.add_argument(
        "--org-dir", 
        help="Directory containing org files (default: $ORG_DIR or ~/org)"
    )
    
    args = parser.parse_args()
    
    if args.org_dir:
        os.environ["ORG_DIR"] = args.org_dir
    
    try:
        mcp.run()
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())