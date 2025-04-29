"""Tests for the org-mcp server."""

import os
import pathlib
import tempfile
from unittest import mock

import pytest

from org_mcp.server import list_org_files, list_org_files_tool, read_org_file, get_org_dir


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