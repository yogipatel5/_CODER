# Developer Instructions

This app is registered with Django.

apps.py is setting up auto discover for the models, tasks, and admin files.

This app manages the print jobs for the Alfie System.
It will host models for the printers I have on my network and have commands for printing files via links, or files.

## Project Structure Overview

### Admin Files (`admin/`)

- Follow the naming convention: `{model_name}admin.py`
- Each admin file should register its corresponding model

### Tasks (`tasks/`)

- Contains Celery task definitions
- Each task file should focus on a specific domain
- Use appropriate decorators (`@shared_task`)
- Include proper error handling and logging

### Models (`models/`)

- Each model should be in its own file
- Follow Django model best practices
- Complex querying logic should use model managers
- Do not put function or class definitions in models

### Model Managers (`managers/`)

- Contains manager classes for handling model operations
- Each model should have a corresponding manager file
- Keep business logic in services not in managers

### API (`api/`)

- Implement API clients and interfaces here
- Include proper error handling and rate limiting

### Services (`services/`)

- Business logic layer between API and models
- Keep services focused and single-responsibility

### Management Commands (`management/commands/`)

- Custom Django management commands
- Follow the pattern in existing commands
- Include help text and command documentation

## Development Guidelines

1. **Code Organization**

   - Keep related functionality together
   - Follow existing patterns for new files

2. **Documentation**

   - Include docstrings for all classes and methods
   - Keep documentation up-to-date

3. **Error Handling**

   - Implement proper exception handling
   - Use appropriate logging levels

4. **Testing**
   - Write tests for new functionality
   - Include both unit and integration tests
