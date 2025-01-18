# Overview of `cursor_setup.sh`

The `cursor_setup.sh` script is designed to manage the export and import of **Cursor** (a VS Code fork) configurations, specifically focusing on extensions and settings. This allows for easy backup and restoration of your development environment.

## Functionality

### Export Configuration (`export_config`)

- **Exports Installed Extensions**:

  - Utilizes the `code` command to list all currently installed extensions.
  - Saves the list to a file named `cursor_extensions.txt`.

- **Exports Settings**:

  - Copies the `settings.json` file from the Cursor User settings directory to `cursor_settings.json`.
  - **Note**: Currently, this operation is supported only on macOS (`darwin` OS type). If the script is run on an unsupported OS, it will exit with an error message.

- **Output**:
  - Confirms the successful export.
  - Specifies the locations where the extensions and settings have been saved.

### Import Configuration (`import_config`)

- **Pre-requisite Checks**:

  - Verifies the existence of both `cursor_extensions.txt` and `cursor_settings.json` before proceeding. If either file is missing, the script exits with an error message.

- **Installs Extensions**:

  - Reads the list of extensions from `cursor_extensions.txt`.
  - Installs each extension using the `code` command.

- **Imports Settings**:

  - Copies the `cursor_settings.json` back to the Cursor User settings directory.
  - **Note**: Similar to the export process, this is currently supported only on macOS. Unsupported OS types will result in an error.

- **Output**:
  - Confirms the successful import of extensions and settings.

### Script Execution Logic

- **Argument Parsing**:

  - The script expects exactly one argument: either `export` or `import`.
  - If an invalid argument is provided or the number of arguments is incorrect, the script displays usage instructions and exits.

- **Directory and File Setup**:
  - Creates necessary directories and initializes files within the `crewai` directory:
    - `crewai/tools/`
    - `crewai/config/`
    - Initializes Python files and YAML configuration files necessary for the project.

## Usage
