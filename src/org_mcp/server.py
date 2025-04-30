"""MCP server for org-mode files."""

import os
import pathlib
import re
import subprocess
from typing import Any

from mcp.server.fastmcp import FastMCP

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
def list_org_files_tool() -> list[dict[str, str]]:
    """Get a list of all org files."""
    org_dir = get_org_dir()
    path = pathlib.Path(org_dir)

    try:
        org_files = list(path.glob("**/*.org"))
        return [{"path": str(file.relative_to(path)), "full_path": str(file)} for file in org_files]
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
        with open(full_path, encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def extract_headings(content: str) -> list[dict[str, Any]]:
    """Extract headings from org file content with their level and content.

    Args:
        content: Org file content

    Returns:
        List of dictionaries containing heading information
    """
    headings = []
    current_heading = None
    heading_content = []

    # Regular expression to match headings (*, **, ***, etc.)
    heading_pattern = re.compile(r"^(\*+)\s+(.*)$")

    for line in content.splitlines():
        heading_match = heading_pattern.match(line)

        if heading_match:
            # If we were collecting content for a previous heading, save it
            if current_heading is not None:
                current_heading["content"] = "\n".join(heading_content)
                headings.append(current_heading)
                heading_content = []

            # Create new heading entry
            stars = heading_match.group(1)
            title = heading_match.group(2)

            # Extract TODO state if present
            todo_match = re.match(r"(TODO|DONE|IN-PROGRESS)\s+(.*)", title)
            todo_state = None
            if todo_match:
                todo_state = todo_match.group(1)
                title = todo_match.group(2)

            current_heading = {
                "level": len(stars),
                "title": title,
                "raw": line,
                "todo_state": todo_state,
            }
        elif current_heading is not None:
            # Add to current heading's content
            heading_content.append(line)

    # Don't forget the last heading
    if current_heading is not None:
        current_heading["content"] = "\n".join(heading_content)
        headings.append(current_heading)

    return headings


@mcp.tool()
def read_file_headings(file_path: str) -> list[dict[str, Any]]:
    """Read and parse headings from an org file.

    Args:
        file_path: Relative path to the org file

    Returns:
        List of dictionaries containing heading information
    """
    content = read_org_file(file_path)
    if content.startswith("Error:"):
        return [{"error": content}]

    return extract_headings(content)


@mcp.tool()
def read_heading(file_path: str, heading_title: str) -> dict[str, Any]:
    """Read a specific heading and its content from an org file.

    Args:
        file_path: Relative path to the org file
        heading_title: The title of the heading to find

    Returns:
        Dictionary with heading information or error message
    """
    headings = read_file_headings(file_path)

    if isinstance(headings, list) and headings and "error" in headings[0]:
        return {"error": headings[0]["error"]}

    for heading in headings:
        if heading["title"] == heading_title:
            return heading

    return {"error": f"Heading '{heading_title}' not found in {file_path}"}


@mcp.tool()
def search_org_files(query: str) -> list[dict[str, Any]]:
    """Search for text across all org files, returning matching files and headings.

    Args:
        query: Text to search for

    Returns:
        List of matches with file path and heading information
    """
    org_dir = get_org_dir()
    path = pathlib.Path(org_dir)
    matches = []

    try:
        org_files = list(path.glob("**/*.org"))

        for file in org_files:
            rel_path = str(file.relative_to(path))

            try:
                with open(file, encoding="utf-8") as f:
                    content = f.read()

                # If query is found in entire file
                if query.lower() in content.lower():
                    # Get headings to provide more context
                    headings = extract_headings(content)

                    # Check for matches in headings
                    found_in_headings = []
                    for heading in headings:
                        if (
                            query.lower() in heading["title"].lower()
                            or query.lower() in heading["content"].lower()
                        ):
                            found_in_headings.append(
                                {
                                    "title": heading["title"],
                                    "level": heading["level"],
                                    "todo_state": heading["todo_state"],
                                }
                            )

                    matches.append(
                        {"file_path": rel_path, "matches_in_headings": found_in_headings}
                    )
            except Exception:
                continue  # Skip files with errors

        return matches
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def add_org_file(file_path: str, content: str = "") -> dict[str, str]:
    """Create a new org file.

    Args:
        file_path: Relative path for the new org file
        content: Initial content for the file

    Returns:
        Status message
    """
    org_dir = get_org_dir()
    full_path = os.path.join(org_dir, file_path)

    try:
        # Make sure the directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Check if file already exists
        if os.path.exists(full_path):
            return {"error": f"File {file_path} already exists"}

        # Create the file with initial content
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return {"status": "success", "message": f"Created new file: {file_path}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def add_heading(
    file_path: str, title: str, level: int = 1, content: str = "", todo_state: str | None = None
) -> dict[str, str]:
    """Add a new heading to an org file.

    Args:
        file_path: Relative path to the org file
        title: Heading title
        level: Heading level (1=*, 2=**, etc.)
        content: Content to add under the heading
        todo_state: Optional TODO state (TODO, DONE, etc.)

    Returns:
        Status message
    """
    org_dir = get_org_dir()
    full_path = os.path.join(org_dir, file_path)

    try:
        # Check if file exists
        if not os.path.exists(full_path):
            return {"error": f"File {file_path} does not exist"}

        # Read existing content
        with open(full_path, encoding="utf-8") as f:
            existing_content = f.read()

        # Create new heading
        stars = "*" * level
        heading_text = f"{stars} "
        if todo_state:
            heading_text += f"{todo_state} "
        heading_text += title

        # Add content with proper formatting
        new_content = f"{existing_content}\n\n{heading_text}\n{content}"

        # Write back to file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {"status": "success", "message": f"Added new heading '{title}' to {file_path}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def modify_heading(
    file_path: str,
    heading_title: str,
    new_title: str | None = None,
    new_content: str | None = None,
    new_todo_state: str | None = None,
) -> dict[str, str]:
    """Modify an existing heading in an org file.

    Args:
        file_path: Relative path to the org file
        heading_title: Title of the heading to modify
        new_title: New title for the heading (or None to keep existing)
        new_content: New content for the heading (or None to keep existing)
        new_todo_state: New TODO state (or None to keep existing)

    Returns:
        Status message
    """
    org_dir = get_org_dir()
    full_path = os.path.join(org_dir, file_path)

    try:
        # Check if file exists
        if not os.path.exists(full_path):
            return {"error": f"File {file_path} does not exist"}

        # Read existing content
        with open(full_path, encoding="utf-8") as f:
            content = f.read()

        headings = extract_headings(content)
        target_heading = None
        heading_index = -1

        # Find the target heading
        for i, heading in enumerate(headings):
            if heading["title"] == heading_title:
                target_heading = heading
                heading_index = i
                break

        if not target_heading:
            return {"error": f"Heading '{heading_title}' not found in {file_path}"}

        # Prepare the modified heading
        stars = "*" * target_heading["level"]
        heading_line = f"{stars} "

        # Update TODO state if provided
        todo_state = new_todo_state if new_todo_state is not None else target_heading["todo_state"]
        if todo_state:
            heading_line += f"{todo_state} "

        # Update title if provided
        title = new_title if new_title is not None else target_heading["title"]
        heading_line += title

        # Update content if provided
        content_text = new_content if new_content is not None else target_heading["content"]

        # Replace the old heading and content in the file
        lines = content.splitlines()

        # Find the line number of the heading
        line_number = -1
        heading_pattern = re.compile(r"^(\*+)\s+(.*)$")

        for i, line in enumerate(lines):
            match = heading_pattern.match(line)
            if match and match.group(2).endswith(heading_title):
                if (
                    match.group(2) == heading_title
                    or match.group(2).startswith("TODO ")
                    or match.group(2).startswith("DONE ")
                ):
                    line_number = i
                    break

        if line_number == -1:
            return {"error": f"Heading line not found for '{heading_title}' in {file_path}"}

        # Find the end of this heading's content (next heading or EOF)
        end_line = len(lines)
        for i in range(line_number + 1, len(lines)):
            if heading_pattern.match(lines[i]):
                end_line = i
                break

        # Replace the heading and its content
        new_lines = (
            lines[:line_number] + [heading_line] + content_text.splitlines() + lines[end_line:]
        )

        # Write the modified content back to the file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))

        return {
            "status": "success",
            "message": f"Modified heading '{heading_title}' in {file_path}",
        }
    except Exception as e:
        return {"error": str(e)}


