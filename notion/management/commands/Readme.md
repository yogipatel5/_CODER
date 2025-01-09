# Notion Management Commands

This directory contains Django management commands for interacting with the Notion API. The structure is designed to be modular and easily extensible.

## Available Commands

### Page Management
```bash
# List all pages
python manage.py list_pages [--database DATABASE_ID] [--limit N]

# Get page details
python manage.py get_page PAGE_ID [--include-content] [--raw] [--show-ids]

# Create a page
python manage.py create_page PARENT_ID --title "Page Title" [--properties key=value]

# Update a page
python manage.py update_page PAGE_ID --properties key=value

# Update a page with JSON
python manage.py update_page_json PAGE_ID [--json-file FILE] [--json-string JSON] [--verbose]

# Delete a page
python manage.py delete_page PAGE_ID

# Search pages
python manage.py search_pages "query"
```

### Block Management
```bash
# Create a block
python manage.py manage_blocks create PARENT_ID --type TYPE --content "Content"

# Update a block
python manage.py manage_blocks update BLOCK_ID --type TYPE --content "Content"

# Delete a block
python manage.py manage_blocks delete BLOCK_ID
```

### Database Management
```bash
# List databases
python manage.py list_databases
```

## Standardized JSON Response Format

All commands return responses in this format:
```json
{
  "success": true/false,
  "message": "Human readable message",
  "context": "Optional context/hints",
  "data": {
    // Command-specific data structure
  },
  "progress": [], // Optional progress messages
  "error": "Error message if failed"
}
```

### Command-Specific Data Structures

#### get_page
```json
{
  "data": {
    "page": {
      "id": "page-id",
      "title": "Page Title",
      "url": "https://notion.so/...",
      "created_time": "2024-01-09T...",
      "last_edited_time": "2024-01-09T...",
      "parent": {
        "type": "page_id|database_id|workspace",
        "id": "parent-id",
        "title": "Parent Title"
      },
      "properties": {}
    },
    "content": [
      {
        "type": "block-type",
        "content": "Block content",
        "indent": 0,
        "id": "block-id" // if --show-ids used
      }
    ]
  }
}
```

#### list_pages
```json
{
  "data": {
    "pages": [
      {
        "id": "page-id",
        "title": "Page Title",
        "parent": {
          "type": "page_id|database_id|workspace",
          "id": "parent-id"
        },
        "url": "https://notion.so/..."
      }
    ],
    "total": 10,
    "limit": 100
  }
}
```

#### update_page_json
```json
{
  "data": {
    "page_id": "page-id",
    "title": "Updated Title",
    "url": "https://notion.so/..."
  }
}
```

## Core Components

### 1. Base Classes (`base.py`)
- `NotionAPI`: Client for interacting with Notion's API
- `NotionBaseCommand`: Base class for all command implementations

### 2. Best Practices

1. **Error Handling**
   - All commands include proper error messages
   - Parent/block IDs are validated
   - JSON responses include error details

2. **Command Features**
   - Support for both CLI and JSON output
   - Verbose progress reporting
   - Helpful context messages

3. **Testing**
   - Unit tests in `notion/tests/`
   - Manual testing script
   - JSON response validation
</rewritten_file>