"""Tests for the org-mcp server."""

import os
import pathlib
import tempfile
from unittest import mock

import pytest

from org_mcp.server import (
    list_org_files, list_org_files_tool, read_org_file, get_org_dir,
    extract_headings, read_file_headings, read_heading, search_org_files,
    add_org_file, add_heading, modify_heading, get_org_agenda, 
    get_org_todos, get_org_schedule, extract_scheduled_items
)


def test_get_org_dir_with_env():
    """Test get_org_dir with environment variable."""
    with mock.patch.dict(os.environ, {"ORG_DIR": "/test/org"}):
        assert get_org_dir() == "/test/org"


def test_get_org_dir_default():
    """Test get_org_dir default."""
    with mock.patch.dict(os.environ, clear=True):
        with mock.patch("os.path.expanduser") as mock_expanduser:
            mock_expanduser.return_value = "/home/user/org"
            assert get_org_dir() == "/home/user/org"


def test_list_org_files():
    """Test list_org_files function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test org files
        (pathlib.Path(temp_dir) / "test1.org").touch()
        (pathlib.Path(temp_dir) / "test2.org").touch()
        os.makedirs(os.path.join(temp_dir, "subdir"))
        (pathlib.Path(temp_dir) / "subdir" / "test3.org").touch()
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            result = list_org_files()
            assert "test1.org" in result
            assert "test2.org" in result
            assert "subdir/test3.org" in result


def test_list_org_files_tool():
    """Test list_org_files_tool function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test org files
        (pathlib.Path(temp_dir) / "test1.org").touch()
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            result = list_org_files_tool()
            assert len(result) == 1
            assert result[0]["path"] == "test1.org"
            assert result[0]["full_path"] == str(pathlib.Path(temp_dir) / "test1.org")


def test_read_org_file():
    """Test read_org_file function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test org file with content
        test_file = pathlib.Path(temp_dir) / "test.org"
        test_file.write_text("* Test Heading\nTest content")
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            result = read_org_file("test.org")
            assert "* Test Heading" in result
            assert "Test content" in result


def test_extract_headings():
    """Test extract_headings function."""
    org_content = """* Heading 1
Content for heading 1

** Sub-heading 1.1
Content for sub-heading 1.1

* TODO Heading 2
Content for heading 2
"""
    headings = extract_headings(org_content)
    
    assert len(headings) == 3
    
    assert headings[0]["level"] == 1
    assert headings[0]["title"] == "Heading 1"
    assert headings[0]["todo_state"] is None
    assert "Content for heading 1" in headings[0]["content"]
    
    assert headings[1]["level"] == 2
    assert headings[1]["title"] == "Sub-heading 1.1"
    assert "Content for sub-heading 1.1" in headings[1]["content"]
    
    assert headings[2]["level"] == 1
    assert headings[2]["title"] == "Heading 2"
    assert headings[2]["todo_state"] == "TODO"
    assert "Content for heading 2" in headings[2]["content"]


def test_read_file_headings():
    """Test read_file_headings function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test org file with content
        test_file = pathlib.Path(temp_dir) / "test.org"
        test_file.write_text("""* Heading 1
Content for heading 1

* TODO Heading 2
Content for heading 2
""")
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            result = read_file_headings("test.org")
            
            assert len(result) == 2
            assert result[0]["title"] == "Heading 1"
            assert result[1]["title"] == "Heading 2"
            assert result[1]["todo_state"] == "TODO"


def test_read_heading():
    """Test read_heading function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test org file with content
        test_file = pathlib.Path(temp_dir) / "test.org"
        test_file.write_text("""* Heading 1
Content for heading 1

* TODO Heading 2
Content for heading 2
""")
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            result = read_heading("test.org", "Heading 2")
            
            assert result["title"] == "Heading 2"
            assert result["todo_state"] == "TODO"
            assert "Content for heading 2" in result["content"]
            
            # Test for non-existent heading
            error_result = read_heading("test.org", "Heading 3")
            assert "error" in error_result


def test_search_org_files():
    """Test search_org_files function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test org files with content
        file1 = pathlib.Path(temp_dir) / "test1.org"
        file1.write_text("""* Project X
Some content about Project X

** TODO Task for Project X
Need to complete this task
""")
        
        file2 = pathlib.Path(temp_dir) / "test2.org"
        file2.write_text("""* Project Y
Some content about Project Y

** Meeting notes
Discussed Project X briefly
""")
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            result = search_org_files("Project X")
            
            assert len(result) == 2  # Should find matches in both files
            
            # Check that we found the right headings
            found_headings = []
            for file_result in result:
                for heading in file_result["matches_in_headings"]:
                    found_headings.append(heading["title"])
            
            assert "Project X" in found_headings
            assert "Task for Project X" in found_headings
            assert "Meeting notes" in found_headings


def test_add_org_file():
    """Test add_org_file function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            # Add a new file
            result = add_org_file("new_file.org", "* Test Content")
            
            assert result["status"] == "success"
            assert os.path.exists(os.path.join(temp_dir, "new_file.org"))
            
            # Read the file to verify content
            with open(os.path.join(temp_dir, "new_file.org"), "r") as f:
                content = f.read()
                assert content == "* Test Content"
            
            # Try to add the same file again (should fail)
            error_result = add_org_file("new_file.org")
            assert "error" in error_result


def test_add_heading():
    """Test add_heading function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test org file with content
        test_file = pathlib.Path(temp_dir) / "test.org"
        test_file.write_text("* Existing Heading\nExisting content")
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            # Add a new heading
            result = add_heading("test.org", "New Heading", level=2, 
                                content="New heading content", todo_state="TODO")
            
            assert result["status"] == "success"
            
            # Read the file to verify the new heading was added
            with open(test_file, "r") as f:
                content = f.read()
                assert "* Existing Heading" in content
                assert "** TODO New Heading" in content
                assert "New heading content" in content


