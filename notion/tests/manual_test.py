"""
Interactive testing script for Notion commands.
Tests all commands with practical examples and verifies JSON responses.
"""

import json
import sys
from typing import Any, Dict

from django.core.management import call_command


def capture_command_output(command: str, *args: Any, **kwargs: Any) -> Dict:
    """Capture command output and parse JSON response."""
    # Redirect stdout to capture output
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        call_command(command, *args, **kwargs)
        output = sys.stdout.getvalue()
        return json.loads(output)
    finally:
        sys.stdout = old_stdout


def verify_json_response(response: Dict) -> bool:
    """Verify that response follows our standard format."""
    required_fields = ["success", "message", "context", "data"]
    return all(field in response for field in required_fields)


def pause(message: str = "Press Enter to continue...") -> None:
    """Pause execution and wait for user input."""
    print(f"\n{message}")
    input()


def run_tests() -> None:
    """Run all manual tests."""
    print("Starting manual Notion command testing...")
    print("This script will test all commands and verify their JSON responses.")
    pause("Please open your Notion workspace in a browser.")

    # Test list_pages
    print("\n1. Testing list_pages command...")
    response = capture_command_output("list_pages")
    assert verify_json_response(response), "Invalid JSON response format"
    print("Found pages:", len(response["data"]["pages"]))
    pause("Verify the pages are listed correctly in your workspace.")

    # Test get_page
    print("\n2. Testing get_page command...")
    page_id = input("Enter a page ID from the list above: ")

    # Test basic page info
    response = capture_command_output("get_page", page_id)
    assert verify_json_response(response), "Invalid JSON response format"
    print(f"Retrieved page: {response['data']['page']['title']}")

    # Test with content
    response = capture_command_output("get_page", page_id, "--include-content")
    assert verify_json_response(response), "Invalid JSON response format"
    print(f"Retrieved {len(response['data']['content'])} blocks")
    pause("Verify the page content matches what you see in Notion.")

    # Test create_page
    print("\n3. Testing create_page command...")
    parent_id = input("Enter a parent page ID where we'll create test pages: ")

    # Create a test page
    response = capture_command_output(
        "create_page", parent_id, "--title", "CLI Test Page", "--properties", "Status=Testing"
    )
    assert verify_json_response(response), "Invalid JSON response format"
    test_page_id = response["data"]["page_id"]
    print(f"Created page with ID: {test_page_id}")
    pause("Verify the new page appears in your workspace.")

    # Test update_page_json
    print("\n4. Testing update_page_json command...")
    test_json = {"properties": {"title": "Updated Test Page", "Status": "In Progress"}}
    response = capture_command_output("update_page_json", test_page_id, f"--json-string={json.dumps(test_json)}")
    assert verify_json_response(response), "Invalid JSON response format"
    print("Updated page title and status")
    pause("Verify the page was updated in Notion.")

    # Test manage_blocks
    print("\n5. Testing manage_blocks command...")

    # Create blocks
    print("Creating different types of blocks...")
    blocks_to_create = [
        ("heading_1", "Test Heading 1"),
        ("paragraph", "This is a test paragraph."),
        ("bulleted_list_item", "Bullet point 1"),
        ("numbered_list_item", "Numbered item 1"),
        ("toggle", "Click to expand"),
        ("callout", "Important note"),
        ("quote", "This is a quote"),
    ]

    block_ids = []
    for block_type, content in blocks_to_create:
        response = capture_command_output(
            "manage_blocks", "create", test_page_id, "--type", block_type, "--content", content
        )
        assert verify_json_response(response), "Invalid JSON response format"
        block_ids.append(response["data"]["block_id"])
        print(f"Created {block_type} block")

    pause("Verify all blocks were created correctly.")

    # Update a block
    print("\nUpdating a block...")
    response = capture_command_output(
        "manage_blocks", "update", block_ids[0], "--type", "heading_1", "--content", "Updated Heading"
    )
    assert verify_json_response(response), "Invalid JSON response format"
    print("Updated heading block")
    pause("Verify the heading was updated.")

    # Delete a block
    print("\nDeleting a block...")
    response = capture_command_output("manage_blocks", "delete", block_ids[-1])
    assert verify_json_response(response), "Invalid JSON response format"
    print("Deleted last block")
    pause("Verify the block was deleted.")

    # Test delete_page
    print("\n6. Testing delete_page command...")
    if input(f"Delete test page {test_page_id}? (y/n): ").lower() == "y":
        response = capture_command_output("delete_page", test_page_id)
        assert verify_json_response(response), "Invalid JSON response format"
        print("Deleted test page")
        pause("Verify the page was deleted.")

    print("\nManual testing complete!")
    print("All JSON responses followed the standard format.")
    print("Please verify that all operations were reflected correctly in your Notion workspace.")


if __name__ == "__main__":
    from io import StringIO

    run_tests()
