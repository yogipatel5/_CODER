# Projects App (projects)

This is the projects app it handles the projects and the project settings and the project configuration.

Apps within Projects:

## Github App (projects.github)

- I use Github for the source control and usually have main, develop and staging branches.

## Vault App (projects.vault)

- I use Hashicorp Vault for the secrets and project settings. It's hosted on proxmox on a lxc container and it secrets are saved by project in different paths.

## Templates Folder(projects.templates)

- Templates are files that will be used to create specific projects. The templates folder has different folders for different types of projects like Django, React, Next JS, etc.
