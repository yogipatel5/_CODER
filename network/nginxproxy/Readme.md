# NGINX Reverse Proxy App

This is the NGINX Reverse Proxy app it handles the NGINX Reverse Proxy for the system.

- Cloudflare is where my domains are hosted and where I have my DNS records.
- NGINX Reverse Proxy is where Cloudflare is proxying the traffic to my home server.
- I set up the NGINX Reverse Proxy to be able to proxy the traffic to the different services that I have running on my home server.
- PFSense is used to handle the DHCP Reservations for static IP Addresses to my services.

Actions:

- Need to create a controller script that will be able to create domain records to route traffic to specific services on my home server.
