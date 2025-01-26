# Code Helpers

A collection of tools for developing on my Macbook Studio and Macbook Pro, built with Django 5.1.4.

## Project Structure

## Setup

1. Clone the repository:

```bash
git clone git@github.com:yogipatel5/Code-Helpers.git
cd Code-Helpers
```

1. Create and activate a conda environment:

```bash
conda create -n coder python=3.11
conda activate coder
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Create a `.env` file in the project root with the following variables:

```text
POSTGRES_PASSWORD=your_password
POSTGRES_USER=your_user
POSTGRES_DB=CODER
POSTGRES_HOST=your_host
POSTGRES_PORT=5432
REDIS_HOST=your_host
REDIS_PORT=6379
```

1. Create the database:

```bash
createdb -h $POSTGRES_HOST -U $POSTGRES_USER CODER
```

1. Run migrations:

```bash
python manage.py migrate
```

1. Create a superuser:

```bash
python manage.py createsuperuser
```

1. Run the development server:

```bash
python manage.py runserver
```

The server will be available at <http://localhost:8000>

## Apps

### Core

- Django project settings and configuration
- Main URL routing

### Automation

- Project creation and automation tools
- Directory structure helpers

### GitHub Management

- GitHub repository management
- Git workflow automation
- Repository operations:
  - Create and delete repositories
  - Update repository descriptions
  - Manage repository visibility
- Push operations:
  - Basic and force push with protection levels
  - Scheduled push operations
  - Branch-specific push settings
  - Push protection management (none/basic/strict)
  - Force push protection and validation
- Git workflow automation

### Usage Examples

```bash
# Push Operations
python -m github_management.giithelper push --branch feature/my-branch  # Push to specific branch
python -m github_management.giithelper push --force --tags             # Force push with tags
python -m github_management.giithelper push --schedule "2024-01-20T15:30:00"  # Schedule push

# Push Protection
python -m github_management.giithelper protection set strict  # Set strict protection
python -m github_management.giithelper protection get        # View current protection
```

### System Management

- System configuration tools
- Environment management

### Project Management

- Project tracking and organization
- Task management

### Proxmox Management

- Proxmox VE management tools
- VM and container management

### Vault Management

- HashiCorp Vault integration
- Secrets management

## Development

- The project uses PostgreSQL for the database
- Redis is used for caching and session storage
- All apps follow Django's app structure
- Code formatting is handled by black, ruff, and mypy

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests and linting
4. Submit a pull request

## License

This project is private and not licensed for public use.
# test comment