def run_org_agenda_command(command: str) -> str:
    """Run an org-agenda command and return the output.

    Args:
        command: The Emacs Lisp command to execute

    Returns:
        Command output or error message

    This requires Emacs to be installed with org-mode configured.
    """
    try:
        # Command to run org-agenda in batch mode
        cmd = [
            "emacs",
            "--batch",
            "--eval",
            f"(progn (require 'org) {command} (princ (buffer-string)))",
        ]

        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running org-agenda: {e}"
    except FileNotFoundError:
        return "Error: Emacs not found. Please ensure Emacs is installed."


def extract_scheduled_items(content: str) -> list[dict[str, Any]]:
    """Extract scheduled items from org content.

    Args:
        content: Org file content

    Returns:
        List of scheduled items with date and heading information
    """
    scheduled_items = []

    # First get all headings
    headings = extract_headings(content)

    # Look for SCHEDULED: timestamps in heading content
    scheduled_pattern = re.compile(r"SCHEDULED:\s*<(\d{4}-\d{2}-\d{2})(?: [^>]*)?>")
    deadline_pattern = re.compile(r"DEADLINE:\s*<(\d{4}-\d{2}-\d{2})(?: [^>]*)?>")

    for heading in headings:
        scheduled_match = scheduled_pattern.search(heading["content"])
        deadline_match = deadline_pattern.search(heading["content"])

        if scheduled_match:
            scheduled_date = scheduled_match.group(1)
            scheduled_items.append(
                {
                    "type": "scheduled",
                    "date": scheduled_date,
                    "title": heading["title"],
                    "todo_state": heading["todo_state"],
                    "level": heading["level"],
                }
            )

        if deadline_match:
            deadline_date = deadline_match.group(1)
            scheduled_items.append(
                {
                    "type": "deadline",
                    "date": deadline_date,
                    "title": heading["title"],
                    "todo_state": heading["todo_state"],
                    "level": heading["level"],
                }
            )

    return scheduled_items


