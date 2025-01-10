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

    @pytest.mark.parametrize("limit", [1, 100, 1000])
    def test_list_pages_limit_boundaries(self, mocker, sample_page, limit):
        """Test page limit boundaries."""
        tool = ListPagesTool()
        pages = [sample_page.copy() for _ in range(1000)]
        mocker.patch.object(tool.api, "search_pages", return_value=pages)

        result = tool._run(limit=limit)
        assert result["success"] is True
        assert len(result["data"]["pages"]) == limit

    @pytest.mark.parametrize("invalid_limit", [-1, 0, 1001])
    def test_list_pages_invalid_limits(self, invalid_limit):
        """Test invalid page limits."""
        with pytest.raises(ValueError):
            ListPagesInput(limit=invalid_limit)

    @pytest.mark.parametrize(
        "database_id,expected_count",
        [
            ("test-database-id", 1),
            ("non-existent-id", 0),
            (None, 2),
        ],
    )
    def test_list_pages_database_filter_scenarios(
        self, mocker, sample_page, sample_database_page, database_id, expected_count
    ):
        """Test various database filter scenarios."""
        tool = ListPagesTool()
        pages = [sample_page, sample_database_page]
        mocker.patch.object(tool.api, "search_pages", return_value=pages)

        result = tool._run(database_id=database_id)
        assert result["success"] is True
        assert len(result["data"]["pages"]) == expected_count

    @pytest.mark.integration
    def test_list_pages_integration(self, mocker):
        """Integration test for listing pages."""
        # This is a placeholder for actual integration testing
        # In a real implementation, this would use actual API calls
        pass

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

    @pytest.mark.asyncio
    async def test_list_pages_async(self, mocker):
        """Test async operation support."""
        # This is a placeholder for async testing
        # In a real implementation, this would test async API calls
        pass

    @pytest.mark.parametrize(
        "cursor,direction,expected_args",
        [
            ("cursor1", "forward", {"start_cursor": "cursor1", "end_cursor": None}),
            ("cursor2", "backward", {"start_cursor": None, "end_cursor": "cursor2"}),
            (None, "forward", {"start_cursor": None, "end_cursor": None}),
        ],
    )
    def test_list_pages_pagination(self, mocker, sample_page, cursor, direction, expected_args):
        """Test pagination with different cursor scenarios."""
        tool = ListPagesTool()
        mock_response = {
            "results": [sample_page],
            "has_more": True,
            "next_cursor": "next_cursor_value",
        }
        mock_search = mocker.patch.object(tool.api, "search_pages", return_value=mock_response)

        result = tool._run(cursor=cursor, direction=direction)

        assert result["success"] is True
        assert result["data"]["pagination"]["has_more"] is True
        assert result["data"]["pagination"]["next_cursor"] == "next_cursor_value"

        # Verify search arguments
        actual_args = {
            "start_cursor": mock_search.call_args[1].get("start_cursor"),
            "end_cursor": mock_search.call_args[1].get("end_cursor"),
        }
        assert actual_args == expected_args

    def test_list_pages_pagination_metadata(self, mocker, sample_page):
        """Test pagination metadata in response."""
        tool = ListPagesTool()
        mock_response = {
            "results": [sample_page],
            "has_more": True,
            "next_cursor": "next_cursor",
            "total_results": 50,
        }
        mocker.patch.object(tool.api, "search_pages", return_value=mock_response)

        result = tool._run()
        pagination = result["data"]["pagination"]

        assert pagination["has_more"] is True
        assert pagination["next_cursor"] == "next_cursor"
        assert pagination["total_results"] == 50

    def test_list_pages_pagination_empty(self, mocker):
        """Test pagination with empty results."""
        tool = ListPagesTool()
        mock_response = {
            "results": [],
            "has_more": False,
            "next_cursor": None,
        }
        mocker.patch.object(tool.api, "search_pages", return_value=mock_response)

        result = tool._run(cursor="some_cursor")
        pagination = result["data"]["pagination"]

        assert pagination["has_more"] is False
        assert pagination["next_cursor"] is None
        assert len(result["data"]["pages"]) == 0

    def test_list_pages_invalid_direction(self):
        """Test invalid pagination direction."""
        with pytest.raises(ValueError, match="Direction must be either 'forward' or 'backward'"):
            ListPagesInput(direction="invalid")

    @pytest.mark.integration
    def test_list_pages_pagination_integration(self, mocker):
        """Integration test for paginated listing."""
        # This is a placeholder for actual integration testing
        # In a real implementation, this would use actual API calls
        pass
