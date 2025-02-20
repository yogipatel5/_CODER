# shipper

This app is registered with Django.

## Project Structure

```text
shipper/
├── README.md                  # This file
├── __init__.py               # Package initialization
├── admin/                    # Django admin interfaces
│   ├── __init__.py
│   └── {model}admin.py       # Admin interface for each model
├── api/                      # API clients and interfaces
│   ├── __init__.py
│   ├── client.py            # Base API client
│   ├── exceptions.py        # Custom API exceptions
│   └── endpoints/           # Endpoint-specific clients
│       ├── __init__.py
│       └── example.py       # Example endpoint client
├── apps.py                  # Django app configuration
├── managers/                # Model managers
│   ├── __init__.py
│   └── {model}_manager.py  # Manager for each model
├── management/              # Django management commands
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       ├── create_task.py
│       ├── show_imports.py
│       └── show-imports.py  # Symlink for kebab-case support
├── migrations/              # Database migrations
│   └── __init__.py
├── models/                  # Django models
│   ├── __init__.py         # Auto-discovers all models
│   └── {model}.py          # One model per file
├── services/               # Business logic services
│   ├── __init__.py
│   ├── base_service.py    # Base service class
│   └── {domain}/         # Domain-specific services
│       ├── __init__.py
│       └── service.py
├── signals/               # Django signal handlers
│   ├── __init__.py       # Auto-discovers all signals
│   └── {model}_signals.py # Signals for each model
├── tasks/                # Celery tasks
│   ├── __init__.py      # Auto-discovers all tasks
│   ├── base_task.py     # Base task class
│   └── {domain}_task.py # Domain-specific tasks
└── tests/               # Unit and integration tests
    ├── __init__.py
    ├── conftest.py     # pytest configuration
    ├── factories/      # Model factories
    │   └── __init__.py
    └── {domain}/      # Domain-specific tests
        └── __init__.py
```

## Auto-Discovery System

The app uses an advanced auto-discovery system that automatically imports:

1. **Models**: All models are automatically discovered from the `models/` directory

   - Each model should be in its own file
   - No need to import models in `models/__init__.py`
   - Access models using either:
     ```python
     from shipper.models import MyModel  # Package import
     from shipper.models.my_model import MyModel  # Direct import
     ```

2. **Tasks**: Celery tasks are automatically discovered from the `tasks/` directory

   - Each task should be in its own file
   - Base classes (e.g., `base_task.py`) are excluded from auto-discovery
   - Access tasks using:
     ```python
     from shipper.tasks import my_task
     ```

3. **Signals**: Signal handlers are automatically discovered from the `signals/` directory
   - Each signal file should handle signals for a specific model
   - Signal handlers are marked with `@receiver` decorator
   - Access signals using:
     ```python
     from shipper.signals import my_signal_handler
     ```

Use the `show_imports` command to see all discovered components:

```bash
python manage.py shipper show_imports  # or show-imports
```

## Project Structure Overview

### Admin Files (`admin/`)

- Follow the naming convention: `{model_name}admin.py`
- Each admin file should register its corresponding model
- Admin interfaces should provide clear task status and execution history
- Use human-readable time formats for task schedules

### Tasks (`tasks/`)

- Contains Celery task definitions
- Each task file should focus on a specific domain
- Use appropriate decorators (`@shared_task`)
- Include proper error handling and logging
- Tasks should update their status in the Task model
- Use the `create_task` management command to set up new tasks:
  ```bash
  python manage.py shipper create_task task_name app.tasks.task_function --schedule-type hours --schedule-every 1
  ```

### Models (`models/`)

- Each model should be in its own file
- Follow Django model best practices
- Complex querying logic should use model managers
- Do not put function or class definitions in models
- Task model provides:
  - Task execution tracking
  - Integration with Celery Beat
  - Error logging and notifications
  - Human-readable schedules

### Signals (`signals/`)

- Contains Django signal handlers for models
- Follow the naming convention: `{model_name}_signals.py`
- Each signal file should handle signals for a specific model
- Keep signal handlers focused on event handling
- Avoid putting business logic in signals
- Use signals for:
  - Reactive behaviors (e.g., updating related data)
  - Event handling (e.g., post_save, pre_delete)
  - Triggering async tasks
- Example: `page_signals.py` for Page model signals

### Model Managers (`managers/`)

