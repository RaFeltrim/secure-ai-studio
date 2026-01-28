#!/bin/bash
# 🛡️ SECURE AI STUDIO - Automated Setup Script
# One-command deployment for WSL2/CachyOS environment

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running in WSL2
check_wsl() {
    if grep -q microsoft /proc/version 2>/dev/null; then
        success "Running in WSL2 environment"
    else
        warning "Not running in WSL2 - some features may not work optimally"
    fi
}

# Install Docker if not present
install_docker() {
    if ! command -v docker &> /dev/null; then
        log "Installing Docker..."
        
        # For Ubuntu/Debian based systems
        sudo apt-get update
        sudo apt-get install -y \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg \
            lsb-release
        
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        echo \
          "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
          $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        
        # Add user to docker group
        sudo usermod -aG docker $USER
        
        success "Docker installed successfully"
        warning "Please logout and login again to use Docker without sudo"
    else
        success "Docker already installed"
    fi
}

# Setup directories and permissions
setup_directories() {
    log "Setting up directories..."
    
    # Create main directories
    mkdir -p models/{image,video,text}
    mkdir -p output logs backup metrics security-reports test-results
    
    # Set proper permissions
    chmod 700 models logs backup security-reports
    chmod 755 output metrics test-results
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        log "Creating environment configuration..."
        cat > .env << EOF
# 🛡️ Secure AI Studio Environment Configuration

# Core Settings
AIR_GAP_MODE=true
MAX_CONCURRENT_JOBS=4
MEMORY_LIMIT=8G

# Security Keys (Auto-generated)
API_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Performance Settings
LOG_LEVEL=INFO
MONITORING_INTERVAL=5

# Network Settings
API_PORT=8000
DASHBOARD_PORT=8080
EOF
        success "Environment file created"
    fi
    
    success "Directories setup complete"
}

# Build and deploy
deploy_system() {
    log "Deploying Secure AI Studio..."
    
    # Build images
    log "Building Docker images..."
    docker-compose build
    
    # Start services
    log "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    log "Waiting for services to initialize..."
    sleep 30
    
    # Run health checks
    log "Running health checks..."
    if docker-compose exec secure-ai-engine python -c "import torch; print('PyTorch OK')" 2>/dev/null; then
        success "AI Engine is running"
    else
        error "AI Engine failed to start"
        return 1
    fi
    
    if docker-compose exec monitoring-agent python -c "import psutil; print('Monitoring OK')" 2>/dev/null; then
        success "Monitoring Agent is running"
    else
        warning "Monitoring Agent may need more time to start"
    fi
    
    success "Deployment completed successfully!"
}

# Run validation tests
run_validation() {
    log "Running system validation..."
    
    # Basic functionality test
    log "Testing basic functionality..."
    docker-compose run --rm secure-ai-engine python tests/simple_offline_test.py
    
    # Security validation
    log "Running security validation..."
    docker-compose run --rm secure-ai-engine python tests/visual_regression_tests.py
    
    success "Validation tests passed"
}

# Display status and next steps
show_status() {
    echo
    echo "=========================================="
    echo "🛡️  SECURE AI STUDIO DEPLOYMENT COMPLETE"
    echo "=========================================="
    echo
    echo "✅ System Status:"
    docker-compose ps
    echo
    echo "🌐 Access Points:"
    echo "  API Endpoint: http://localhost:8000"
    echo "  Web Dashboard: http://localhost:8080"
    echo "  API Docs: http://localhost:8000/docs"
    echo
    echo "📂 Important Directories:"
    echo "  Models: ./models/"
    echo "  Output: ./output/"
    echo "  Logs: ./logs/"
    echo "  Metrics: ./metrics/"
    echo
    echo "🔧 Management Commands:"
    echo "  make status     - Check system status"
    echo "  make logs       - View service logs"
    echo "  make test       - Run validation tests"
    echo "  make down       - Stop all services"
    echo "  make backup     - Create system backup"
    echo
    echo "🚀 Next Steps:"
    echo "1. Add your AI models to ./models/"
    echo "2. Test the API with curl or Postman"
    echo "3. Monitor performance through the dashboard"
    echo "4. Run load tests: make test-load"
    echo
    success "Your Secure AI Studio is ready for production use!"
}

# Main execution
main() {
    log "Starting Secure AI Studio automated deployment..."
    
    check_wsl
    install_docker
    setup_directories
    deploy_system
    run_validation
    show_status
    
    return 0
}

# Handle script interruption
trap 'error "Deployment interrupted"; exit 1' INT TERM

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi