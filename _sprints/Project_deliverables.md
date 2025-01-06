# Project Deliverables

## Project Name: Code Helpers

### Description

A collection of tools for developing on my Macbook Studio and Macbook Pro. This project aims to streamline the setup and management of development environments and projects. It includes scripts and templates for project creation, system configuration, and more.

## End Goal

The end goal of this project is to create a simple project creation tool that:

1. Takes a YAML configuration file as a command line input
2. Creates a new project based on that configuration
3. Returns a summary of what was created
4. Can be extended with additional tools and features over ti me

The tool will serve as a foundation that can grow to include more project setup automation capabilities as needed.

### Target Capabilities

- [x] - Create a new project based on a YAML configuration file.
- [x] - Create conda environment based on a YAML configuration file.
- [x] - Add Git local repository to the project

Git Remote

- [ ] - Add Git remote repository to the project.
- [ ] - Add Git branches to the project.
- [ ] - Add Git commit message to the project.
- [ ] - Add Git commit to the project.
- [ ] - Add Git push to the project.

### Current Capabilities

- The project is able to now create a new project based on a YAML configuration file.
- Based on the YAML it will be able to do the following:
  - Create a new project directory.
  - Create a new conda environment.
  - Create a new git repository.
  - Copy all template files to the project directory.
  - Copy all template files to the conda environment.
  - Copy all template files to the git repository.

Current Project Tree

```bash
.
├── .conda
│   └── bin
│       └── python
├── .cursorrules
├── .env
├── .github
│   └── pull_request_template.md
├── .gitignore
├── .vscode
│   └── settings.json
├── README.md
├── docs
├── requirements.txt
└── tests
```

#### Project Management Scripts

- `/coder_project_template.yaml` - This is a template for creating a new project on my Macbook. It uses the `coder` command to create the project.
- `/projects/create_project.sh` - This is a script that will create a new project on my Macbook. It uses the `coder` command to create the project.
  > TODO: Create the `coder` alias and executable. Consider adding command line CLI with prompts when YAML file is not provided.
- `/projects/dirhelper.py` - This is a script that will helps manage the ~/code/ directory

#### System Scripts

- (No system scripts are currently listed in the Readme)

#### .Template Directory

- `/.templates/system/` - This is a collection of template files for my system ranging such as`/.zshrc`, `/.ssh/config`, `/.shared_aliases.template`

- `.templates/system/.zshrc.template` - This is a sample `.zshrc` file that I use on my Macbook, if I make updates, it should be reflected in the `.zshrc.template` file.

<!-- TODO : Need to create a script that will update the `.zshrc.template` file with the latest `.zshrc` file automatically maybe on a cron job. -->

#### Github Directory

This is where I am
/Users/yp/Code/\_CODER/github

#### Sprints

- Sprint 1: Project Creation Automation - Completed

### Future Sprints
