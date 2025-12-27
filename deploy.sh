#!/bin/bash

# VT ULTRA PRO - Deployment Script
# Automated deployment for production environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="vt-ultra-pro"
APP_DIR="/opt/$APP_NAME"
BACKUP_DIR="/opt/backups"
LOG_DIR="/var/log/$APP_NAME"
ENV_FILE="$APP_DIR/.env"
CONFIG_FILE="$APP_DIR/config.yaml"

# Print colored message
print_message() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

print_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        print_error "Please run as root"
        exit 1
    fi
}

# Create directory structure
create_directories() {
    print_message "Creating directory structure..."
    
    mkdir -p $APP_DIR
    mkdir -p $BACKUP_DIR
    mkdir -p $LOG_DIR
    mkdir -p $APP_DIR/database
    mkdir -p $APP_DIR/logs
    mkdir -p $APP_DIR/backups
    mkdir -p $APP_DIR/config
    mkdir -p $APP_DIR/static
    mkdir -p $APP_DIR/templates
    
    chmod 755 $APP_DIR
    chmod 755 $LOG_DIR
}

# Install system dependencies
install_dependencies() {
    print_message "Installing system dependencies..."
    
    # Update package list
    apt-get update -y
    
    # Install Python and pip
    apt-get install -y python3.9 python3.9-dev python3-pip python3-venv
    
    # Install system packages
    apt-get install -y \
        git \
        nginx \
        supervisor \
        redis-server \
        postgresql \
        postgresql-contrib \
        libpq-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        curl \
        wget \
        htop \
        net-tools
    
    # Install Docker (if needed)
    if [ "$INSTALL_DOCKER" = "true" ]; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
    fi
}

# Setup Python virtual environment
setup_python_env() {
    print_message "Setting up Python virtual environment..."
    
    cd $APP_DIR
    
    # Create virtual environment
    python3.9 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # Install core dependencies
        pip install \
            aiohttp==3.8.4 \
            aiogram==3.0.0 \
            sqlalchemy==2.0.0 \
            fastapi==0.100.0 \
            uvicorn==0.23.0 \
            psutil==5.9.5 \
            redis==4.5.5 \
            pydantic==2.0.0 \
            yaml==6.0 \
            alembic==1.11.0 \
            requests==2.31.0 \
            beautifulsoup4==4.12.0 \
            selenium==4.11.0 \
            undetected-chromedriver==3.5.0 \
            python-dotenv==1.0.0 \
            cryptography==41.0.0 \
            bcrypt==4.0.1 \
            pyjwt==2.8.0
    fi
    
    deactivate
}

# Configure PostgreSQL database
setup_database() {
    print_message "Setting up PostgreSQL database..."
    
    # Start PostgreSQL service
    systemctl start postgresql
    systemctl enable postgresql
    
    # Create database and user
    sudo -u postgres psql << EOF
CREATE DATABASE $APP_NAME;
CREATE USER $APP_NAME WITH PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE $APP_NAME TO $APP_NAME;
ALTER DATABASE $APP_NAME OWNER TO $APP_NAME;
\c $APP_NAME
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOF
    
    print_message "PostgreSQL database created"
}

# Configure Redis
setup_redis() {
    print_message "Configuring Redis..."
    
    # Backup original config
    cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
    
    # Update Redis configuration
    cat > /etc/redis/redis.conf << EOF
bind 127.0.0.1
port 6379
daemonize yes
pidfile /var/run/redis/redis-server.pid
logfile /var/log/redis/redis-server.log
databases 16
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF
    
    systemctl restart redis-server
    systemctl enable redis-server
}

