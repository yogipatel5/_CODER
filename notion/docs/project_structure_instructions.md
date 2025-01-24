# Developer Instructions

This app is registered with Django.

apps.py is setting up auto discover for the models, tasks, and admin files. You do not have to do anything else but create the files.

## Project Structure Overview

### Admin Files (notion/admin)
- Follow the naming convention: `{model_name}admin.py`
- Each admin file should register its corresponding model with the Django admin interface
- Examples: 
  - `notionagentjobadmin.py` for the NotionAgentJob model
  - `taskadmin.py` for the Task model

### Tasks (notion/tasks)
- Contains Celery task definitions
- Each task file should focus on a specific domain of functionality
- Follow the pattern:
  - Use appropriate decorators (`@shared_task`)
  - Include detailed docstrings
  - Implement proper error handling and logging
- Current tasks:
  - `scanning.py`: Tasks for scanning and creating Notion agent jobs
  - `processing.py`: Tasks for processing pending Notion agent jobs

### Models (notion/models)
- Each model should be in its own file
- Follow Django model best practices with proper field definitions and docstrings
- Complex querying logic should use model managers
- Current models:
  - `notionagentjobs.py`: Tracks agent job states and task execution
  - `task.py`: Manages Celery task configurations and schedules
  - `page.py`: Represents Notion page data and metadata
- Do not put function or class definitions in models use separate managers

### Model Managers (notion/managers)
- Contains manager classes for handling complex model operations
- Each model has a corresponding manager file
- Current managers:
  - `notionagentjob.py`: Handles NotionAgentJob operations (e.g., marking tasks complete/failed)
  - `task.py`: Manages Task operations (e.g., active task queries, status toggling)
  - `page.py`: Handles Page operations (e.g., active/archived/trashed page queries)
- Keep business logic in managers, not in models

### API (notion/api)
- `client.py` serves as the central point for all Notion API interactions
- Implement all API calls through the client class
- Include proper error handling and rate limiting
- Use appropriate authentication methods

### Services (notion/services)
- Business logic layer between API and models
- `project.py`: Handles project-related Notion operations
- `notey.py`: Core service functionality
- Keep services focused and single-responsibility

### Management Commands (notion/management/commands)
- Custom Django management commands
- Every task created in Celery should have a corresponding management command without repeating the code.
- Any command corresponding with celery task will have a --celery task option to run it in Celery.
- Follow the pattern in existing commands:
  - Inherit from `base_command.py`
  - Implement `handle()` method
  - Include help text and command documentation

## Development Guidelines

1. **Code Organization**
   - Keep related functionality together
   - Follow existing patterns for new files
   - Use appropriate Django decorators and mixins

2. **Documentation**
   - Include docstrings for all classes and methods
   - Document any complex logic or business rules
   - Keep the documentation up-to-date

3. **Error Handling**
   - Implement proper exception handling
   - Use appropriate logging levels
   - Handle API rate limits and timeouts

4. **Testing**
   - Write tests for new functionality
   - Follow existing test patterns
   - Include both unit and integration tests

5. **Configuration**
   - Use Django settings appropriately
   - Keep sensitive information in environment variables
   - Document any new configuration options