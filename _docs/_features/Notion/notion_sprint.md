<!-- Sperry - Inter Sprint Here -->

# Notion AI Agent Implementation Sprint

## Sprint Overview

Duration: 4 days
Goal: Implement a Notion AI agent that can process natural language prompts to interact with Notion through the service layer

## Prerequisites

- [x] Ensure `notion-client`, `pydantic`, `click`, and `python-dotenv` are installed
- [x] Valid Notion API key for testing
- [x] Access to existing `NotionService` implementation (reviewed and available in `services.py`)

## Existing Service Layer Review

The current `NotionService` implementation provides:

- Core Notion API operations (CRUD for pages, blocks, databases)
- Task-specific methods (add_task, update_task_status)
- Type-safe operations using Pydantic models
- Proper error handling and type casting

## Phase 1: Core Integration (Day 1)

### Package Structure Setup

- [x] Create directory structure:

  ```text
  notion/
  ├── __init__.py
  ├── services.py          # Existing service implementation
  ├── agent/
  │   ├── __init__.py
  │   ├── base.py         # New agent implementation
  │   ├── processor.py    # New prompt processor
  │   └── tools/          # New tool implementations
  ├── cli/
  └── config/
  ```

### Base Implementation

- [x] Implement `NotionAgent` class in `agent/base.py`
  - [x] Function: `__init__(self, service: NotionService)`
  - [x] Function: `_initialize_tools(self) -> Dict[str, Any]`
  - [x] Function: `async execute(self, prompt: str) -> Dict[str, Any]` # Now async
  - [x] Test: Create unit test for agent initialization
  - [x] Test: Verify tool initialization

### Service Integration

- [x] Create service connection in `NotionAgent`
  - [x] Utilize existing `NotionService` methods
  - [x] Implement async wrapper methods for service calls
- [x] Implement error handling for service connection
- [x] Test: Verify service connectivity
- [x] Test: Validate error handling for invalid API keys

## Phase 2: Tool Implementation (Day 2-3)

### Pydantic Integration

We'll use these Pydantic features:

- [x] BaseModel for request/response validation
- [x] Field validations with custom validators
- [x] Strict type checking
- [x] JSON schema generation for API documentation

### Day 2: Base Tool Structure (Priority: High)

- [x] Implement `BaseTool` abstract class in `tools/__init__.py`

  - [x] Define `async execute()` abstract method
  - [x] Implement `ToolResult` model with Pydantic

  ```python
  class ToolResult(BaseModel):
      success: bool
      data: Dict[str, Any]
      error: Optional[str] = None
      metadata: Optional[Dict[str, Any]] = None
  ```

  - [x] Test: Verify tool inheritance structure

### Create Page Tool (Priority: High)

- [x] Implement `CreatePageTool` in `tools/create.py`

  - [x] Create `CreatePageParams` model using Pydantic

  ```python
  class CreatePageParams(BaseModel):
      title: str
      content: str
      parent_id: Optional[str] = None
      properties: Optional[Dict[str, Any]] = None
  ```

  - [x] Implement `async execute()` method
  - [x] Add input validation using Pydantic validators
  - [x] Test: Verify page creation
  - [x] Test: Validate error handling

### Read Page Tool (Priority: Medium)

- [x] Implement `ReadPageTool` in `tools/read.py`

  - [x] Create `ReadPageParams` model using Pydantic

  ```python
  class ReadPageParams(BaseModel):
      page_id: str
      include_content: bool = True
  ```

  - [x] Implement `async execute()` method
  - [x] Add input validation
  - [x] Test: Verify page reading
  - [x] Test: Handle non-existent pages

### Day 3: Edit Tool and Processor (Priority: Low)

- [x] Implement `EditPageTool` in `tools/edit.py`

  - [x] Create `EditPageParams` model using Pydantic

  ```python
  class EditPageParams(BaseModel):
      page_id: str
      title: Optional[str] = None
      content: Optional[str] = None
      properties: Optional[Dict[str, Any]] = None
      append_content: bool = False
  ```

  - [x] Implement `async execute()` method
  - [x] Add input validation
  - [x] Test: Verify page editing
  - [x] Test: Handle concurrent edits

### Prompt Processor

- [x] Implement `PromptProcessor` in `processor.py`

  - [x] Function: `async parse(prompt: str) -> Action`
  - [x] Add prompt validation using Pydantic

  ```python
  class Action(BaseModel):
      tool_name: str
      parameters: Dict[str, Any]
      confidence: float
  ```

  - [x] Test: Verify prompt parsing
  - [x] Test: Handle invalid prompts

