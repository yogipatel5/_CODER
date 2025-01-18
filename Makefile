# Add system/vscode/cursor_setup.sh to the PATH

# Export Cursor/VS Code configuration
export_config:
	cursor_setup.sh export

# Import Cursor/VS Code configuration
import_config:
	cursor_setup.sh import
