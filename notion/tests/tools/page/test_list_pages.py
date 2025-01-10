"""
Tests for the ListPagesTool.
"""

from typing import Any, Dict, List

import pytest

from notion.tools.page.list_pages import ListPagesInput, ListPagesTool


class TestListPagesTool:
    """Test suite for ListPagesTool."""

    def test_list_pages_empty(self, mocker):
        """Test listing pages when no pages exist."""
        tool = ListPagesTool()
        mocker.patch.object(tool.api, "search_pages", return_value=[])

        result = tool._run()
        assert result["success"] is True
        assert result["data"]["pages"] == []
        assert result["data"]["total"] == 0

    def test_list_pages_with_results(self, mocker, sample_page, sample_database_page):
        """Test listing pages with results."""
        tool = ListPagesTool()
        mocker.patch.object(tool.api, "search_pages", return_value=[sample_page, sample_database_page])

        result = tool._run()
        assert result["success"] is True
        assert len(result["data"]["pages"]) == 2
        assert result["data"]["total"] == 2

    def test_list_pages_with_database_filter(self, mocker, sample_database_page):
        """Test filtering pages by database ID."""
        tool = ListPagesTool()
        mocker.patch.object(tool.api, "search_pages", return_value=[sample_database_page])

        result = tool._run(database_id="test-database-id")
        assert result["success"] is True
        assert len(result["data"]["pages"]) == 1
        assert result["data"]["pages"][0]["parent"]["type"] == "database_id"

    def test_list_pages_with_limit(self, mocker, sample_page):
        """Test limiting the number of returned pages."""
        tool = ListPagesTool()
        pages = [sample_page.copy() for _ in range(5)]
        mocker.patch.object(tool.api, "search_pages", return_value=pages)

        result = tool._run(limit=3)
        assert result["success"] is True
        assert len(result["data"]["pages"]) == 3
        assert result["data"]["total"] == 3

    def test_list_pages_with_archived_filter(self, mocker, sample_page):
        """Test filtering by archived status."""
        tool = ListPagesTool()
        archived_page = sample_page.copy()
        archived_page["archived"] = True
        pages = [sample_page, archived_page]
        mocker.patch.object(tool.api, "search_pages", return_value=pages)

        result = tool._run(archived=True)
        assert result["success"] is True
        assert len(result["data"]["pages"]) == 1
        assert all(page.get("archived", False) for page in result["data"]["pages"])

    def test_list_pages_input_validation(self):
        """Test input validation."""
        with pytest.raises(ValueError):
            ListPagesInput(database_id="", limit=100)

        with pytest.raises(ValueError):
            ListPagesInput(database_id="test", limit=0)

        with pytest.raises(ValueError):
            ListPagesInput(database_id="test", limit=1001)

    def test_list_pages_error_handling(self, mocker):
        """Test error handling."""
        tool = ListPagesTool()
        mocker.patch.object(tool.api, "search_pages", side_effect=Exception("API Error"))

        result = tool._run()
        assert result["success"] is False
        assert result["error"] is not None