## Phase 3: CLI & Documentation (Day 4)

### CLI Implementation

- [x] Implement CLI interface in `cli/commands.py`
  - [x] Create `cli()` group
  - [x] Implement async `execute()` command
  - [x] Add environment variable support
  - [x] Test: Verify CLI functionality
  - [x] Test: Validate environment variable handling

### Documentation

- [ ] Add docstrings to all classes and methods
- [ ] Create usage examples
- [ ] Document configuration options
- [ ] Add README.md with setup instructions

### Testing

- [x] Implement integration tests
- [ ] Add test coverage reporting
- [ ] Create test documentation

## Testing Requirements

### Unit Tests

```python
# Required test cases for each component:
async def test_agent_initialization():
    """Test agent initialization with valid service"""

async def test_tool_execution():
    """Test individual tool execution"""

async def test_prompt_processing():
    """Test prompt processing and action generation"""

async def test_cli_commands():
    """Test CLI command execution"""
```

### Integration Tests

```python
# Required integration test cases:
async def test_end_to_end_flow():
    """Test complete flow from prompt to Notion update"""

async def test_error_handling():
    """Test error handling across components"""

async def test_concurrent_operations():
    """Test handling of concurrent operations"""
```

## Definition of Done

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] 90% test coverage
- [ ] Documentation complete
- [ ] Code reviewed and approved
- [ ] No linting errors
- [ ] All TODOs addressed

## Notes

- Use type hints consistently throughout the codebase
- Follow PEP 8 style guide
- Document all public APIs
- Handle rate limiting gracefully
- Implement proper logging
- All operations are async/await for consistency with modern Python practices
- Utilize existing NotionService methods where possible
- Prioritize Create and Read operations before Edit operations

## Questions Addressed

1. **Existing Service Review**: We've reviewed `services.py` and incorporated its functionality into our plan. The existing service provides a solid foundation with type-safe operations.

2. **Pydantic Features**: We'll use Pydantic for:

   - Request/response validation
   - Type safety with BaseModel
   - Custom validators
   - JSON schema generation
   - Field validation and documentation

3. **Tool Prioritization**: Tools are prioritized as:

   - High: Create Page Tool (most common operation)
   - Medium: Read Page Tool (essential for verification)
   - Low: Edit Page Tool (less frequent operation)

4. **Async Implementation**: The entire service will be async for:
   - Consistent programming model
   - Better performance under load
   - Future scalability
   - Integration with modern Python practices

## Phase 4: Pydantic AI Integration

### Goals

- [x] Replace regex-based command processing with Pydantic AI
- [x] Implement natural language understanding
- [x] Add support for complex operations
- [ ] Fix known formatting and content issues
- [ ] Improve error handling and user feedback

### Implementation Plan

1. Integrate Pydantic AI for command processing

   - [x] Create AI models for command understanding
   - [x] Train on example commands and variations
   - [x] Implement context awareness

2. Enhance Content Handling

   - [x] Implement proper block management
   - [x] Add rich text formatting support
   - [x] Fix content duplication issues
   - [x] Preserve formatting and line breaks

3. Improve User Experience

   - [x] Add better error messages
   - [x] Implement progress feedback
   - [x] Create help system
   - [x] Add command suggestions

### Testing Requirements2

- [x] Test natural language variations
- [x] Verify formatting preservation
- [x] Test complex operations
- [x] Validate error handling improvements

### Completed Features

1. Base Agent Implementation

   - [x] Created `NotionAgentV2` class with Pydantic AI integration
   - [x] Implemented dependency management
   - [x] Added streaming response support
   - [x] Added comprehensive error handling

2. Tool Implementation

   - [x] Created `CreatePageTool` with natural language support
   - [x] Created `ReadPageTool` with content handling
   - [x] Created `EditPageTool` with append/replace options
   - [x] Added proper block structure support

3. Testing Coverage

   - [x] Unit tests for all tools
   - [x] Integration tests for agent
   - [x] Error handling tests
   - [x] Natural language processing tests

### Next Steps

1. CLI Integration

   - [ ] Update CLI to use new agent
   - [ ] Add streaming response support
   - [ ] Implement progress indicators
   - [ ] Add help command

2. Documentation

   - [ ] Update README with new features
   - [ ] Add examples for natural language commands
   - [ ] Document configuration options
   - [ ] Create user guide

3. Performance Optimization

   - [ ] Add caching for frequent operations
   - [ ] Implement batch processing
   - [ ] Add rate limiting support
   - [ ] Monitor and log performance metrics
