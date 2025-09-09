#!/bin/bash

# Custard Backend Production Deployment Script
# This script ensures safe deployment with health checks and rollback capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="./backups"
LOG_FILE="./deployment.log"
HEALTH_CHECK_URL="http://localhost:8000/ready"
MAX_HEALTH_CHECK_ATTEMPTS=30
HEALTH_CHECK_INTERVAL=10

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if environment file exists
    if [[ ! -f ".env.production" ]]; then
        error "Production environment file (.env.production) not found"
        exit 1
    fi
    
    log "Prerequisites check passed"
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_FILE="$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    # Backup database if running
    if docker-compose -f docker-compose.production.yml ps postgres | grep -q "Up"; then
        log "Backing up database..."
        docker-compose -f docker-compose.production.yml exec -T postgres pg_dump -U custard custard_db > "$BACKUP_DIR/db-backup-$(date +%Y%m%d-%H%M%S).sql"
    fi
    
    # Backup application data
    tar -czf "$BACKUP_FILE" --exclude='node_modules' --exclude='.git' --exclude='logs' .
    log "Backup created: $BACKUP_FILE"
}

# Health check function
health_check() {
    local attempt=1
    log "Performing health check..."
    
    while [[ $attempt -le $MAX_HEALTH_CHECK_ATTEMPTS ]]; do
        log "Health check attempt $attempt/$MAX_HEALTH_CHECK_ATTEMPTS"
        
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log "Health check passed"
            return 0
        fi
        
        log "Health check failed, waiting ${HEALTH_CHECK_INTERVAL}s before retry..."
        sleep $HEALTH_CHECK_INTERVAL
        ((attempt++))
    done
    
    error "Health check failed after $MAX_HEALTH_CHECK_ATTEMPTS attempts"
    return 1
}

# Deploy application
deploy() {
    log "Starting deployment..."
    
    # Pull latest images
    log "Pulling latest images..."
    docker-compose -f docker-compose.production.yml pull
    
    # Build application
    log "Building application..."
    docker-compose -f docker-compose.production.yml build --no-cache
    
    # Stop existing services gracefully
    log "Stopping existing services..."
    docker-compose -f docker-compose.production.yml down --timeout 30
    
    # Start services
    log "Starting services..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 30
    
    # Perform health check
    if ! health_check; then
        error "Deployment failed - health check did not pass"
        rollback
        exit 1
    fi
    
    log "Deployment completed successfully"
}

# Rollback function
rollback() {
    error "Initiating rollback..."
    
    # Stop current services
    docker-compose -f docker-compose.production.yml down
    
    # Find latest backup
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/backup-*.tar.gz 2>/dev/null | head -n1)
    
    if [[ -n "$LATEST_BACKUP" ]]; then
        log "Rolling back to: $LATEST_BACKUP"
        tar -xzf "$LATEST_BACKUP"
        
        # Restart services
        docker-compose -f docker-compose.production.yml up -d
        
        # Wait and check health
        sleep 30
        if health_check; then
            log "Rollback completed successfully"
        else
            error "Rollback failed - manual intervention required"
            exit 1
        fi
    else
        error "No backup found for rollback"
        exit 1
    fi
}

# Cleanup old backups
cleanup() {
    log "Cleaning up old backups..."
    
    # Keep only last 5 backups
    find "$BACKUP_DIR" -name "backup-*.tar.gz" -type f -printf '%T@ %p\n' | \
        sort -n | head -n -5 | cut -d' ' -f2- | xargs -r rm -f
    
    # Clean up old database backups
    find "$BACKUP_DIR" -name "db-backup-*.sql" -type f -mtime +7 -delete
    
    log "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting Custard Backend Production Deployment"
    
    check_root
    check_prerequisites
    create_backup
    deploy
    cleanup
    
    log "Deployment process completed successfully"
    log "Application is available at: http://localhost:8000"
    log "Health check: $HEALTH_CHECK_URL"
    log "Monitoring: http://localhost:3000 (Grafana)"
    log "Metrics: http://localhost:9090 (Prometheus)"
}

# Handle script arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    rollback)
        rollback
        ;;
    health-check)
        health_check
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|health-check|cleanup}"
        exit 1
        ;;
esac
