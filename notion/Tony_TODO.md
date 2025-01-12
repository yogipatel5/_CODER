# Notion Agent Implementation TODO

## Goal
Create a working end-to-end test of Notion agent using CrewAI that:
1. Accepts commands via Django management command
2. Executes actions in Notion
3. Verifies results through existing notion commands

## Research Notes

### Task 1: Create Basic Agent Command
#### Key Questions
1. **Agent Configuration**
   - How will we structure the agent's role, goal, and backstory for Notion tasks?
   - Should we use YAML configuration (recommended by CrewAI) or direct code definition?
   - What specific attributes do we need for a Notion agent?

2. **Command Structure**
   - How do we integrate CrewAI's agent with Django's command system?
   - What command-line arguments do we need besides the prompt?
   - How to handle agent responses in the command context?

3. **Tool Integration**
   - How will we wrap existing Notion commands as CrewAI tools?
   - Should we use synchronous or asynchronous tool execution?
   - How to handle tool errors and retries?

4. **Memory Implementation**
   - Memory Architecture:
     ```python
     from django.db import models
     
     class NotionAgentMemory(models.Model):
         """Long-term memory storage for Notion agent"""
         created_at = models.DateTimeField(auto_now_add=True)
         updated_at = models.DateTimeField(auto_now=True)
         memory_type = models.CharField(max_length=50)  # 'task_pattern', 'entity', etc.
         key = models.CharField(max_length=255)
         value = models.JSONField()
         embedding = models.BinaryField(null=True)  # For vector similarity search
         
         class Meta:
             indexes = [
                 models.Index(fields=['memory_type', 'key']),
                 models.Index(fields=['created_at'])
             ]
     ```
   
   - Memory Strategy:
     1. Short-term: Use CrewAI's default RAG with OpenAI embeddings (in-memory for session)
     2. Long-term: Store in PostgreSQL
        - Task patterns and outcomes
        - Entity relationships
        - User preferences
     3. Entity Memory: Track Notion entities in PostgreSQL with embeddings
        - Page hierarchies
        - Database structures
        - Common operations
     4. Memory Migration: Add Django migration for memory table

   - Memory Integration:
     ```python
     from crewai import Crew
     from .models import NotionAgentMemory
     
     class NotionCrew:
         def __init__(self):
             self.crew = Crew(
                 agents=[notion_agent],
                 tasks=[handle_request],
                 process=Process.sequential,
                 memory=True,
                 verbose=True,
                 embedder={
                     "provider": "openai",
                     "config": {
                         "model": 'text-embedding-3-small'
                     }
                 }
             )
             
         def store_long_term_memory(self, memory_type, key, value, embedding=None):
             """Store memory in PostgreSQL"""
             NotionAgentMemory.objects.create(
                 memory_type=memory_type,
                 key=key,
                 value=value,
                 embedding=embedding
             )
     ```

#### Memory-Related Command Arguments
```python
def add_arguments(self, parser):
    parser.add_argument('--prompt', required=True, help='Instruction for the agent')
    parser.add_argument('--verbose', action='store_true', help='Enable detailed logging')
    parser.add_argument('--reset-memory', action='store_true', help='Reset agent memory before execution')
    parser.add_argument('--no-memory', action='store_true', help='Disable memory for this execution')
```

#### Initial Decisions
1. **Configuration Approach**
   - Use YAML configuration for better maintainability
   - Store agent config in `notion/config/agents.yaml`
   - Keep agent attributes focused on Notion operations

2. **Command Structure**
   ```python
   class Command(NotionBaseCommand):
       help = "Execute Notion operations using AI agent"
       
       def add_arguments(self, parser):
           parser.add_argument('--prompt', required=True, help='Instruction for the agent')
           parser.add_argument('--verbose', action='store_true', help='Enable detailed logging')
           
       def handle(self, *args, **options):
           # Initialize agent
           # Process prompt
           # Execute actions
           # Return results
   ```

3. **Tool Integration Plan**
   - Wrap existing Notion commands as CrewAI BaseTool classes
   - Use synchronous execution initially
   - Implement basic error handling and retries

#### Open Questions
1. Do we need conversation history for the command-line interface?
2. How should we handle long-running operations?
3. What's the best way to format agent responses for command-line output?
4. Should we implement custom memory storage for specific Notion entities?
5. How do we handle memory persistence between Django command calls?

## Implementation Steps

### 1. Create Basic Agent Command (Priority: High)
- [ ] Create `notion/management/commands/agent.py`
  - Implement new subcommand for agent interaction
  - Add command-line argument for prompt/instruction
  - Integrate with existing command structure
  
### 2. Implement CrewAI Setup (Priority: High)
- [ ] Create `notion/crew/notion_crew.py`
  - Basic CrewAI implementation
  - Tool integration
  - Response handling

### 3. Create Test Scenario (Priority: High)
- [ ] Create `notion/tests/test_agent_e2e.py`
  ```python
  def test_agent_create_and_verify():
      # 1. Use management command to trigger agent
      call_command('notion', 'agent', 
                  '--prompt', 'Create a new page titled "Test Page" with content "Hello World"')
      
      # 2. Use existing get_page command to verify
      result = call_command('notion', 'get_page', 
                          '--title', 'Test Page')
      
      # 3. Assert content matches
      assert "Hello World" in result
  ```

### 4. Tool Implementation (Priority: High)
- [ ] Create basic Notion tools:
  - Create page tool
  - Read page tool
  - Update page tool
- [ ] Integrate with existing Notion commands

### 5. Configuration (Priority: Medium)
- [ ] Create `notion/config/agents.yaml`:
  ```yaml
  notion_agent:
    name: "Notion Assistant"
    role: "Creates and manages Notion pages"
    goal: "Execute user requests accurately"
  ```
- [ ] Create `notion/config/tasks.yaml`

## Test Scenario Steps
1. Start with command: `python manage.py notion agent --prompt "Create a page titled 'Meeting Notes' with content 'Discuss project timeline'""`
2. Agent should:
   - Parse the instruction
   - Use CrewAI to execute appropriate tools
   - Create the page in Notion
3. Verify with: `python manage.py notion get_page --title "Meeting Notes"`
4. Compare output content

## Files to Create/Modify

### New Files
1. `notion/management/commands/agent.py`
2. `notion/crew/notion_crew.py`
3. `notion/crew/tools/notion_tools.py`
4. `notion/tests/test_agent_e2e.py`
5. `notion/config/agents.yaml`
6. `notion/config/tasks.yaml`

### Existing Files to Modify
1. `notion/management/commands/notion.py` (add agent subcommand)

## Success Criteria
1. Command `python manage.py notion agent --prompt "..."` works
2. Agent correctly interprets and executes commands
3. Results can be verified with existing notion commands
4. Tests pass and demonstrate end-to-end functionality

## Next Steps After Completion
1. Add more sophisticated prompts
2. Implement error handling
3. Add conversation history
4. Prepare for Alfie integration

## Notes
- Focus on getting basic end-to-end flow working first
- Use existing command structure
- Keep it simple but extensible
- Document all assumptions and decisions 