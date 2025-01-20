import json

# Sample JSON data
data = {
    "name": "Test User",
    "age": 30,
    "address": {"street": "123 Main St", "city": "Anytown", "country": "USA"},
    "hobbies": ["reading", "coding", "hiking"],
}

# Print JSON with | fx appended for terminal formatting
print(json.dumps(data, indent=2) + " | fx")
