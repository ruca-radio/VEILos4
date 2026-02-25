# VEILos4 Deployment Guide

Production deployment guide for VEILos4 multi-model orchestration platform.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running in Production](#running-in-production)
- [Systemd Services](#systemd-services)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [Security Hardening](#security-hardening)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB
- OS: Ubuntu 20.04+ / Debian 11+ / RHEL 8+ / macOS 12+

**Recommended (with LLM providers):**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 20GB+
- Network: Stable connection for API calls

### Software Dependencies

- Python 3.10+
- pip / virtualenv
- systemd (for service management, Linux only)
- nginx / caddy (for reverse proxy, optional)
- git

---

## Installation

### 1. Clone Repository

```bash
# Production server
cd /opt
sudo git clone https://github.com/yourusername/VEILos4.git
cd VEILos4
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python demo.py
```

Expected output: `11/11 sections pass` ✅

---

## Configuration

### Environment Variables

Create `/opt/VEILos4/.env`:

```bash
# LLM Provider Configuration
# (Optional — system falls back to mocks if not set)

# Ollama (local models)
OLLAMA_BASE_URL=http://localhost:11434

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...

# xAI Grok
XAI_API_KEY=xai-...

# Kernel Configuration
VEIL_DEBUG=false
VEIL_COGNITIVE_LAYERS=3
VEIL_AUDIT_ENABLED=true

# Web Interface
VEIL_WEB_HOST=0.0.0.0
VEIL_WEB_PORT=8001
VEIL_WEB_WORKERS=4

# Security
VEIL_SECRET_KEY=<generate-with-openssl-rand-hex-32>
VEIL_ALLOWED_ORIGINS=https://yourdomain.com
```

### Generate Secret Key

```bash
openssl rand -hex 32
```

### Load Environment Variables

```bash
# Add to shell profile (~/.bashrc or ~/.zshrc)
export $(cat /opt/VEILos4/.env | xargs)

# Or use direnv (recommended)
sudo apt install direnv
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
# Create .envrc: echo 'dotenv' > /opt/VEILos4/.envrc
# Allow: direnv allow /opt/VEILos4
```

---

## Running in Production

### Option 1: Uvicorn (Simple)

```bash
cd /opt/VEILos4
source .venv/bin/activate

# Production mode (no reload)
uvicorn interfaces.web:app \
  --host 0.0.0.0 \
  --port 8001 \
  --workers 4 \
  --log-level info \
  --access-log
```

### Option 2: Gunicorn + Uvicorn Workers (Recommended)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn interfaces.web:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8001 \
  --log-level info \
  --access-logfile /var/log/veilos4/access.log \
  --error-logfile /var/log/veilos4/error.log \
  --daemon
```

### Option 3: Systemd Service (Best for Production)

See [Systemd Services](#systemd-services) section below.

---

## Systemd Services

### Web Dashboard Service

Create `/etc/systemd/system/veilos4-web.service`:

```ini
[Unit]
Description=VEILos4 Web Dashboard
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/VEILos4
Environment="PATH=/opt/VEILos4/.venv/bin"
EnvironmentFile=/opt/VEILos4/.env
ExecStart=/opt/VEILos4/.venv/bin/gunicorn interfaces.web:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8001 \
  --log-level info \
  --access-logfile /var/log/veilos4/access.log \
  --error-logfile /var/log/veilos4/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### TUI Service (Optional)

For running TUI as a service (accessible via SSH):

```ini
[Unit]
Description=VEILos4 TUI Interface
After=network.target

[Service]
Type=simple
User=veilos4
Group=veilos4
WorkingDirectory=/opt/VEILos4
Environment="PATH=/opt/VEILos4/.venv/bin"
EnvironmentFile=/opt/VEILos4/.env
ExecStart=/opt/VEILos4/.venv/bin/python interfaces/tui.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services

```bash
# Create log directory
sudo mkdir -p /var/log/veilos4
sudo chown www-data:www-data /var/log/veilos4

# Create user (if using dedicated user)
sudo useradd -r -s /bin/bash -d /opt/VEILos4 veilos4
sudo chown -R veilos4:veilos4 /opt/VEILos4

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable veilos4-web
sudo systemctl enable veilos4-tui  # if using

# Start services
sudo systemctl start veilos4-web
sudo systemctl start veilos4-tui  # if using

# Check status
sudo systemctl status veilos4-web
```

### Service Management Commands

```bash
# View logs
sudo journalctl -u veilos4-web -f

# Restart
sudo systemctl restart veilos4-web

# Stop
sudo systemctl stop veilos4-web

# Disable
sudo systemctl disable veilos4-web
```

---

## Reverse Proxy Setup

### Nginx

Create `/etc/nginx/sites-available/veilos4`:

```nginx
upstream veilos4_backend {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration (use certbot for Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy Settings
    location / {
        proxy_pass http://veilos4_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=veilos4_limit:10m rate=10r/s;
    location /execute {
        limit_req zone=veilos4_limit burst=20 nodelay;
        proxy_pass http://veilos4_backend;
    }

    # Static files (if any)
    location /static {
        alias /opt/VEILos4/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Logging
    access_log /var/log/nginx/veilos4_access.log;
    error_log /var/log/nginx/veilos4_error.log;
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/veilos4 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal (certbot installs cron job automatically)
sudo certbot renew --dry-run
```

### Caddy (Alternative, Simpler)

Create `/etc/caddy/Caddyfile`:

```caddy
yourdomain.com {
    reverse_proxy localhost:8001

    # Automatic HTTPS (Let's Encrypt)
    tls your-email@example.com

    # Rate limiting
    rate_limit {
        zone execute {
            key {remote_host}
            events 10
            window 1s
        }
        match {
            path /execute
        }
    }

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
    }

    # Logging
    log {
        output file /var/log/caddy/veilos4_access.log
    }
}
```

Start Caddy:

```bash
sudo systemctl enable caddy
sudo systemctl start caddy
```

---

## Security Hardening

### 1. Firewall (UFW)

```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (if using reverse proxy)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block direct access to VEILos4 port (if behind reverse proxy)
# Only allow localhost connections
sudo ufw deny 8001/tcp
```

### 2. File Permissions

```bash
# Restrict access to .env
chmod 600 /opt/VEILos4/.env
chown veilos4:veilos4 /opt/VEILos4/.env

# Restrict logs
chmod 750 /var/log/veilos4
chown veilos4:veilos4 /var/log/veilos4
```

### 3. API Authentication (Recommended)

Add API key authentication to `interfaces/web.py`:

```python
from fastapi import Header, HTTPException

API_KEY = os.getenv("VEIL_API_KEY")

async def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        return  # Skip auth if not configured
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

# Add to routes:
@app.post("/execute", dependencies=[Depends(verify_api_key)])
async def execute_command(request: ExecuteRequest):
    # ...
```

Update `.env`:

```bash
VEIL_API_KEY=<generate-with-openssl-rand-hex-32>
```

Client usage:

```bash
curl -X POST https://yourdomain.com/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"command": "status"}'
```

### 4. Input Validation

Already implemented in `veil_kernel.py`:
- Command length: max 10,000 characters
- State IDs: alphanumeric + underscore only
- Memory keys: max 256 characters

### 5. Audit Logging

Enable audit logging in `.env`:

```bash
VEIL_AUDIT_ENABLED=true
```

Query audit log:

```python
result = kernel.execute("Show audit log")
# Returns all operations with timestamps
```

### 6. HTTPS Only

**Force HTTPS in nginx** (already in config above):

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

**Or in Caddy** (automatic):

```caddy
yourdomain.com {
    # HTTPS is default, HTTP redirects automatically
}
```

---

## Monitoring & Logging

### Application Logs

**Systemd journal:**

```bash
# View web dashboard logs
sudo journalctl -u veilos4-web -f

# View last 100 lines
sudo journalctl -u veilos4-web -n 100

# Filter by date
sudo journalctl -u veilos4-web --since "2025-02-24 00:00:00"
```

**Log files:**

```bash
# Access logs
tail -f /var/log/veilos4/access.log

# Error logs
tail -f /var/log/veilos4/error.log

# Nginx logs
tail -f /var/log/nginx/veilos4_access.log
tail -f /var/log/nginx/veilos4_error.log
```

### Health Monitoring

**Simple script** (`/opt/VEILos4/monitor.sh`):

```bash
#!/bin/bash

# Check if service is running
if ! systemctl is-active --quiet veilos4-web; then
    echo "VEILos4 web service is down!"
    sudo systemctl restart veilos4-web
    exit 1
fi

# Check health endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health)
if [ "$HTTP_CODE" != "200" ]; then
    echo "Health check failed: HTTP $HTTP_CODE"
    exit 1
fi

echo "VEILos4 is healthy"
exit 0
```

**Cron job** (runs every 5 minutes):

```bash
# Add to crontab
crontab -e

# Add line:
*/5 * * * * /opt/VEILos4/monitor.sh >> /var/log/veilos4/monitor.log 2>&1
```

### Prometheus Metrics (Advanced)

Install prometheus client:

```bash
pip install prometheus-client
```

Add to `interfaces/web.py`:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
request_count = Counter('veilos4_requests_total', 'Total requests')
request_duration = Histogram('veilos4_request_duration_seconds', 'Request duration')

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")

# Instrument routes
@app.middleware("http")
async def add_metrics(request, call_next):
    request_count.inc()
    with request_duration.time():
        response = await call_next(request)
    return response
```

Configure Prometheus (`/etc/prometheus/prometheus.yml`):

```yaml
scrape_configs:
  - job_name: 'veilos4'
    static_configs:
      - targets: ['localhost:8001']
```

### Grafana Dashboard (Advanced)

1. Install Grafana: https://grafana.com/docs/grafana/latest/setup-grafana/installation/
2. Add Prometheus data source
3. Import dashboard or create custom:
   - Request rate (requests/sec)
   - Error rate (errors/sec)
   - Response time (p50, p95, p99)
   - Active connections

---

## Backup & Recovery

### Data to Backup

VEILos4 is mostly stateless, but backup:

1. **Configuration files**:
   - `/opt/VEILos4/.env`
   - `/opt/VEILos4/config/*.yaml` (if any)

2. **Audit logs** (if stored to disk):
   - `./.veilos/audit.log.jsonl`

3. **Custom plugins/templates**:
   - `plugins/`
   - `templates/`

4. **Application code** (if modified):
   - `/opt/VEILos4/` (or just use git)

### Backup Script

```bash
#!/bin/bash
# /opt/VEILos4/backup.sh

BACKUP_DIR="/var/backups/veilos4"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/veilos4_backup_$DATE.tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup configuration and data
tar -czf "$BACKUP_FILE" \
  /opt/VEILos4/.env \
  /opt/VEILos4/.veilos/ \
  /opt/VEILos4/plugins/ \
  /opt/VEILos4/templates/ \
  /var/log/veilos4/

# Keep only last 7 backups
find "$BACKUP_DIR" -name "veilos4_backup_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

**Cron job** (daily at 2am):

```bash
crontab -e

# Add:
0 2 * * * /opt/VEILos4/backup.sh >> /var/log/veilos4/backup.log 2>&1
```

### Restore from Backup

```bash
# Extract backup
tar -xzf /var/backups/veilos4/veilos4_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Restart services
sudo systemctl restart veilos4-web
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status veilos4-web

# View logs
sudo journalctl -u veilos4-web -n 50

# Common issues:
# 1. Port already in use
sudo lsof -i :8001
sudo kill <PID>

# 2. Permission denied
sudo chown -R veilos4:veilos4 /opt/VEILos4
sudo chmod 600 /opt/VEILos4/.env

# 3. Missing dependencies
source /opt/VEILos4/.venv/bin/activate
pip install -r /opt/VEILos4/requirements.txt
```

### High Memory Usage

```bash
# Check memory
free -h

# Reduce workers in systemd service
# Edit /etc/systemd/system/veilos4-web.service
# Change: --workers 4 → --workers 2

sudo systemctl daemon-reload
sudo systemctl restart veilos4-web
```

### Slow Response Times

**Check cognitive stack latency:**

```python
# Enable debug mode
export VEIL_DEBUG=true

# Check logs for timing info
sudo journalctl -u veilos4-web -f | grep "duration"
```

**Reduce cognitive layers:**

```bash
# In .env
VEIL_COGNITIVE_LAYERS=2  # Down from 3
```

**Check LLM provider status:**

```bash
# Ollama
curl http://localhost:11434/api/tags

# OpenAI
curl https://status.openai.com/

# Anthropic
curl https://status.anthropic.com/
```

### Web Interface 500 Errors

```bash
# Check error logs
tail -f /var/log/veilos4/error.log

# Common issues:
# 1. Kernel not initialized
# Check web.py has kernel.start() in startup event

# 2. LLM provider timeout
# Check provider API keys and network

# 3. Missing environment variables
cat /opt/VEILos4/.env
```

### Nginx 502 Bad Gateway

```bash
# Check if backend is running
curl http://localhost:8001/health

# Check nginx error log
tail -f /var/log/nginx/veilos4_error.log

# Test nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal
```

---

## Performance Tuning

### Gunicorn Workers

**Formula:** `(2 × CPU_cores) + 1`

For 4 cores: `(2 × 4) + 1 = 9 workers`

Update systemd service:

```ini
ExecStart=/opt/VEILos4/.venv/bin/gunicorn interfaces.web:app \
  --workers 9 \
  --worker-class uvicorn.workers.UvicornWorker \
  ...
```

### Database Connection Pooling

If using external database (future feature):

```python
# PostgreSQL example
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10
)
```

### Caching

**Redis for session caching** (if implementing sessions):

```bash
# Install redis
sudo apt install redis-server

# Enable redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

```python
# In web.py
import redis

cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.post("/execute")
async def execute_command(request: ExecuteRequest):
    # Check cache
    cache_key = f"execute:{request.command}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Execute and cache
    result = kernel.execute(request.command)
    cache.setex(cache_key, 300, json.dumps(result))  # 5 min TTL
    return result
```

---

## Security Checklist

Before going live:

- [ ] Change default secret keys
- [ ] Enable HTTPS (SSL certificates)
- [ ] Configure firewall (UFW/iptables)
- [ ] Restrict file permissions (`.env`, logs)
- [ ] Enable API authentication
- [ ] Configure rate limiting
- [ ] Set up audit logging
- [ ] Configure backup cron jobs
- [ ] Enable fail2ban (optional)
- [ ] Review nginx/caddy security headers
- [ ] Test disaster recovery procedure
- [ ] Monitor logs for suspicious activity

---

## Production Checklist

Final checklist before production:

- [ ] All tests pass (`python demo.py`)
- [ ] All three interfaces tested
- [ ] Environment variables configured
- [ ] Systemd services enabled
- [ ] Reverse proxy configured (nginx/caddy)
- [ ] SSL certificates installed
- [ ] Firewall configured
- [ ] Backup cron jobs running
- [ ] Health monitoring active
- [ ] Log rotation configured
- [ ] Documentation accessible to team
- [ ] Incident response plan documented

---

## Additional Resources

- **VEILos4 Documentation**: [docs/](.)
- **Systemd Manual**: https://www.freedesktop.org/software/systemd/man/
- **Nginx Documentation**: https://nginx.org/en/docs/
- **Caddy Documentation**: https://caddyserver.com/docs/
- **Let's Encrypt**: https://letsencrypt.org/
- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/

---

## Support

For deployment issues:

1. Check logs: `sudo journalctl -u veilos4-web -f`
2. Review [Troubleshooting](#troubleshooting) section above
3. Search GitHub issues: https://github.com/yourusername/VEILos4/issues
4. Open new issue with:
   - OS and version
   - Python version
   - Full error logs
   - Steps to reproduce

---

**VEILos4 is production-ready. Deploy with confidence.** 🚀
