# Cloudflare App

This is the Cloudflare app it handles the Cloudflare settings and the Cloudflare configuration.

- Cloudflare is where my domains are hosted and where I have my DNS records.
- I use Cloudflare for the DNS records and use Cloudflare tunneling to connect to my home server, specifically the nginx reverse proxy lxc container in proxmox where it gets proxied to the different services.

Actions:

- Need to create a controller script that will be able to create domain records to route traffic to specific services on my home server.
- Need a way to update the Cloudflare DNS records for the domains.
- Need a task to keep the Cloudflare DNS records up to date with the domains and the services.
- Will need a model to store the important Cloudflare DNS records for the domains and the services.
