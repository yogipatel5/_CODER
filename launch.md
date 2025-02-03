# Production Deployment Guide

This guide outlines the steps to deploy the Django project to production using Proxmox LXC, Nginx, and Cloudflare with automated GitHub deployments.

## Prerequisites

- Proxmox VE server
- Domain name configured in Cloudflare already coder.ypgoc.com -> this is currently going to our nginx proxy manager and from there we can reverse proxy to the django app
- Use pf sence using the mac address of the lxc container to assign a static internal ip to lxc container so we can use that in nginx proxy manager
- GitHub repository with the project
- the only secrets we need to store in lxc is the vault token and the vault config found in our current .env

## 1. Proxmox LXC Container Setup

1. Create a new CT (Container):

```bash
# Create Ubuntu-based container
pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.gz \
    --hostname django-prod \
    --memory 2048 \
    --swap 512 \
    --cores 2 \
    --net0 name=eth0,bridge=vmbr0,ip=dhcp
```

2. Start and access the container:

```bash
pct start 100
pct enter 100
```

3. System Updates:

```bash
apt update && apt upgrade -y
apt install python3-pip python3-venv nginx git supervisor -y
```

## 2. Project Setup

1. Create application user:

```bash
adduser django-app
usermod -aG sudo django-app
```

2. Clone the repository:

```bash
cd /opt
git clone <your-repository-url> django-project
chown -R django-app:django-app django-project
```

3. Setup Python environment:

```bash
cd django-project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Environment Configuration:

```bash
# Create .env file
cp .env.example .env
# Edit with production settings
nano .env
```

## 3. Gunicorn Setup

1. Create Gunicorn service file:

```bash
nano /etc/supervisor/conf.d/django.conf

[program:django]
command=/opt/django-project/venv/bin/gunicorn --workers 3 --bind unix:/opt/django-project/app.sock <project_name>.wsgi:application
directory=/opt/django-project
user=django-app
autostart=true
autorestart=true
stderr_logfile=/var/log/django/django.err.log
stdout_logfile=/var/log/django/django.out.log

[supervisord]
logfile=/var/log/supervisor/supervisord.log
```

2. Create log directory:

```bash
mkdir -p /var/log/django
chown -R django-app:django-app /var/log/django
```

## 4. Nginx Configuration

1. Create Nginx configuration:

```bash
nano /etc/nginx/sites-available/django

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://unix:/opt/django-project/app.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/django-project/static/;
    }

    location /media/ {
        alias /opt/django-project/media/;
    }
}
```

2. Enable the site:

```bash
ln -s /etc/nginx/sites-available/django /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default  # Remove default site
nginx -t  # Test configuration
systemctl restart nginx
```

## 5. SSL Configuration with Let's Encrypt

1. Install Certbot:

```bash
apt install certbot python3-certbot-nginx -y
```

2. Obtain SSL certificate:

```bash
certbot --nginx -d your-domain.com
```

## 6. Cloudflare Configuration

1. DNS Settings:

   - Add A record pointing to your Proxmox host IP
   - Enable proxy status (orange cloud)

2. SSL/TLS Settings:
   - Set SSL/TLS encryption mode to "Full (strict)"
   - Enable "Always Use HTTPS"

## 7. GitHub Webhook Setup

1. Create deployment script:

```bash
nano /opt/django-project/deploy.sh

#!/bin/bash
cd /opt/django-project
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
supervisorctl restart django
```

2. Make script executable:

```bash
chmod +x /opt/django-project/deploy.sh
```

3. Install webhook listener:

```bash
apt install webhook -y
```

4. Configure webhook:

```bash
nano /etc/webhook.conf

{
  "hooks": [
    {
      "id": "deploy",
      "execute-command": "/opt/django-project/deploy.sh",
      "command-working-directory": "/opt/django-project",
      "response-message": "Deploying application...",
      "trigger-rule": {
        "match": {
          "type": "payload-hash-sha1",
          "secret": "your-webhook-secret",
          "parameter": {
            "source": "header",
            "name": "X-Hub-Signature"
          }
        }
      }
    }
  ]
}
```

5. Create webhook service:

```bash
nano /etc/systemd/system/webhook.service

[Unit]
Description=Github webhook
After=network.target

[Service]
ExecStart=/usr/bin/webhook -hooks /etc/webhook.conf -verbose

[Install]
WantedBy=multi-user.target
```

6. Start webhook service:

```bash
systemctl enable webhook
systemctl start webhook
```

7. Configure GitHub webhook:
   - Go to repository settings > Webhooks
   - Add webhook URL: `https://your-domain.com/hooks/deploy`
   - Set content type to `application/json`
   - Add secret
   - Select "Just the push event"

## 8. Final Steps

1. Django production settings:

   - Set `DEBUG = False`
   - Update `ALLOWED_HOSTS`
   - Configure production database
   - Set secure cookie settings

2. Initial deployment:

```bash
python manage.py collectstatic
python manage.py migrate
```

3. Test deployment:
   - Push to main branch
   - Monitor logs:
     ```bash
     tail -f /var/log/django/django.out.log
     tail -f /var/log/django/django.err.log
     ```

## Maintenance

- Regular backups:
  ```bash
  python manage.py dumpdata > backup.json
  ```
- Monitor logs and system resources
- Keep system packages updated
- Regularly check SSL certificate renewal

## Troubleshooting

1. Check service status:

```bash
systemctl status nginx
supervisorctl status
systemctl status webhook
```

2. View logs:

```bash
tail -f /var/log/nginx/error.log
tail -f /var/log/django/django.err.log
journalctl -u webhook
```

3. Common issues:
   - Permission problems: Check file ownership and permissions
   - Socket errors: Verify Gunicorn is running
   - 502 Bad Gateway: Check Gunicorn/Django logs
   - Webhook not triggering: Verify webhook service and GitHub configuration
