# Yogi's Infrastructure Deployment Workflow

## Prerequisites Documentation

- Create central documentation file (`infrastructure.md`) to track:
  - IP addresses
  - PCT container IDs
  - MAC addresses
  - DNS records
  - Environment variables
  - API tokens/credentials
  - Monitoring endpoints

## Phase 0: Documentation Setup

```bash
# Initialize MkDocs in project directory
cd ~/ebay_django
mkdocs new .

# Configure mkdocs.yml
cat << EOF > mkdocs.yml
site_name: eBay Django Service
theme:
  name: material
  features:
    - navigation.instant
    - navigation.sections
plugins:
  - search
  - mkdocstrings:
      default_handler: python
  - git-revision-date
nav:
  - Home: index.md
  - Infrastructure:
    - Proxmox Setup: infrastructure/proxmox.md
    - Networking: infrastructure/networking.md
    - Monitoring: infrastructure/monitoring.md
  - Deployment:
    - Staging: deployment/staging.md
    - Production: deployment/production.md
  - Operations:
    - Monitoring: operations/monitoring.md
    - Backup: operations/backup.md
    - Troubleshooting: operations/troubleshooting.md
EOF

# Create documentation structure
mkdir -p docs/{infrastructure,deployment,operations}
touch docs/infrastructure/{proxmox,networking,monitoring}.md
touch docs/deployment/{staging,production}.md
touch docs/operations/{monitoring,backup,troubleshooting}.md

# Initial documentation build
mkdocs build
```

## Phase 0.1: Monitoring Infrastructure Setup

```bash
# SSH into Proxmox
ssh proxmox-host

# Create monitoring container
pct create 102 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.gz \
    --hostname monitoring-server \
    --memory 4096 \
    --cores 2 \
    --net0 name=eth0,bridge=vmbr0,ip=dhcp

# Install Prometheus
pct exec 102 -- bash -c 'apt update && apt install -y prometheus'

# Configure Prometheus
cat << EOF > /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ebay_django'
    static_configs:
      - targets: ['ebay-django-staging-server:8000']
    metrics_path: '/metrics'

  - job_name: 'node'
    static_configs:
      - targets: ['ebay-django-staging-server:9100']
EOF

# Install Grafana
pct exec 102 -- bash -c 'apt install -y grafana'

# Configure basic auth for Grafana API
pct exec 102 -- bash -c 'grafana-cli admin reset-admin-password $GRAFANA_ADMIN_PASSWORD'

# Install OpenTelemetry Collector
pct exec 102 -- bash -c 'wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.88.0/otelcol_0.88.0_linux_amd64.deb && dpkg -i otelcol_0.88.0_linux_amd64.deb'

# Configure OpenTelemetry Collector
cat << EOF > /etc/otelcol/config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  logging:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, logging]
EOF

# Start monitoring services
pct exec 102 -- bash -c 'systemctl enable prometheus grafana-server otelcol && systemctl start prometheus grafana-server otelcol'
```

## Phase 0.2: Initial Grafana Dashboard Setup

```bash
# Create API token for automation
GRAFANA_API_TOKEN=$(curl -X POST -H "Content-Type: application/json" \
    -d '{"name":"automation", "role": "Admin"}' \
    http://admin:$GRAFANA_ADMIN_PASSWORD@monitoring-server:3000/api/auth/keys | jq -r .key)

# Create basic dashboard
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- \
  http://monitoring-server:3000/api/dashboards/db << EOF
{
  "dashboard": {
    "id": null,
    "title": "eBay Django Overview",
    "tags": ["ebay-django", "staging"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(django_http_requests_total[5m])",
            "legendFormat": "{{method}} {{handler}}"
          }
        ]
      }
    ]
  }
}
EOF
```

Create a central documentation file (`infrastructure.md`) to track:

- IP addresses
- PCT container IDs
- MAC addresses
- DNS records
- Environment variables
- API tokens/credentials

## Phase 1: Local Development Setup

### Local Repository Setup

```bash
# Create local project directory
mkdir -p ~/ebay_django
cd ~/ebay_django

# Initialize git and create branches
git init
git branch -M main
git branch staging
```

### GitHub Configuration

