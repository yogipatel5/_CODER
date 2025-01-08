#!/bin/bash

# Constants
EXTENSIONS_FILE="cursor_extensions.txt"
SETTINGS_FILE="cursor_settings.json"

# Function to show usage
show_usage() {
    echo "Usage: $0 [export|import]"
    echo "  export - Export current extensions and settings"
    echo "  import - Import extensions and settings"
    exit 1
}

# Function to export extensions and settings
export_config() {
    echo "Exporting Cursor/VS Code configuration..."
    
    # Export extensions
    echo "Exporting extensions..."
    code --list-extensions > "$EXTENSIONS_FILE"
    
    # Export settings
    echo "Exporting settings..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        cp ~/Library/Application\ Support/Cursor/User/settings.json "$SETTINGS_FILE"
    else
        echo "Unsupported OS for settings export"
        exit 1
    fi
    
    echo "Export completed successfully!"
    echo "Extensions saved to: $EXTENSIONS_FILE"
    echo "Settings saved to: $SETTINGS_FILE"
}

# Function to import extensions and settings
import_config() {
    echo "Importing Cursor/VS Code configuration..."
    
    # Check if files exist
    if [ ! -f "$EXTENSIONS_FILE" ] || [ ! -f "$SETTINGS_FILE" ]; then
        echo "Error: Required files not found!"
        echo "Please ensure both $EXTENSIONS_FILE and $SETTINGS_FILE exist."
        exit 1
    fi
    
    # Install extensions
    echo "Installing extensions..."
    while IFS= read -r extension; do
        echo "Installing extension: $extension"
        code --install-extension "$extension"
    done < "$EXTENSIONS_FILE"
    
    # Import settings
    echo "Importing settings..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        cp "$SETTINGS_FILE" ~/Library/Application\ Support/Cursor/User/settings.json
    else
        echo "Unsupported OS for settings import"
        exit 1
    fi
    
    echo "Import completed successfully!"
}

# Main script logic
if [ $# -ne 1 ]; then
    show_usage
fi

case "$1" in
    "export")
        export_config
        ;;
    "import")
        import_config
        ;;
    *)
        show_usage
        ;;
esac

mkdir -p crewai/tools crewai/config
touch crewai/__init__.py
touch crewai/main.py
touch crewai/crew.py
touch crewai/tools/__init__.py
touch crewai/tools/custom_tool.py
touch crewai/config/agents.yaml
touch crewai/config/tasks.yaml
