# Proxmox VE API Documentation

## Overview

The Proxmox VE API is a RESTful API that uses HTTPS protocol on port 8006. All API calls use JSON for data formatting and require authentication via either a ticket (cookie) or API token.

Base URL: `https://<proxmox-host>:8006/api2/json/`

## Authentication

Our current implementation uses API token authentication with the following credentials:

- Host: `10.16.1.51:8006`
- Token ID: `root@pam!mac-studio`
- Token format: `USER@REALM!TOKENID`

## Common API Endpoints

### Nodes

- `GET /nodes` - List all nodes in the cluster
- `GET /nodes/{node}` - Get node details
- `GET /nodes/{node}/status` - Get node status
- `GET /nodes/{node}/netstat` - Get node network statistics
- `GET /nodes/{node}/tasks` - List tasks for node

### Virtual Machines (QEMU)

- `GET /nodes/{node}/qemu` - List all VMs
- `POST /nodes/{node}/qemu` - Create a new VM
- `GET /nodes/{node}/qemu/{vmid}/status/current` - Get VM status
- `POST /nodes/{node}/qemu/{vmid}/status/start` - Start VM
- `POST /nodes/{node}/qemu/{vmid}/status/stop` - Stop VM
- `POST /nodes/{node}/qemu/{vmid}/status/reset` - Reset VM
- `POST /nodes/{node}/qemu/{vmid}/status/shutdown` - Shutdown VM

### Containers (LXC)

- `GET /nodes/{node}/lxc` - List all containers
- `POST /nodes/{node}/lxc` - Create a new container
- `GET /nodes/{node}/lxc/{vmid}/status/current` - Get container status
- `POST /nodes/{node}/lxc/{vmid}/status/start` - Start container
- `POST /nodes/{node}/lxc/{vmid}/status/stop` - Stop container
- `POST /nodes/{node}/lxc/{vmid}/status/shutdown` - Shutdown container

### Storage

- `GET /storage` - List all storage
- `GET /nodes/{node}/storage` - List storage for node
- `GET /nodes/{node}/storage/{storage}` - Get storage details
- `GET /nodes/{node}/storage/{storage}/content` - List storage content
- `POST /nodes/{node}/storage/{storage}/content` - Upload content
- `DELETE /nodes/{node}/storage/{storage}/content/{volume}` - Delete content

### Network

- `GET /nodes/{node}/network` - List network interfaces
- `GET /nodes/{node}/network/{iface}` - Get interface config
- `PUT /nodes/{node}/network/{iface}` - Update interface config

### Cluster

- `GET /cluster/resources` - List all cluster resources
- `GET /cluster/tasks` - List all cluster tasks
- `GET /cluster/status` - Get cluster status
- `GET /cluster/nextid` - Get next free VMID

### Access Control

- `GET /access/users` - List all users
- `POST /access/users` - Create user
- `GET /access/groups` - List all groups
- `GET /access/roles` - List all roles
- `GET /access/domains` - List authentication domains

## Response Formats

The API supports multiple response formats:

- `json` - Standard JSON format (default)
- `extjs` - JSON format compatible with ExtJS
- `html` - HTML formatted (for debugging)
- `text` - Plain text (for debugging)

## API Stability

Proxmox VE maintains API compatibility within major releases. For example:

- API calls working in 6.0 will work in 6.4
- No guarantee of compatibility between major versions (e.g., 6.x to 7.x)

Breaking changes may include:

- Removing endpoints
- Moving endpoints to new paths
- Removing parameters
- Changing non-null return types

Non-breaking changes include:

- Adding new endpoints
- Adding new parameters
- Adding new properties to returned objects
- Changing null return types