def test_modify_heading():
    """Test modify_heading function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test org file with content
        test_file = pathlib.Path(temp_dir) / "test.org"
        test_file.write_text("""* Heading 1
Content for heading 1

* TODO Heading 2
Content for heading 2
""")
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            # Modify a heading
            result = modify_heading("test.org", "Heading 2", 
                                    new_title="Updated Heading", 
                                    new_todo_state="DONE")
            
            assert result["status"] == "success"
            
            # Read the file to verify the modification
            with open(test_file, "r") as f:
                content = f.read()
                assert "* Heading 1" in content
                assert "* DONE Updated Heading" in content
                assert "* TODO Heading 2" not in content
                assert "Content for heading 2" in content


def test_extract_scheduled_items():
    """Test extract_scheduled_items function."""
    org_content = """* Task with Schedule
SCHEDULED: <2025-05-01 Thu>
Some description

* Task with Deadline
DEADLINE: <2025-05-15 Thu>
Some description

* Task with both
SCHEDULED: <2025-05-02 Fri> DEADLINE: <2025-05-20 Tue>
Some description
"""
    items = extract_scheduled_items(org_content)
    
    assert len(items) == 4  # 2 scheduled + 2 deadline
    
    scheduled_items = [item for item in items if item["type"] == "scheduled"]
    deadline_items = [item for item in items if item["type"] == "deadline"]
    
    assert len(scheduled_items) == 2
    assert len(deadline_items) == 2
    
    assert "2025-05-01" in [item["date"] for item in scheduled_items]
    assert "2025-05-02" in [item["date"] for item in scheduled_items]
    assert "2025-05-15" in [item["date"] for item in deadline_items]
    assert "2025-05-20" in [item["date"] for item in deadline_items]


def test_get_org_agenda():
    """Test get_org_agenda function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test org files with some TODO items and scheduled items
        file1 = pathlib.Path(temp_dir) / "test1.org"
        file1.write_text("""* TODO Task 1
SCHEDULED: <2025-05-01 Thu>
Some description

* DONE Completed task
""")
        
        file2 = pathlib.Path(temp_dir) / "test2.org"
        file2.write_text("""* Regular heading
        
* TODO Task 2
DEADLINE: <2025-05-15 Thu>
Priority task
""")
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            # Mock the emacs calls to fail so we use the fallback parsing
            with mock.patch("org_mcp.server.run_org_agenda_command", 
                           return_value="Error: Emacs not found"):
                result = get_org_agenda()
                
                # Check that we got both todos and scheduled items
                assert "todos" in result
                assert "scheduled" in result
                
                # Check TODOs
                assert len(result["todos"]) == 2
                task_titles = [task["heading"] for task in result["todos"]]
                assert "Task 1" in task_titles
                assert "Task 2" in task_titles
                
                # Check scheduled items
                assert len(result["scheduled"]) == 2
                scheduled_types = [item["type"] for item in result["scheduled"]]
                assert "scheduled" in scheduled_types
                assert "deadline" in scheduled_types


def test_get_org_todos():
    """Test get_org_todos function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test org files with some TODO items
        file1 = pathlib.Path(temp_dir) / "test1.org"
        file1.write_text("""* TODO Task 1
Some description

* DONE Completed task
""")
        
        file2 = pathlib.Path(temp_dir) / "test2.org"
        file2.write_text("""* Regular heading
        
* TODO Task 2
Priority task
""")
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            # Mock the emacs call to fail so we use the fallback parsing
            with mock.patch("org_mcp.server.run_org_agenda_command", 
                           return_value="Error: Emacs not found"):
                result = get_org_todos()
                
                assert "todos" in result
                assert len(result["todos"]) == 2
                
                # Check that we found all the TODO items
                task_titles = [task["heading"] for task in result["todos"]]
                assert "Task 1" in task_titles
                assert "Task 2" in task_titles
                assert "Completed task" not in task_titles  # This is DONE


def test_get_org_schedule():
    """Test get_org_schedule function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test org files with some scheduled items
        file1 = pathlib.Path(temp_dir) / "test1.org"
        file1.write_text("""* Task 1
SCHEDULED: <2025-05-01 Thu>
Some description
""")
        
        file2 = pathlib.Path(temp_dir) / "test2.org"
        file2.write_text("""* Task 2
DEADLINE: <2025-05-15 Thu>
Some description
""")
        
        with mock.patch("org_mcp.server.get_org_dir", return_value=temp_dir):
            # Mock the emacs call to fail so we use the fallback parsing
            with mock.patch("org_mcp.server.run_org_agenda_command", 
                           return_value="Error: Emacs not found"):
                result = get_org_schedule()
                
                assert "scheduled" in result
                assert len(result["scheduled"]) == 2
                
                # Check scheduled items
                scheduled_types = [item["type"] for item in result["scheduled"]]
                assert "scheduled" in scheduled_types
                assert "deadline" in scheduled_types
                
                # Verify dates
                dates = [item["date"] for item in result["scheduled"]]
                assert "2025-05-01" in dates
                assert "2025-05-15" in dates