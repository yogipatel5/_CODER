# Notion Integration

A Django app for integrating with Notion and processing Notion pages with AI agents.

## Directory Structure

```
notion/
├── api/                    # Notion API integration
│   ├── __init__.py
│   └── client.py          # Notion API client
├── core/                  # Core business logic
│   ├── __init__.py
│   └── services.py       # Business logic services
├── management/           # Django management commands
│   └── commands/
│       └── scan_notion.py
├── models/              # Database models
│   ├── __init__.py
│   └── agent_job.py    # NotionAgentJob model
├── tasks/              # Background tasks
│   ├── __init__.py
│   ├── scanning.py    # Notion scanning tasks
│   └── processing.py  # Job processing tasks
├── tests/             # Test suite
│   ├── __init__.py
│   └── test_models.py
├── admin.py          # Django admin configuration
├── apps.py          # Django app configuration
└── config.py       # App configuration settings
```

## Setup

1. Add the app to your Django INSTALLED_APPS:

```python
INSTALLED_APPS = [
    ...
    'notion',
]
```

2. Configure your Notion API key in Django settings:

```python
NOTION_API_KEY = 'your-api-key'
```

3. Run migrations:

```bash
python manage.py migrate
```

## Usage

To scan Notion for new tasks:

```bash
python manage.py scan_notion
```

## Development

Run tests:

```bash
python manage.py test notion
```
