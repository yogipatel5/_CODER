        self.error_type = error_type
        self.status_code = status_code
        super().__init__(message)

# Standard response format
{
    "success": False,
    "error_type": "validation",
    "message": "Validation error: title"
}
```

## Testing Strategy

### 1. Coverage Requirements
- Unit Tests: 90% coverage
- Integration Tests: 80% coverage
- Error Cases: 100% coverage

### 2. Test Categories
- [x] Model Validation Tests
  - [x] Field validation
  - [x] Type conversion
  - [x] Error formats
- [ ] Tool Integration Tests
  - [ ] API compatibility
  - [ ] CrewAI integration
  - [ ] Error handling
- [ ] Performance Tests
  - [ ] Response time benchmarks
  - [ ] Memory usage
  - [ ] Cache effectiveness

## Implementation Examples

### 1. Base Models (`notion/tools/models/`)
```python
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

class PageParent(BaseModel):
    type: ParentType
    id: str = Field(validation_alias="page_id")
    model_config = ConfigDict(strict=True, populate_by_name=True)

class PageProperties(BaseModel):
    title: str = Field(..., min_length=1)
    icon: Optional[str] = None
    cover: Optional[str] = None
    model_config = ConfigDict(strict=True)
```

### 2. Tool Classes (`notion/tools/`)
```python
from crewai.tools import BaseTool
from pydantic import ValidationError

class NotionBaseTool(BaseTool):
    def _handle_validation_error(self, error: ValidationError) -> Dict[str, Any]:
        return self._format_response(
            success=False,
            message="Validation error",
            error=error.errors()
        )
```

## Checkpoints and Reviews

### Mid-Sprint Checkpoint
- [x] Review with Archie:
  - [x] Verify NotionBaseTool implementation
  - [x] Validate shared models design
  - [x] Confirm Django API client integration
  - [x] Address any blockers or concerns
  - [x] Get approval to proceed with CRUD tools

### Final Sprint 1 Checkpoint
- [ ] Run and verify coverage report
- [ ] Complete core documentation
- [ ] Address any critical bugs
- [ ] Review improvements for Sprint 2:
  - [ ] Pagination support (NOTION-123)
  - [ ] Template system (NOTION-126)
  - [ ] Optimistic locking (NOTION-129)
  - [ ] Recursive deletion (NOTION-132)

## Definition of Done
- [x] All core tools implemented and tested
- [ ] Test coverage meets 90% requirement
- [x] Code passes type checking
- [ ] Documentation is complete
- [ ] No known critical bugs

## Notes
- Reuse existing API client from Django commands
- Maintain consistent response format
- Focus on tool functionality first, optimization later
- Use type hints and docstrings for better agent interaction
# Sprint 1: Foundation & Core Tools Checklist

## Original Core Tasks

### 1. Base Tool Implementation
- [x] Create NotionBaseTool class (`tools/base.py`)
  - [x] Implement API client integration from Django commands
  - [x] Add standardized response formatting
  - [x] Implement error handling patterns
  - [x] Add type hints and docstrings

### 2. Shared Models (`tools/models/`)
- [x] Create base Pydantic models
  - [x] PageParent model
  - [x] PageProperties model
  - [x] PageResponse model
  - [x] BlockContent model

### 3. Core Page Operations
#### ListPagesTool (`tools/page/list_pages.py`)
- [x] Create ListPagesInput schema
- [x] Implement tool class
- [x] Add database filtering support
- [x] Implement page formatting
- [x] Add error handling

#### CreatePageTool (`tools/page/create_page.py`)
- [x] Create PageUpdateInput schema
- [x] Implement tool class
- [x] Handle parent types (workspace/page/database)
- [x] Add error handling

#### UpdatePageTool (`tools/page/update_page.py`)
- [x] Create UpdatePageInput schema
- [x] Implement tool class
- [x] Support property updates
- [x] Add error handling

#### DeletePageTool (`tools/page/delete_page.py`)
- [x] Create DeletePageInput schema
- [x] Implement tool class
- [x] Add error handling

### 4. Testing Infrastructure
- [x] Set up pytest configuration
  - [x] Configure coverage settings
  - [x] Add test markers
  - [x] Set up branch coverage
  - [x] Configure concurrency support
- [x] Create test fixtures
  - [x] Mock Notion API client
  - [x] Sample page data
  - [x] Error scenarios
  - [x] Mock API response collection
- [x] Implement unit tests for each tool
  - [x] Base tool tests
  - [x] Model tests
  - [x] Page operation tools tests
- [ ] Set up test coverage reporting (90% target)
  - [ ] Run initial coverage report
  - [ ] Address any coverage gaps
  - [ ] Verify 90% requirement met

## Pydantic V2 Migration Plan

### 1. Setup and Tools
- [x] Install migration tools:
  ```bash
  pip install bump-pydantic
  cd /Users/yp/Code/_CODER
  bump-pydantic notion/
  ```

### 2. Model Updates Required
#### Base Model Changes
```python
# Update model configs
model_config = ConfigDict(
    populate_by_name=True,
    validate_assignment=True,
    strict=True
)

# Update validator syntax
@field_validator('field')
@classmethod
def check_field(cls, v):
    return v