# Configure Nginx
setup_nginx() {
    print_message "Configuring Nginx..."
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/$APP_NAME << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME} www.${DOMAIN_NAME};
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN_NAME} www.${DOMAIN_NAME};
    
    # SSL certificates (update paths)
    ssl_certificate /etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Static files
    location /static/ {
        alias ${APP_DIR}/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias ${APP_DIR}/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
    
    # Admin panel
    location /admin/ {
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    
    # Test configuration
    nginx -t
    
    # Reload Nginx
    systemctl restart nginx
    systemctl enable nginx
}

# Configure Supervisor
setup_supervisor() {
    print_message "Configuring Supervisor..."
    
    # Create Supervisor configuration
    cat > /etc/supervisor/conf.d/$APP_NAME.conf << EOF
[program:$APP_NAME-api]
command=${APP_DIR}/venv/bin/uvicorn api.rest_api:app --host 0.0.0.0 --port 8000 --workers 4
directory=${APP_DIR}
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=${LOG_DIR}/api.error.log
stdout_logfile=${LOG_DIR}/api.access.log

[program:$APP_NAME-worker]
command=${APP_DIR}/venv/bin/python ${APP_DIR}/start.py --mode worker
directory=${APP_DIR}
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=${LOG_DIR}/worker.error.log
stdout_logfile=${LOG_DIR}/worker.access.log

[program:$APP_NAME-telegram]
command=${APP_DIR}/venv/bin/python ${APP_DIR}/start.py --mode telegram
directory=${APP_DIR}
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=${LOG_DIR}/telegram.error.log
stdout_logfile=${LOG_DIR}/telegram.access.log

[program:$APP_NAME-monitor]
command=${APP_DIR}/venv/bin/python ${APP_DIR}/start.py --mode monitor
directory=${APP_DIR}
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=${LOG_DIR}/monitor.error.log
stdout_logfile=${LOG_DIR}/monitor.access.log
EOF
    
    # Create Supervisor log directory
    mkdir -p /var/log/supervisor
    
    # Reload Supervisor
    supervisorctl reread
    supervisorctl update
    supervisorctl start $APP_NAME-*
}

# Create systemd service
create_systemd_service() {
    print_message "Creating systemd service..."
    
    cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=VT ULTRA PRO - TikTok Automation System
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
ExecStart=${APP_DIR}/venv/bin/python ${APP_DIR}/start.py --mode all
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$APP_NAME

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable $APP_NAME.service
}

# Setup SSL certificates
setup_ssl() {
    print_message "Setting up SSL certificates..."
    
    if [ "$ENABLE_SSL" = "true" ]; then
        # Install Certbot
        apt-get install -y certbot python3-certbot-nginx
        
        # Obtain SSL certificate
        certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --non-interactive --agree-tos --email $ADMIN_EMAIL
        
        # Setup auto-renewal
        echo "0 12 * * * root certbot renew --quiet" >> /etc/crontab
    else
        print_warning "SSL certificates not enabled"
    fi
}

# Create environment file
create_env_file() {
    print_message "Creating environment file..."
    
    cat > $ENV_FILE << EOF
# VT ULTRA PRO Environment Variables
# Generated on $(date)

# Application
APP_NAME="$APP_NAME"
APP_ENV="production"
SECRET_KEY="${SECRET_KEY}"
DEBUG="false"

# Database
DB_TYPE="postgresql"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="$APP_NAME"
DB_USER="$APP_NAME"
DB_PASSWORD="${DB_PASSWORD}"
DATABASE_URL="postgresql://${APP_NAME}:${DB_PASSWORD}@localhost:5432/${APP_NAME}"

# Redis
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD=""
REDIS_URL="redis://localhost:6379/0"

# Telegram
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
TELEGRAM_ADMIN_IDS="${TELEGRAM_ADMIN_IDS}"

# API
API_HOST="0.0.0.0"
API_PORT="8000"
API_WORKERS="4"

# Security
ALLOWED_HOSTS="${DOMAIN_NAME},www.${DOMAIN_NAME},localhost"
CORS_ORIGINS="https://${DOMAIN_NAME},https://www.${DOMAIN_NAME}"

# Email
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USERNAME="${SMTP_USERNAME}"
SMTP_PASSWORD="${SMTP_PASSWORD}"
EMAIL_FROM="noreply@${DOMAIN_NAME}"

# Monitoring
SENTRY_DSN="${SENTRY_DSN}"
LOG_LEVEL="INFO"
EOF
    
    chmod 600 $ENV_FILE
}

# Backup existing installation
backup_existing() {
    if [ -d "$APP_DIR" ]; then
        print_message "Backing up existing installation..."
        
        BACKUP_FILE="$BACKUP_DIR/${APP_NAME}_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar -czf $BACKUP_FILE -C /opt $APP_NAME
        
        print_message "Backup created: $BACKUP_FILE"
    fi
}

# Deploy application code
deploy_code() {
    print_message "Deploying application code..."
    
    cd $APP_DIR
    
    if [ "$DEPLOY_METHOD" = "git" ]; then
        # Clone or pull from Git
        if [ -d ".git" ]; then
            git pull origin $GIT_BRANCH
        else
            git clone $GIT_REPO .
            git checkout $GIT_BRANCH
        fi
    elif [ "$DEPLOY_METHOD" = "upload" ]; then
        # Extract uploaded archive
        if [ -f "$UPLOAD_PATH" ]; then
            tar -xzf $UPLOAD_PATH -C $APP_DIR --strip-components=1
        fi
    fi
    
    # Set permissions
    chown -R www-data:www-data $APP_DIR
    chmod -R 755 $APP_DIR
}

# Run database migrations
run_migrations() {
    print_message "Running database migrations..."
    
    cd $APP_DIR
    source venv/bin/activate
    
    # Run Alembic migrations
    if [ -f "alembic.ini" ]; then
        alembic upgrade head
    else
        # Initialize Alembic if not exists
        alembic init alembic
        # Update alembic.ini with database URL
        sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = ${DATABASE_URL}|" alembic.ini
        # Create initial migration
        alembic revision --autogenerate -m "Initial migration"
        alembic upgrade head
    fi
    
    deactivate
}

# Restart services
restart_services() {
    print_message "Restarting services..."
    
    systemctl restart nginx
    systemctl restart postgresql
    systemctl restart redis-server
    supervisorctl restart all
    
    if [ -f "/etc/systemd/system/$APP_NAME.service" ]; then
        systemctl restart $APP_NAME.service
    fi
}

# Print deployment summary
print_summary() {
    print_message "Deployment completed successfully!"
    echo ""
    echo "══════════════════════════════════════════════════════════════"
    echo "                    DEPLOYMENT SUMMARY"
    echo "══════════════════════════════════════════════════════════════"
    echo ""
    echo "Application:      $APP_NAME"
    echo "Environment:      Production"
    echo "Installation:     $APP_DIR"
    echo "Logs:             $LOG_DIR"
    echo "Database:         PostgreSQL ($APP_NAME)"
    echo "Cache:            Redis (localhost:6379)"
    echo "Web Server:       Nginx"
    echo "Process Manager:  Supervisor"
    echo ""
    echo "Services Status:"
    echo "  • PostgreSQL:   $(systemctl is-active postgresql)"
    echo "  • Redis:        $(systemctl is-active redis-server)"
    echo "  • Nginx:        $(systemctl is-active nginx)"
    echo "  • Supervisor:   $(systemctl is-active supervisor)"
    echo ""
    echo "Access URLs:"
    echo "  • Website:      https://$DOMAIN_NAME"
    echo "  • API:          https://$DOMAIN_NAME/api"
    echo "  • Admin:        https://$DOMAIN_NAME/admin"
    echo ""
    echo "Next steps:"
    echo "  1. Configure Telegram bot token in $ENV_FILE"
    echo "  2. Setup payment gateway credentials"
    echo "  3. Configure proxy providers"
    echo "  4. Test the system thoroughly"
    echo ""
    echo "══════════════════════════════════════════════════════════════"
}

# Main deployment function
deploy() {
    print_message "Starting VT ULTRA PRO deployment..."
    
    # Check if running as root
    check_root
    
    # Load deployment configuration
    if [ -f "deploy.config" ]; then
        source deploy.config
    fi
    
    # Set default values
    DOMAIN_NAME=${DOMAIN_NAME:-"example.com"}
    ADMIN_EMAIL=${ADMIN_EMAIL:-"admin@example.com"}
    DB_PASSWORD=${DB_PASSWORD:-$(openssl rand -hex 16)}
    SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}
    DEPLOY_METHOD=${DEPLOY_METHOD:-"git"}
    GIT_REPO=${GIT_REPO:-"https://github.com/yourusername/vt-ultra-pro.git"}
    GIT_BRANCH=${GIT_BRANCH:-"main"}
    ENABLE_SSL=${ENABLE_SSL:-"true"}
    INSTALL_DOCKER=${INSTALL_DOCKER:-"false"}
    
    # Backup existing installation
    backup_existing
    
    # Create directory structure
    create_directories
    
    # Install dependencies
    install_dependencies
    
    # Deploy code
    deploy_code
    
    # Setup Python environment
    setup_python_env
    
    # Setup database
    setup_database
    
    # Setup Redis
    setup_redis
    
    # Create environment file
    create_env_file
    
    # Run migrations
    run_migrations
    
    # Setup SSL certificates
    setup_ssl
    
    # Setup Nginx
    setup_nginx
    
    # Setup Supervisor
    setup_supervisor
    
    # Create systemd service
    create_systemd_service
    
    # Restart services
    restart_services
    
    # Print summary
    print_summary
    
    print_message "Deployment completed in $(($SECONDS / 60)) minutes and $(($SECONDS % 60)) seconds"
}