@mcp.tool()
def get_org_agenda() -> dict[str, Any]:
    """Get the org agenda for today, including schedule and TODOs.

    Returns:
        Dictionary with agenda information including schedule and TODOs
    """
    try:
        # First try using Emacs for full agenda functionality
        agenda_output = run_org_agenda_command("(org-agenda-list)")
        todo_output = run_org_agenda_command("(org-todo-list)")

        if agenda_output.startswith("Error") or todo_output.startswith("Error"):
            # Manual parsing fallback if org-agenda command fails
            org_dir = get_org_dir()
            path = pathlib.Path(org_dir)
            todos = []
            scheduled_items = []

            org_files = list(path.glob("**/*.org"))
            for file in org_files:
                rel_path = str(file.relative_to(path))

                try:
                    with open(file, encoding="utf-8") as f:
                        content = f.read()

                    # Parse headings
                    headings = extract_headings(content)

                    # Get TODOs
                    for heading in headings:
                        if heading["todo_state"] in ["TODO", "IN-PROGRESS"]:
                            todos.append(
                                {
                                    "file": rel_path,
                                    "heading": heading["title"],
                                    "state": heading["todo_state"],
                                }
                            )

                    # Get scheduled items
                    items = extract_scheduled_items(content)
                    for item in items:
                        item["file"] = rel_path
                        scheduled_items.append(item)
                except Exception:
                    continue  # Skip files with errors

            # Sort scheduled items by date
            scheduled_items.sort(key=lambda x: x["date"])

            return {
                "source": "manual_parsing",
                "message": "Used manual parsing fallback",
                "todos": todos,
                "scheduled": scheduled_items,
            }
        else:
            # Return the output from both org-agenda commands
            return {"source": "org_agenda_command", "agenda": agenda_output, "todos": todo_output}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_org_todos() -> dict[str, Any]:
    """Get all TODO items from org files.

    Returns:
        Dictionary with TODO information
    """
    try:
        # First try using Emacs for full functionality
        todo_output = run_org_agenda_command("(org-todo-list)")

        if todo_output.startswith("Error"):
            # Manual parsing fallback
            org_dir = get_org_dir()
            path = pathlib.Path(org_dir)
            todos = []

            org_files = list(path.glob("**/*.org"))
            for file in org_files:
                rel_path = str(file.relative_to(path))

                try:
                    with open(file, encoding="utf-8") as f:
                        content = f.read()

                    headings = extract_headings(content)
                    for heading in headings:
                        if heading["todo_state"] in ["TODO", "IN-PROGRESS"]:
                            todos.append(
                                {
                                    "file": rel_path,
                                    "heading": heading["title"],
                                    "state": heading["todo_state"],
                                }
                            )
                except Exception:
                    continue

            return {"source": "manual_parsing", "todos": todos}
        else:
            return {"source": "org_agenda_command", "todos": todo_output}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_org_schedule() -> dict[str, Any]:
    """Get scheduled items and deadlines from org files.

    Returns:
        Dictionary with scheduled items
    """
    try:
        # First try using Emacs
        schedule_output = run_org_agenda_command("(org-agenda-list)")

        if schedule_output.startswith("Error"):
            # Manual parsing fallback
            org_dir = get_org_dir()
            path = pathlib.Path(org_dir)
            scheduled_items = []

            org_files = list(path.glob("**/*.org"))
            for file in org_files:
                rel_path = str(file.relative_to(path))

                try:
                    with open(file, encoding="utf-8") as f:
                        content = f.read()

                    items = extract_scheduled_items(content)
                    for item in items:
                        item["file"] = rel_path
                        scheduled_items.append(item)
                except Exception:
                    continue

            # Sort by date
            scheduled_items.sort(key=lambda x: x["date"])

            return {"source": "manual_parsing", "scheduled": scheduled_items}
        else:
            return {"source": "org_agenda_command", "schedule": schedule_output}
    except Exception as e:
        return {"error": str(e)}


@mcp.prompt()
def org_help() -> str:
    """Help prompt for org-mode interactions."""
    return """
I can help you access and work with your org-mode files. Here are some things you can ask me:

- List all your org files
- Read a specific org file or heading
- Search for content in your org files
- View your agenda with scheduled items and deadlines
- See all your TODO items
- Add new files or headings
- Modify existing headings

Examples:
- "What does my day look like today?"
- "What are the most important things for me to work on right now?"
- "Show me all my TODO items related to 'project X'"
- "Create a new heading in my notes.org file"
- "Show me my schedule for this week"
- "What deadlines do I have coming up?"
    """


if __name__ == "__main__":
    mcp.run()
