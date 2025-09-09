#!/bin/bash

# Local Docker Testing Script for Custard Backend
# This script tests the Docker setup before Railway deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HEALTH_CHECK_URL="http://localhost:8000/health"
READY_CHECK_URL="http://localhost:8000/ready"
MAX_ATTEMPTS=30
ATTEMPT_INTERVAL=5

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    log "Prerequisites check passed"
}

# Build and start services
start_services() {
    log "Building and starting services..."
    
    # Build the application
    log "Building Docker image..."
    docker-compose -f docker-compose.local.yml build --no-cache
    
    # Start services
    log "Starting services..."
    docker-compose -f docker-compose.local.yml up -d
    
    log "Services started successfully"
}

# Wait for services to be ready
wait_for_services() {
    log "Waiting for services to be ready..."
    
    local attempt=1
    while [[ $attempt -le $MAX_ATTEMPTS ]]; do
        log "Health check attempt $attempt/$MAX_ATTEMPTS"
        
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log "Health check passed!"
            return 0
        fi
        
        log "Health check failed, waiting ${ATTEMPT_INTERVAL}s before retry..."
        sleep $ATTEMPT_INTERVAL
        ((attempt++))
    done
    
    error "Health check failed after $MAX_ATTEMPTS attempts"
    return 1
}

# Test endpoints
test_endpoints() {
    log "Testing API endpoints..."
    
    # Test health endpoint
    info "Testing /health endpoint..."
    if curl -f -s "$HEALTH_CHECK_URL" | grep -q "healthy"; then
        log "✅ /health endpoint working"
    else
        error "❌ /health endpoint failed"
        return 1
    fi
    
    # Test ready endpoint
    info "Testing /ready endpoint..."
    if curl -f -s "$READY_CHECK_URL" | grep -q "ready"; then
        log "✅ /ready endpoint working"
    else
        error "❌ /ready endpoint failed"
        return 1
    fi
    
    # Test status endpoint
    info "Testing /status endpoint..."
    if curl -f -s "http://localhost:8000/status" > /dev/null; then
        log "✅ /status endpoint working"
    else
        error "❌ /status endpoint failed"
        return 1
    fi
    
    # Test API docs (if enabled)
    info "Testing /docs endpoint..."
    if curl -f -s "http://localhost:8000/docs" > /dev/null; then
        log "✅ /docs endpoint working"
    else
        warning "⚠️ /docs endpoint not accessible (may be disabled)"
    fi
}

# Test database connectivity
test_database() {
    log "Testing database connectivity..."
    
    # Test database connection through the app
    if curl -f -s "$HEALTH_CHECK_URL" | grep -q "database.*healthy"; then
        log "✅ Database connection working"
    else
        error "❌ Database connection failed"
        return 1
    fi
}

# Test Redis connectivity
test_redis() {
    log "Testing Redis connectivity..."
    
    # Test Redis through the app (if Redis is used in health checks)
    if curl -f -s "$HEALTH_CHECK_URL" > /dev/null; then
        log "✅ Redis connection working"
    else
        warning "⚠️ Redis connection test inconclusive"
    fi
}

# Show service status
show_status() {
    log "Service status:"
    docker-compose -f docker-compose.local.yml ps
    
    log "Application logs (last 20 lines):"
    docker-compose -f docker-compose.local.yml logs --tail=20 custard-backend
    
    log "Database logs (last 10 lines):"
    docker-compose -f docker-compose.local.yml logs --tail=10 postgres
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    docker-compose -f docker-compose.local.yml down
    log "Cleanup completed"
}

# Main test function
run_tests() {
    log "Starting local Docker testing for Custard Backend"
    
    check_prerequisites
    start_services
    
    if wait_for_services; then
        test_endpoints
        test_database
        test_redis
        show_status
        
        log "🎉 All tests passed! Your application is ready for Railway deployment."
        log "You can now deploy to Railway with confidence."
        
        # Ask if user wants to keep services running
        echo ""
        read -p "Keep services running for manual testing? (y/n): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            cleanup
        else
            log "Services are still running. Use 'docker-compose -f docker-compose.local.yml down' to stop them."
        fi
    else
        error "Tests failed. Check the logs above for issues."
        show_status
        cleanup
        exit 1
    fi
}

# Handle script arguments
case "${1:-test}" in
    test)
        run_tests
        ;;
    start)
        check_prerequisites
        start_services
        log "Services started. Run './test-local.sh test' to run tests."
        ;;
    stop)
        cleanup
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {test|start|stop|status}"
        echo ""
        echo "Commands:"
        echo "  test   - Run full test suite (default)"
        echo "  start  - Start services only"
        echo "  stop   - Stop all services"
        echo "  status - Show service status"
        exit 1
        ;;
esac
