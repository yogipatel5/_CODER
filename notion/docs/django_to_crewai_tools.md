# Converting Django Management Commands to CrewAI Tools

This guide provides a comprehensive approach to converting Django management commands into CrewAI tools, enabling AI agents to interact with your Django application's functionality.

## Table of Contents
1. [Understanding the Components](#understanding-the-components)
2. [Conversion Strategy](#conversion-strategy)
3. [Implementation Patterns](#implementation-patterns)
4. [Best Practices](#best-practices)
5. [Examples](#examples)
6. [Testing and Validation](#testing-and-validation)

## Understanding the Components

### Django Management Commands
- Command-line interface for Django applications
- Structured with `handle()` method for execution
- Arguments defined in `add_arguments()`
- Access to Django's ORM and application context

### CrewAI Tools
- Function or class-based tools for AI agents
- Input validation with Pydantic models
- Structured responses for AI consumption
- Caching capabilities for optimization

## Conversion Strategy

### 1. Analysis Phase
- Identify command purpose and functionality
- Map command arguments to tool inputs
- Define expected output structure
- Determine required Django context

### 2. Design Decisions
Choose the appropriate tool pattern:
1. **Function Decorator Pattern**
   ```python
   @tool("Command Name")
   def command_tool(argument: str) -> str:
       """For simple, single-purpose commands"""
   ```

2. **BaseTool Class Pattern**
   ```python
   class CommandTool(BaseTool):
       """For complex commands with multiple options"""
   ```

3. **Structured Tool Pattern**
   ```python
   class CommandInput(BaseModel):
       """For commands requiring input validation"""
   ```

### 3. Context Management
- Handle Django setup requirements
- Manage database connections
- Handle authentication/permissions
- Maintain transaction integrity

## Implementation Patterns

### Pattern 1: Direct Conversion
For commands that don't require Django context:
```python
@tool("List Items")
def list_items_tool(query: str) -> List[Dict]:
    # Direct conversion of command logic
```

### Pattern 2: Context-Aware Conversion
For commands requiring Django context:
```python
class DjangoContextTool(BaseTool):
    def setup_django(self):
        # Django setup code
```

### Pattern 3: Hybrid Approach
For commands needing both:
```python
class HybridTool(BaseTool):
    def _run(self, **kwargs):
        with django_context():
            # Command logic
```

## Best Practices

### 1. Input Validation
- Use Pydantic models for argument validation
- Match Django command arguments
- Provide clear error messages
- Example:
  ```python
  class CommandInput(BaseModel):
      argument: str = Field(..., description="Clear description")
  ```

### 2. Output Standardization
- Consistent response format
- Error handling patterns
- Status indicators
- Example:
  ```python
  {
      "success": bool,
      "data": Any,
      "error": Optional[str]
  }
  ```

### 3. Error Handling
- Catch Django-specific exceptions
- Provide AI-friendly error messages
- Maintain audit trail
- Example:
  ```python
  try:
      # Command logic
  except CommandError as e:
      return {"success": False, "error": str(e)}
  ```

### 4. Caching Strategy
- Implement tool-specific caching
- Consider Django cache backend
- Cache invalidation rules
- Example:
  ```python
  def cache_function(args, result):
      return should_cache(result)
  ```

## Examples

### Basic Command Conversion
```python
# From Django Command:
class Command(BaseCommand):
    def handle(self, *args, **options):
        # logic here

# To CrewAI Tool:
@tool("Command Name")
def command_tool(argument: str) -> str:
    # same logic here
```

### Complex Command Conversion
```python
# From Django Command:
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--option', type=str)

# To CrewAI Tool:
class ComplexCommandTool(BaseTool):
    name = "Complex Command"
    args_schema = CommandInput
```

## Testing and Validation

### 1. Unit Testing
- Test tool inputs/outputs
- Validate Django context
- Mock database operations
- Example:
  ```python
  def test_tool_execution():
      tool = CommandTool()
      result = tool.run(input_data)
      assert result["success"]
  ```

### 2. Integration Testing
- Test with CrewAI agents
- Validate Django integration
- Check error handling
- Example:
  ```python
  def test_agent_interaction():
      agent = Agent(tools=[CommandTool()])
      result = agent.execute_task()
  ```

### 3. Performance Testing
- Measure execution time
- Monitor resource usage
- Validate caching
- Example:
  ```python
  def test_tool_performance():
      with performance_monitor():
          tool.run(input_data)
  ```

## Conclusion

Converting Django management commands to CrewAI tools requires careful consideration of:
- Command complexity and context requirements
- Input/output standardization
- Error handling and validation
- Performance and caching strategies

Following these patterns and best practices ensures your tools are:
- Reliable and maintainable
- Easy for AI agents to use
- Consistent with both Django and CrewAI patterns
- Well-tested and performant

Remember to:
- Document your tools thoroughly
- Maintain type hints and docstrings
- Consider security implications
- Keep the conversion process consistent

For more examples and patterns, refer to the `tools/` directory in this project. 