# Handle command line arguments
case "$1" in
    deploy)
        deploy
        ;;
    backup)
        backup_existing
        ;;
    restore)
        print_error "Restore function not implemented yet"
        ;;
    update)
        deploy_code
        run_migrations
        restart_services
        print_message "Update completed"
        ;;
    status)
        echo "Service Status:"
        echo "PostgreSQL: $(systemctl is-active postgresql)"
        echo "Redis:      $(systemctl is-active redis-server)"
        echo "Nginx:      $(systemctl is-active nginx)"
        echo "Supervisor: $(systemctl is-active supervisor)"
        supervisorctl status
        ;;
    logs)
        tail -f $LOG_DIR/*.log
        ;;
    help|*)
        echo "VT ULTRA PRO Deployment Script"
        echo ""
        echo "Usage: $0 {deploy|backup|restore|update|status|logs|help}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment of the application"
        echo "  backup   - Create backup of existing installation"
        echo "  restore  - Restore from backup (not implemented)"
        echo "  update   - Update code and restart services"
        echo "  status   - Check service status"
        echo "  logs     - Tail application logs"
        echo "  help     - Show this help message"
        echo ""
        echo "Before running deploy, create deploy.config with variables:"
        echo "  DOMAIN_NAME=yourdomain.com"
        echo "  ADMIN_EMAIL=admin@yourdomain.com"
        echo "  TELEGRAM_BOT_TOKEN=your_bot_token"
        echo "  TELEGRAM_ADMIN_IDS=123456789"
        echo "  SMTP_USERNAME=your_email@gmail.com"
        echo "  SMTP_PASSWORD=your_app_password"
        echo "  SENTRY_DSN=your_sentry_dsn"
        exit 1
        ;;
esac