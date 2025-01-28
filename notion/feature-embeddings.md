# Notion Page Embeddings Feature - Alpha Sprint

## Overview

Alpha implementation of Notion page embeddings functionality focusing on core features and essential error handling.

## Architecture Flow

1. Page Update → Django Signal
2. Signal Handler → Celery Task
3. Celery Task → Embeddings Service
4. Embeddings Service → Update Page Model

## Critical Tasks

### 1. EmbeddingsService Enhancement (`services/embeddings.py`)

#### Task 1.1: Essential Error Handling

- [x] Replace print statements with proper logging
  - Added structured logging with proper levels (info, warning, error)
  - Using Python's built-in logging module
- [x] Add basic exception handling for OpenAI API errors
  - Added specific handling for openai.APIError
  - Improved error messages with context
- [x] Implement simple retry mechanism
  - Added tenacity-based retry mechanism
  - 3 attempts with exponential backoff (4-10s)

#### Task 1.2: Basic Optimization

- [x] Add content preprocessing
  - Added max_content_length validation (8192 chars)
  - Content is truncated if exceeds limit
- [x] Add validation for maximum content length
  - Implemented in update_page_embeddings
  - Logs warning when content is truncated

### 2. Signal Handler Enhancement (`signals.py`)

#### Task 2.1: Core Signal Logic

- [x] Add field-specific triggers for embedding updates
  - Added EMBEDDING_TRIGGER_FIELDS set for content and title
  - Skip updates when no relevant fields are modified
- [x] Add basic validation for required fields
  - Added validation for content and title
  - Improved logging with context

### 3. Celery Task Enhancement (`tasks/page_tasks.py`)

#### Task 3.1: Essential Task Management

- [x] Add task status tracking
  - Added Redis-based status tracking
  - Status includes: start/end time, retries, errors
  - Status stored with 1-hour TTL
- [x] Implement basic retry strategy
  - Enhanced retry configuration with backoff and jitter
  - Max 3 retries with exponential backoff
  - Max 5 minutes between retries

## Testing & Deployment

### Local Testing Commands

````bash
# 1. Watch logs in separate terminals:
make logs-web-100     # Django logs
make logs-celery      # Celery worker logs
make logs-redis       # Redis logs

# 2. If you need to restart services:
make restart

# 3. To check service status:
make ps


### Manual Testing Steps
1. Create/Update a Notion page via a command in notion/management/command/test_embeddings.py
```bash
python manage.py test_embeddings
````

2. Check Celery logs for task execution
3. Verify embedding updates in database
4. Test basic error scenarios:
   - Invalid content
   - API failures
   - Network issues

### Troubleshooting Commands

```bash
# Access Django shell
make enter-shell
python manage.py shell

# Check Celery task status
from notion.tasks.page_tasks import process_page_update
process_page_update.delay(page_id="test-id", updated_fields=["content"])

# View Redis queue
make logs-redis
```

## Success Criteria (Alpha)

1. Basic embedding generation works for page content updates
2. System handles and logs basic error cases
3. Celery tasks execute and retry properly
4. Configuration can be updated via environment variables

## Dependencies

- Local OpenAI-compatible API endpoint
- Docker environment (Redis, Celery, Django)

## Timeline

- Priority: Error Handling → Basic Optimization → Testing