# Update type hints
field: str | None = None  # Instead of Optional[str]
required_field: str = Field(...)
```

#### Specific Model Updates
- [x] Update PageParent model
- [x] Update PageProperties model
- [x] Update PageResponse model
- [x] Update BlockContent model

### 3. Error Handling Updates
- [x] Implement standardized NotionError class
- [x] Update all models to use consistent error handling
- [x] Add comprehensive validation in from_notion_format methods
- [x] Improve error messages for better debugging

## Testing Strategy

### 1. Coverage Requirements
- Unit Tests: 90% coverage
- Integration Tests: 80% coverage
- Error Cases: 100% coverage

### 2. Test Categories
- [x] Model Validation Tests
  - [x] Field validation
  - [x] Type conversion
  - [x] Error formats
- [ ] Tool Integration Tests
  - [ ] API compatibility
  - [ ] CrewAI integration
  - [ ] Error handling
- [ ] Performance Tests
  - [ ] Response time benchmarks
  - [ ] Memory usage
  - [ ] Cache effectiveness

## Implementation Examples

### 1. Base Models (`notion/tools/models/`)
```python
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

class PageParent(BaseModel):
    type: ParentType
    id: str = Field(validation_alias="page_id")
    model_config = ConfigDict(strict=True, populate_by_name=True)

class PageProperties(BaseModel):
    title: str = Field(..., min_length=1)
    icon: Optional[str] = None
    cover: Optional[str] = None
    model_config = ConfigDict(strict=True)
```

### 2. Tool Classes (`notion/tools/`)
```python
from crewai.tools import BaseTool
from pydantic import ValidationError

class NotionBaseTool(BaseTool):
    def _handle_validation_error(self, error: ValidationError) -> Dict[str, Any]:
        return self._format_response(
            success=False,
            message="Validation error",
            error=error.errors()
        )
```

## Checkpoints and Reviews

### Mid-Sprint Checkpoint
- [x] Review with Archie:
  - [x] Verify NotionBaseTool implementation
  - [x] Validate shared models design
  - [x] Confirm Django API client integration
  - [x] Address any blockers or concerns
  - [x] Get approval to proceed with CRUD tools

### Final Sprint 1 Checkpoint
- [ ] Run and verify coverage report
- [ ] Complete core documentation
- [ ] Address any critical bugs
- [ ] Review improvements for Sprint 2:
  - [ ] Pagination support (NOTION-123)
  - [ ] Template system (NOTION-126)
  - [ ] Optimistic locking (NOTION-129)
  - [ ] Recursive deletion (NOTION-132)

## Definition of Done
- [x] All core tools implemented and tested
- [ ] Test coverage meets 90% requirement
- [ ] Code passes type checking
- [ ] Documentation is complete
- [ ] No known critical bugs

## Notes
- Reuse existing API client from Django commands
- Maintain consistent response format
- Focus on tool functionality first, optimization later
- Use type hints and docstrings for better agent interaction

## Testing Implementation Guide

### 1. Coverage Configuration
```bash
# Basic coverage report
pytest notion/tests/ --cov=notion --cov-report=term-missing --cov-branch

# Detailed HTML report for analysis
pytest notion/tests/ --cov=notion --cov-report=html --cov-branch

# With specific test markers for categories
pytest notion/tests/ -v -m "not integration" --cov=notion --cov-report=term-missing --cov-branch
```

### 2. Test Patterns Example
```python
class TestPageParentAPI:
    """Test suite for PageParent API integration."""
    
    def test_parse_valid_api_response(self, mock_notion_client):
        """Test parsing valid API response."""
        # Given: A typical Notion API response
        api_response = {
            "type": "page_id",
            "page_id": "test-page-123",
            "workspace": False
        }
        
        # When: Parsing the response
        parent = PageParent.from_notion_format(api_response)
        
        # Then: Model should be correctly populated
        assert parent.type == ParentType.PAGE
        assert parent.id == "test-page-123"

    def test_parse_malformed_api_response(self, mock_notion_client):
        """Test handling malformed API response."""
        # Given: A malformed API response
        api_response = {
            "type": "page_id",
            # Missing page_id field
        }
        
        # When/Then: Should raise appropriate error
        with pytest.raises(NotionError) as exc_info:
            PageParent.from_notion_format(api_response)
        
        assert exc_info.value.error_type == "validation"
        assert exc_info.value.status_code == 400
        assert "Missing parent ID" in str(exc_info.value)

    @pytest.mark.parametrize("api_response,expected_error", [
        (
            {"type": "invalid_type", "page_id": "123"},
            "Unsupported parent type"
        ),
        (
            {"type": "page_id", "page_id": ""},
            "Empty page ID not allowed"
        ),
        (
            {"type": "workspace", "page_id": "123"},
            "Workspace parent cannot have ID"
        )
    ])
    def test_edge_cases(self, api_response, expected_error):
        """Test various edge cases in API responses."""
        with pytest.raises(NotionError) as exc_info:
            PageParent.from_notion_format(api_response)
        assert expected_error in str(exc_info.value)

    def test_large_response_handling(self):
        """Test handling unusually large responses."""
        # Given: A response with unusually long ID
        long_id = "a" * 1000
        api_response = {
            "type": "page_id",
            "page_id": long_id
        }
        
        # When/Then: Should handle gracefully or raise appropriate error
        with pytest.raises(NotionError) as exc_info:
            PageParent.from_notion_format(api_response)
        assert "ID exceeds maximum length" in str(exc_info.value)

    def test_null_handling(self):
        """Test handling of null values in API response."""
        api_response = {
            "type": "page_id",
            "page_id": None
        }
        
        with pytest.raises(NotionError) as exc_info:
            PageParent.from_notion_format(api_response)
        assert "NULL value not allowed for page_id" in str(exc_info.value)
```

### 3. Testing Focus Areas
- Response parsing logic
- Error handling paths
- Type conversions
- Validation rules
- Edge cases
- NULL/empty value handling

### 4. Test Organization Principles
- Clear Given/When/Then structure
- Descriptive test names explaining the scenario
- Well-organized test classes
- Fixtures for common test data
- Both success and failure cases
- Edge cases and boundary conditions