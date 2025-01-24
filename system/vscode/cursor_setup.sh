#!/bin/bash

# Constants
EXTENSIONS_FILE="${PWD}/system/vscode/cursor_extensions.txt"
SETTINGS_FILE="${PWD}/system/vscode/cursor_settings.json"

# Function to show usage
show_usage() {
	echo "Usage: ${0} [export|import]"
	echo "  export - Export current extensions and settings"
	echo "  import - Import extensions and settings"
	exit 1
}

# Function to export extensions and settings
export_config() {
	echo "Exporting Cursor/VS Code configuration..."

	# Export extensions with full IDs
	echo "Exporting extensions..."
	# Get the list of installed extensions with their full IDs - Dont remove the versions
	# trunk-ignore(shellcheck/SC2312)
	cursor --list-extensions --show-versions | cut -d@ -f1 >"${EXTENSIONS_FILE}"

	# Export settings
	echo "Exporting settings..."
	if [[ ${OSTYPE} == "darwin"* ]]; then
		cp "${HOME}/Library/Application Support/Cursor/User/settings.json" "${SETTINGS_FILE}"
	else
		echo "Unsupported OS for settings export"
		exit 1
	fi

	echo "Export completed successfully!"
	echo "Extensions saved to: ${EXTENSIONS_FILE}"
	echo "Settings saved to: ${SETTINGS_FILE}"
}

# Function to import extensions and settings
import_config() {
	echo "Importing Cursor/VS Code configuration..."

	# Check if files exist
	if [[ ! -f ${EXTENSIONS_FILE} ]] || [[ ! -f ${SETTINGS_FILE} ]]; then
		echo "Error: Required files not found!"
		echo "Please ensure both ${EXTENSIONS_FILE} and ${SETTINGS_FILE} exist."
		exit 1
	fi

	# Uninstall currently installed extensions that are listed in the extensions file
	echo "Uninstalling existing extensions..."
	while IFS= read -r extension; do
		# trunk-ignore(shellcheck/SC2312)
		if cursor --list-extensions | grep -q "^${extension}$"; then
			echo "Uninstalling extension: ${extension}"
			cursor --uninstall-extension "${extension}"
		fi
	done <"${EXTENSIONS_FILE}"

	# Install extensions
	echo "Installing extensions..."
	while IFS= read -r extension; do
		echo "Installing extension: ${extension}"
		cursor --install-extension "${extension}"
	done <"${EXTENSIONS_FILE}"

	# Import settings
	echo "Importing settings..."
	if [[ ${OSTYPE} == "darwin"* ]]; then
		cp "${SETTINGS_FILE}" "${HOME}/Library/Application Support/Cursor/User/settings.json"
	else
		echo "Unsupported OS for settings import"
		exit 1
	fi

	echo "Import completed successfully!"
}

# Main script logic
if [[ $# -ne 1 ]]; then
	show_usage
fi

case "${1}" in
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