```bash
# Create read-only tokens for server deployment
# One for staging, one for production
gh auth token create ebay-django-staging-readonly \
    --repo repo:username/ebay_django:read \
    --repo repo:username/ebay_django:pull

# Create repository
gh repo create ebay_django --private
git remote add origin git@github.com:username/ebay_django.git
git push -u origin --all
```

### Local Environment Setup

```bash
# Create conda environment
conda create -p .conda python=3.11
conda activate ./.conda

# VS Code configuration
cat << EOF > .vscode/settings.json
{
    "python.defaultInterpreterPath": "\${workspaceFolder}/.conda/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true
}
EOF
```

## Phase 2: Infrastructure Setup

### Container Creation

```bash
# SSH into Proxmox
ssh proxmox-host

# Create container from Ubuntu 22.04 template
pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.gz \
    --hostname ebay-django-staging-server \
    --memory 4096 \
    --cores 2 \
    --net0 name=eth0,bridge=vmbr0,ip=dhcp

# Start container and get MAC address
pct start 100
pct config 100 | grep net0
```

### DHCP Reservation

```bash
# Using pfsense API to create DHCP reservation
curl -X POST "https://pfsense/api/v1/services/dhcpd/static" \
    -H "Authorization: $PFSENSE_TOKEN" \
    -d '{
        "mac": "<container_mac>",
        "ipaddr": "<next_available_ip>",
        "hostname": "ebay-django-staging-server"
    }'

# Restart container to get new IP
pct restart 100
```

## Phase 3: NPM and Domain Setup

### Verify NPM Container

```bash
# Check NPM container status
pct status <npm-container-id>
[ $? -eq 0 ] || exit 1

# Get NPM container IP
NPM_IP=$(pct config <npm-container-id> | grep net0 | grep -oP 'ip=\K[^,]+')
```

### Configure Proxy in NPM

```bash
# SSH into NPM container
pct enter <npm-container-id>

# Add proxy configuration via API
curl -X POST "http://localhost:81/api/nginx/proxy-hosts" \
    -H "Authorization: Bearer $NPM_TOKEN" \
    -d '{
        "domain_names": ["staging.autoboost.ai"],
        "forward_scheme": "http",
        "forward_host": "<ebay-django-container-ip>",
        "forward_port": 8000,
        "access_list_id": 0,
        "certificate_id": null,
        "ssl_forced": true,
        "websockets": true
    }'
```

### Configure DNS (Cloudflare)

```bash
# Using existing Cloudflare tunnel
# Add DNS record via API
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -H "Authorization: Bearer $CF_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "type": "CNAME",
        "name": "staging.autoboost.ai",
        "content": "<tunnel-id>.cfargotunnel.com",
        "proxied": true
    }'
```

## Phase 4: Server Configuration and Monitoring Setup

### SSH Key Generation (Local)

```bash
# Generate project-specific key
ssh-keygen -t ed25519 -C "ebay-django-staging" -f ~/.ssh/ebay-django-staging

# Add to SSH config
cat << EOF >> ~/.ssh/config
Host ebay-django-staging
    HostName <ip-address>
    User root
    IdentityFile ~/.ssh/ebay-django-staging
EOF
```

### Server Setup

```bash
# SSH into container
ssh ebay-django-staging

# Create environment file
cat << EOF > /etc/environment
ENV=staging
PROJECT_NAME=ebay_django
EOF

# Install requirements
apt update && apt upgrade -y
apt install -y \
    git python3 python3-pip python3-venv \
    nginx netcat-traditional htop \
    postgresql postgresql-contrib \
    redis-server \
    node-exporter prometheus-node-exporter

# Install OpenTelemetry
curl -L -O https://github.com/open-telemetry/opentelemetry-java-agent/releases/latest/download/opentelemetry-javaagent.jar

# Clone repository with read-only token
git clone https://oauth2:<github-token>@github.com/username/ebay_django.git /var/www/ebay_django
cd /var/www/ebay_django
git checkout staging
```

## Phase 5: Vault Configuration

```bash
# Create staging policy
vault policy write ebay-django-staging - << EOF
path "secret/data/ebay-django/staging/*" {
    capabilities = ["read", "list"]
}
EOF

# Create AppRole
vault write auth/approle/role/ebay-django-staging \
    token_policies="ebay-django-staging" \
    token_ttl=1h \
    token_max_ttl=4h

# Get credentials
ROLE_ID=$(vault read -field=role_id auth/approle/role/ebay-django-staging/role-id)
SECRET_ID=$(vault write -f -field=secret_id auth/approle/role/ebay-django-staging/secret-id)

# Store initial secrets
vault kv put secret/ebay-django/staging/config \
    django_secret=<value> \
    postgres_password=<value> \
    redis_password=<value>
```

