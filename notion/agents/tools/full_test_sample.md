# Notion Integration Documentation

## 1. Overview
This document demonstrates the **complete feature set** of our *Notion Integration* system. The system allows for seamless conversion of markdown to Notion blocks.

### Key Features
- Markdown to Notion conversion
- Rich text formatting support
- Nested structure preservation
- Multi-block type support

## 2. Text Formatting

### Basic Formatting
Regular text with **bold text**, *italic text*, ~~strikethrough text~~, and `inline code`.

### Quote / Callout
> This is a callout block with **bold text**

### Table
| Column 1 | Column 2 |
|----------|----------|
| Row 1    | Row 2    |
| Row 3    | Row 4    |

### Divider
---

### Links and References
- External link: [Notion API Documentation](https://developers.notion.com)

### Images
![Notion Logo](https://www.jordanharbinger.com/wp-content/uploads/2021/08/notion-350x250.png)

### Images in Lists
- Here's our logo: ![Notion Logo](https://www.jordanharbinger.com/wp-content/uploads/2021/08/notion-350x250.png)
- Another image: ![Example](https://example.com/image.png)

## 3. List Types

### Bullet Lists
- Top level item
  - Second level
    - Third level
  - Back to second
- Another top level
  - With sublevel

### Numbered Lists
1. First step
   1. Sub-step one
   2. Sub-step two
2. Second step
   - Mixed with bullet
   - Another bullet

### Task Lists
- [ ] Pending task
  - [x] Completed subtask
  - [ ] Pending subtask
- [x] Completed task
  1. Numbered subtask
  2. Another subtask

## 4. Code Blocks

### Python Example
```python
def convert_markdown(content: str) -> dict:
"""
Convert markdown content to Notion blocks.
"""
blocks = process_content(content)
return {
"type": "blocks",
"content": blocks
}
```
### YAML Configuration
```yaml
key: value
notion:
version: "2023-06"
features:
   -markdown
   -blocks
   -formatting
```

## 5. Nested Structure Preservation
This is a nested structure example:
- Outer list
  - Inner list
    - Innermost list

## 6. Multi-Block Type Support
This is a multi-block type example:
- Paragraph
- Quote
- Heading
- Callout