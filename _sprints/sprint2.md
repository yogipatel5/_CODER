# Project Sprints

This document lists all the sprints for the project.

## Project Information

**Project Name:** Code Helpers

**Description:** A collection of tools for developing on my Macbook Studio and Macbook Pro.

## Sprint 1: Project Creation Automation

**Goal:** Implement the core functionality for creating new projects based on YAML configurations.

**Status:** In Progress

**Details:** [sprint1.md](sprint1.md)

## Sprint 2: Django Project Restructure and Setup (Functional Setup)

**Goal:** Restructure the existing codebase into a functional Django project with multiple apps, including a configured PostgreSQL database, Redis, and environment variables loaded from a `.env` file. The Django app should be runnable locally. Refactoring of scripts will be done in a later sprint.

**Status:** Completed

**Details:**

1. **Project Setup:**

   - Create a new Django project named `coder` in `/Users/yp/Code/_CODER/`.
   - Create a `requirements.txt` file and add `django==5.1.4`, `psycopg2`, `python-dotenv`, `redis`, and `django-redis`.
   - Create a `.env` file in the project root and add the following variables:

     ```
     POSTGRES_PASSWORD=GesxAVcH1TgIy@
     POSTGRES_USER=n8n
     POSTGRES_DB=CODER
     POSTGRES_HOST=10.16.1.100
     POSTGRES_PORT=5432
     REDIS_HOST=10.16.1.100
     REDIS_PORT=6379
     ```

   - Update `.gitignore` to include `.env`, `__pycache__`, `.vscode`, `.idea`, `*.pyc`, and `*.sqlite3`.
   - [start comment] TODO : Update the `.gitignore` file to include more common files [end comment]

2. **Core App Setup:**
   - Create a `core` app in `/core/`.
   - Move the Django project's `settings.py` to `/core/settings.py`.
   - Update the Django project's `manage.py` to point to the new `settings.py` location.
   - Create `urls.py`, `models.py`, `admin.py`, and `apps.py` in `/core/`.
   - Configure `settings.py` to use PostgreSQL and Redis with the credentials from the `.env` file.
   - Set `DEBUG = True` and `ALLOWED_HOSTS = ['localhost', '127.0.0.1']` in `settings.py`.
3. **Automation App Setup:**
   - Create an `automation` app in `/automation/`.
   - Create `models.py`, `views.py`, `urls.py`, `admin.py`, `templates/`, and `apps.py` in `/automation/`.
   - Move the existing `project/create_project.py` and `project/dirhelper.py` to `/automation/`.
   - **Note:** Refactoring of these scripts will be done in a later sprint.
4. **GitHub Management App Setup:**
   - Create a `github_management` app in `/github_management/`.
   - Create `models.py`, `views.py`, `urls.py`, `admin.py`, `templates/`, and `apps.py` in `/github_management/`.
   - Move the existing `github/giithelper.py` to `/github_management/`.
   - **Note:** Refactoring of this script will be done in a later sprint.
5. **System Management App Setup:**
   - Create a `system_management` app in `/system_management/`.
   - Create `models.py`, `views.py`, `urls.py`, `admin.py`, `templates/`, and `apps.py` in `/system_management/`.
   - Move the existing `system/coder_system.py` to `/system_management/`.
   - **Note:** Refactoring of this script will be done in a later sprint.
6. **Project Management App Setup:**
   - Create a `project_management` app in `/project_management/`.
   - Create `models.py`, `views.py`, `urls.py`, `admin.py`, `templates/`, and `apps.py` in `/project_management/`.
   - [start comment] TODO : Add functionality to the `project_management` app in a later sprint [end comment]
7. **Proxmox Management App Setup:**
   - Create a `proxmox_management` app in `/proxmox_management/`.
   - Create `models.py`, `views.py`, `urls.py`, `admin.py`, `templates/`, and `apps.py` in `/proxmox_management/`.
   - [start comment] TODO : Add functionality to the `proxmox_management` app in a later sprint [end comment]
8. **Vault Management App Setup:**
   - Create a `vault_management` app in `/vault_management/`.
   - Create `models.py`, `views.py`, `urls.py`, `admin.py`, `templates/`, and `apps.py` in `/vault_management/`.
   - [start comment] TODO : Add functionality to the `vault_management` app in a later sprint [end comment]
9. **File Movement:**
   - Move `_CODER.coder.yaml`, `coder_proejct_template.yaml`, and `project_creation.log` to the project root (`/Users/yp/Code/_CODER/`).
   - Move `.cursorrules` to the project root (`/Users/yp/Code/_CODER/`).
   - Move `project/templates/project/.cursorrules` and `project/templates/project/.vscode/settings.json` to `/core/templates/project/`.
   - Move `github/Readme.md` to `/github_management/templates/`.
   - Move `system/templates/.shared_alliases.template` to `/system_management/templates/`.
   - Keep the existing `Readme.md` in the project root.
10. **Database Setup:**
    - Configure Django to use the PostgreSQL database using the environment variables in the `.env` file.
    - Create the `CODER` database in PostgreSQL.
    - Run Django migrations to create the necessary database tables.
    - **Note:** No models will be created in this sprint, so the migrations will be minimal.
11. **Redis Setup:**
    - Configure Django to use Redis using the environment variables in the `.env` file.
    - [start comment] TODO : Add redis functionality to the project in a later sprint [end comment]
12. **Run Django App:**
    - Ensure the Django app can be run locally using `python manage.py runserver`.
13. **Documentation:**
    - Update the project's `README.md` to reflect the new Django project structure.
    - [start comment] TODO : Add more detailed documentation for each app in a later sprint [end comment]

**Sprint Deliverables:**

- A functional Django project named `coder` with the specified app structure (apps directly under the project root).
- All relevant files moved to their respective app directories.
- A configured PostgreSQL database named `CODER`.
- Redis configured.
- A `.env` file with the necessary environment variables.
- The Django app can be run locally.
- Updated `README.md` file.

**Notes:**

- This sprint focuses on the initial setup and restructuring. The functionality of each app will be further developed in subsequent sprints.
- The existing scripts will be moved to their respective app directories but will not be refactored in this sprint.
- The developer should ask for clarification if they are unsure about where a file should go.
- The Django app should be runnable locally with the database and redis configured.