- Contains manager classes for handling model operations
- Each model should have a corresponding manager file
- Keep business logic in services not in managers
- Task manager handles:
  - Task status updates
  - Schedule management
  - Error tracking

### Services (`services/`)

Services handle complex business logic and external integrations. Follow these patterns:

1. **Base Service Classes**:

   - Create base classes for common functionality in `base_service.py`
   - Use dependency injection for flexibility and testing
   - Include logging and error handling

2. **Service Organization**:

   - One service class per major functionality
   - Group related services in subdirectories (e.g., `services/niimprint/`)
   - Keep services focused on business logic

3. **Service Patterns**:

   ```python
   class PrintService:
       def __init__(self, config=None):
           self.config = config or {}
           self.logger = logging.getLogger(__name__)

       def process_job(self, job):
           """Main business logic method."""
           try:
               # Pre-processing
               self._validate_job(job)

               # Core logic
               result = self._execute_job(job)

               # Post-processing
               self._handle_result(result)

           except Exception as e:
               self.logger.error(f"Job failed: {e}")
               self._handle_error(e)
   ```

4. **Service Best Practices**:
   - Use private methods for implementation details
   - Include comprehensive logging
   - Handle all exceptions gracefully
   - Document public methods thoroughly
   - Use type hints for better IDE support

### API (`api/`)

The API package handles external API integrations and provides internal APIs:

1. **API Client Structure**:

   ```text
   api/
   ├── __init__.py
   ├── client.py          # Base API client
   ├── exceptions.py      # Custom API exceptions
   └── endpoints/         # Endpoint-specific clients
       ├── __init__.py
       └── example.py     # Example endpoint client
   ```

2. **Client Implementation**:

   ```python
   class APIClient:
       def __init__(self, base_url, api_key=None):
           self.base_url = base_url
           self.api_key = api_key
           self.session = self._create_session()

       def _create_session(self):
           """Create and configure requests session."""
           session = requests.Session()
           session.headers.update({
               "Authorization": f"Bearer {self.api_key}",
               "Content-Type": "application/json",
           })
           return session

       def _handle_response(self, response):
           """Handle API response and errors."""
           try:
               response.raise_for_status()
               return response.json()
           except requests.exceptions.HTTPError as e:
               raise APIError(f"HTTP {response.status_code}: {str(e)}")
   ```

3. **Endpoint Implementation**:

   ```python
   class ExampleEndpoint:
       def __init__(self, client: APIClient):
           self.client = client
           self.base_path = "/api/v1/example"

       def get_items(self, query: Optional[str] = None) -> List[Dict]:
           """Get items from the endpoint."""
           try:
               params = {"q": query} if query else {}
               return self.client.get(f"{self.base_path}/items", params=params)
           except Exception as e:
               raise APIError(f"Failed to get items: {str(e)}")
   ```

4. **API Best Practices**:

   - Use custom exceptions for API errors
   - Implement proper rate limiting
   - Include retry logic for transient failures
   - Add comprehensive logging
   - Use async where appropriate
   - Cache responses when possible

5. **Endpoint Organization**:
   - One endpoint class per external service/API
   - Keep endpoints focused and single-responsibility
   - Include comprehensive docstrings and type hints
   - Handle all errors consistently
   - Use dataclasses or Pydantic models for request/response data

### Management Commands (`management/commands/`)

Commands provide CLI interfaces to your app's functionality. Follow these patterns:

1. **Command Structure**:

   ```python
   class Command(BaseCommand):
       help = "Clear description of command purpose"

       def add_arguments(self, parser):
           parser.add_argument("required_arg", help="Description")
           parser.add_argument(
               "--optional-arg",
               default="value",
               help="Description with default",
           )

       def handle(self, *args, **options):
           try:
               # Command logic here
               self.stdout.write(self.style.SUCCESS("Success message"))
           except Exception as e:
               self.stderr.write(self.style.ERROR(f"Error: {e}"))
   ```

2. **Command Types**:

   - **Data Management**: Import/export data (`load_printers`)
   - **System Management**: Manage app state (`create_task`)
   - **Maintenance**: Clean up, verify data (`cleanup_jobs`)
   - **Development**: Debug, inspect state (`show_imports`)
   - **Integration**: External system setup (`discover_printers`)

3. **Command Best Practices**:

   - Use descriptive help text
   - Support both naming styles (`show_imports`/`show-imports`)
   - Include progress indicators for long operations
   - Provide dry-run options for destructive operations
   - Add verbose output options
   - Handle all errors gracefully