## Phase 6: Service Configuration

### Create Services

```bash
# Create service files
cat << EOF > /etc/systemd/system/gunicorn.service
[Unit]
Description=Gunicorn daemon for ebay_django
After=network.target

[Service]
Environment=ENV=staging
User=www-data
Group=www-data
WorkingDirectory=/var/www/ebay_django
ExecStart=/var/www/ebay_django/venv/bin/gunicorn ebay_django.wsgi:application
StandardOutput=append:/var/log/ebay_django/gunicorn.log
StandardError=append:/var/log/ebay_django/gunicorn.error.log

[Install]
WantedBy=multi-user.target
EOF

# Similar for celery, celery-beat, daphne

# Create log directory
mkdir -p /var/log/ebay_django
chown -R www-data:www-data /var/log/ebay_django

# Configure log rotation
cat << EOF > /etc/logrotate.d/ebay_django
/var/log/ebay_django/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl restart gunicorn celery daphne celery-beat
    endscript
}
EOF
```

### Webhook Service

```bash
cat << EOF > /etc/systemd/system/webhook.service
[Unit]
Description=Webhook listener for deployment
After=network.target

[Service]
Environment=ENV=staging
ExecStart=/usr/local/bin/webhook -hooks /etc/webhook/hooks.json -verbose
StandardOutput=append:/var/log/ebay_django/webhook.log
StandardError=append:/var/log/ebay_django/webhook.error.log

[Install]
WantedBy=multi-user.target
EOF

# Create deployment script
cat << EOF > /usr/local/bin/deploy.sh
#!/bin/bash
cd /var/www/ebay_django
git pull origin staging
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart gunicorn celery daphne celery-beat
EOF
chmod +x /usr/local/bin/deploy.sh
```

## Phase 9: Documentation Updates

```bash
# Generate API documentation
python manage.py generate_swagger swagger.json
mv swagger.json docs/api/

# Update API documentation in MkDocs
cat << EOF > docs/api/overview.md
# API Documentation

This documentation is automatically generated from our OpenAPI specification.

For the raw OpenAPI specification, see [swagger.json](./swagger.json)
EOF

# Build and deploy documentation
mkdocs build
mkdocs gh-deploy  # If using GitHub Pages
```

## Verification Steps

### Infrastructure Check

```bash
# Check container status
pct status <container-id>

# Verify DHCP reservation
curl "https://pfsense/api/v1/services/dhcpd/static" \
    -H "Authorization: $PFSENSE_TOKEN" | grep ebay-django-staging-server
```

### Network Check

```bash
# From NPM container
cloudflared tunnel list
curl -H "Host: staging.autoboost.ai" localhost:80

# Check DNS
dig staging.autoboost.ai
```

### Service Check

```bash
# Check all services
systemctl status gunicorn celery celery-beat daphne webhook

# Check logs
tail -f /var/log/ebay_django/*.log
```

### Environment Check

```bash
# Verify environment
echo $ENV  # Should return 'staging'

# Check monitoring services
curl -s http://monitoring-server:9090/-/healthy  # Prometheus
curl -s http://monitoring-server:3000/api/health  # Grafana
curl -s http://localhost:8000/metrics | grep django_http_requests_total

# Check documentation
mkdocs serve --dev-addr=0.0.0.0:8001

# Check Vault access
VAULT_TOKEN=$(vault write auth/approle/login \
    role_id=$ROLE_ID \
    secret_id=$SECRET_ID)
vault kv get secret/ebay-django/staging/config
```

## Important Notes

1. Environment (staging/production) is set at multiple levels:

   - Container environment file
   - Vault paths and policies
   - Service configurations
   - GitHub tokens and permissions

2. Security layers:

   - pfsense firewall
   - Cloudflare proxy
   - NPM access control
   - Read-only GitHub tokens
   - Restricted Vault policies

3. All operations should be CLI-based for automation

4. Logs are centralized in `/var/log/ebay_django/`

5. Prerequisites must be verified before deployment:
   - NPM container running
   - Cloudflare tunnel active
   - Vault access configured
   - GitHub tokens created
