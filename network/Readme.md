# Network App

This is the network app it handles the network of the system for the projects.

- Cloudflare is where my domains are hosted and where I have my DNS records.
- NGINX Reverse Proxy is where Cloudflare is proxying the traffic to my home server.
- proxmox is where I have my virtual machines and lxc containers for services.
- PFSense is my home router and firewall which handles my DHCP Reservations for static IP Addresses to my services.

Inside of each of those apps I have service.py where actions are defined for the services what Alfie can use for automations and actions.
