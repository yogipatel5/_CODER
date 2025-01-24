# Project Architecture

## Overview

This document outlines the architectural design of the Coder helper project, with a specific focus on how Django commands are extended through Alfie and how each app is structured. We'll use the GitHub app as our primary example to demonstrate the complete architecture.

## Core Architecture Principles

### 1. Service-Oriented Architecture

- Each app follows a service-oriented pattern
- Clear separation between business logic and data access
- Standardized interface for Alfie CLI integration

### 2. Command Pattern Integration

- Django commands as base functionality
- Alfie CLI as an intelligent wrapper
- Natural language processing for command interpretation

### 3. Component Isolation

- Each app is self-contained with its own services
- Shared utilities through core app
- Standardized interfaces for cross-app communication

## GitHub App Architecture (Template Pattern)

### Directory Structure

```tree
projects/
└── github/
    ├── management/
    │   └── commands/
    │       ├── __init__.py
    │       ├── github_repo.py
    │       ├── github_branch.py
    │       └── github_user.py
    ├── services/
    │   ├── __init__.py
    │   ├── github_service.py
    │   ├── repository_service.py
    │   └── branch_service.py
    ├── managers/
    │   ├── __init__.py
    │   ├── repository_manager.py
    │   └── branch_manager.py
    ├── models/
    │   ├── __init__.py
    │   ├── repository.py
    │   ├── branch.py
    │   └── github_settings.py
    ├── admin/
    │   ├── __init__.py
    │   ├── repository_admin.py
    │   └── github_settings_admin.py
    ├── templates/
    │   └── github_management/
    │       ├── dashboard.html
    │       └── repositories/
    │           ├── list.html
    │           └── detail.html
    ├── api/
    │   ├── __init__.py
    │   ├── views.py
    │   └── serializers.py
    └── tests/
        ├── __init__.py
        ├── test_models/
        │   ├── __init__.py
        │   ├── test_repository.py
        │   ├── test_branch.py
        │   └── test_github_settings.py
        ├── test_services/
        │   ├── __init__.py
        │   ├── test_github_service.py
        │   ├── test_repository_service.py
        │   └── test_branch_service.py
        ├── test_managers/
        │   ├── __init__.py
        │   ├── test_repository_manager.py
        │   └── test_branch_manager.py
        ├── test_commands/
        │   ├── __init__.py
        │   ├── test_github_repo.py
        │   ├── test_github_branch.py
        │   └── test_github_user.py
        └── test_api/
            ├── __init__.py
            ├── test_views.py
            └── test_serializers.py
```

### Component Details

#### 1. Models

```python
# models/repository.py
class Repository(models.Model):
    name = models.CharField(max_length=255)
    github_id = models.IntegerField(unique=True)
    url = models.URLField()
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    settings = models.ForeignKey('GithubSettings', on_delete=models.CASCADE)

# models/github_settings.py
class GithubSettings(models.Model):
    token = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    default_branch = models.CharField(max_length=50, default='main')
```

#### 2. Services

```python
# services/github_service.py
class GithubService:
    def __init__(self, settings: GithubSettings):
        self.settings = settings
        self.client = Github(settings.token)

    async def create_repository(self, name: str, is_private: bool = True) -> Repository:
        # Implementation

    async def delete_repository(self, repo_name: str) -> bool:
        # Implementation
```

#### 3. Managers

```python
# managers/repository_manager.py
class RepositoryManager:
    def __init__(self, service: GithubService):
        self.service = service

    def create_repository_with_template(self, name: str, template: str) -> Repository:
        # High-level business logic
```

#### 4. Django Commands

```python
# management/commands/github_repo.py
class Command(BaseCommand):
    help = 'Manage GitHub repositories'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['create', 'delete', 'list'])
        parser.add_argument('--name', type=str)

    def handle(self, *args, **options):
        # Command implementation
```

#### 5. Alfie CLI Integration

```python
# alfie/commands/github.py
class GithubCommand(AlfieBaseCommand):
    """
    Natural language interface for GitHub operations
    """
    def process_command(self, text: str) -> str:
        # Parse natural language
        intent = self.nlp.parse_intent(text)

        # Map to Django command
        if intent.action == "create_repository":
            return self.run_django_command(
                "github_repo",
                "create",
                name=intent.parameters.get("name")
            )
```

### Admin Interface

```python
# admin/repository_admin.py
@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'is_private', 'created_at']
    search_fields = ['name']
    list_filter = ['is_private', 'created_at']

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ['github_id', 'created_at']
        return ['created_at']
```

## Alfie CLI Architecture

### Command Processing Flow

1. **Natural Language Input**

   ```bash
   alfie create new github repository myproject
   ```

2. **Intent Recognition**

   - Parse natural language
   - Extract parameters
   - Map to specific app command

3. **Command Execution**
   - Convert to Django command
   - Execute with parameters
   - Handle response

### Integration Pattern

```python
# alfie/base.py
class AlfieBaseCommand:
    def __init__(self):
        self.nlp = NLPProcessor()
        self.command_registry = CommandRegistry()

    async def execute(self, text: str) -> CommandResult:
        intent = self.nlp.parse(text)
        command = self.command_registry.get_command(intent)
        return await command.execute(intent.parameters)
```

## Service Layer Pattern

### Base Service

```python
# core/services/base.py
class BaseService:
    def __init__(self, settings: dict):
        self.settings = settings
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, action: str, **kwargs) -> Any:
        method = getattr(self, action, None)
        if not method:
            raise NotImplementedError(f"Action {action} not implemented")
        return await method(**kwargs)
```

### Manager Pattern

```python
# core/managers/base.py
class BaseManager:
    def __init__(self, service: BaseService):
        self.service = service

    def validate(self, action: str, **kwargs) -> bool:
        # Validation logic
        pass

    async def execute(self, action: str, **kwargs) -> Any:
        if not self.validate(action, **kwargs):
            raise ValidationError(f"Invalid parameters for {action}")
        return await self.service.execute(action, **kwargs)
```

## Future Considerations

### 1. Scalability

- Implement caching layer
- Add background task processing
- Consider message queue for long-running operations

### 2. Monitoring

- Add telemetry to services
- Implement performance tracking
- Set up alerting for failures

### 3. Security

- Implement rate limiting
- Add audit logging
- Enhance authentication mechanisms

### 4. Testing

- Unit tests for services
- Integration tests for managers
- End-to-end tests for commands
- Testing using Alfie CLI
- Testing using sample project yaml file
