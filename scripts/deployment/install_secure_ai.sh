#!/bin/bash
# 🛡️ SECURE AI STUDIO - Linux Deployment Script
# Comprehensive setup for offline AI content generation system

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root"
        exit 1
    fi
}

# Verify system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check WSL2 environment
    if ! grep -q microsoft /proc/version 2>/dev/null; then
        warning "Not running in WSL2 environment"
    fi
    
    # Check available disk space
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 52428800 ]]; then  # 50GB in KB
        error "Insufficient disk space. Minimum 50GB required."
        exit 1
    fi
    
    # Check RAM
    total_ram=$(free -m | awk '/^Mem:/{print $2}')
    if [[ $total_ram -lt 16000 ]]; then
        warning "Less than 16GB RAM detected. Performance may be impacted."
    fi
    
    success "System requirements check passed"
}

# Setup directory structure
setup_directories() {
    log "Setting up directory structure..."
    
    local base_dir="/opt/secure-ai-studio"
    
    # Create main directories with proper permissions
    sudo mkdir -p "$base_dir"/{core,models,assets,output,scripts,config,logs,backup,docs,tests}
    sudo mkdir -p "$base_dir/core"/{engine,security,ui}
    sudo mkdir -p "$base_dir/models"/{image,video,text}
    sudo mkdir -p "$base_dir/assets"/{templates,branding,watermarks}
    sudo mkdir -p "$base_dir/scripts"/{deployment,maintenance,utilities}
    
    # Set proper ownership and permissions
    sudo chown -R $USER:$USER "$base_dir"
    sudo chmod 755 "$base_dir"
    sudo chmod 700 "$base_dir"/{config,logs,backup}
    sudo chmod 755 "$base_dir"/{core,models,assets,output,scripts,docs,tests}
    
    # Create user-specific directories
    mkdir -p "$HOME/.secure-ai"/{cache,temp,preferences}
    
    success "Directory structure created"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    # Update package lists
    sudo pacman -Syu --noconfirm
    
    # Core dependencies
    sudo pacman -S --noconfirm \
        python3 python-pip \
        opencv python-opencv \
        ffmpeg python-ffmpeg-python \
        pillow python-pillow \
        numpy python-numpy \
        scikit-image python-scikit-image \
        cryptography python-cryptography \
        tk python-tk \
        git wget curl \
        htop tree nano vim
    
    # Development tools
    sudo pacman -S --noconfirm \
        python-setuptools \
        python-wheel \
        python-devtools
    
    success "System dependencies installed"
}

# Setup Python environment
setup_python_environment() {
    log "Setting up Python environment..."
    
    # Create virtual environment
    python3 -m venv "$HOME/.secure-ai/venv"
    
    # Activate virtual environment
    source "$HOME/.secure-ai/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python packages
    pip install \
        torch torchvision torchaudio \
        opencv-python-headless \
        Pillow \
        numpy \
        scikit-image \
        cryptography \
        moviepy \
        tqdm \
        pyyaml \
        watchdog
    
    deactivate
    
    success "Python environment configured"
}

# Configure security settings
configure_security() {
    log "Configuring security settings..."
    
    local config_dir="/opt/secure-ai-studio/config"
    
    # Create firewall rules (basic)
    sudo iptables -P INPUT DROP
    sudo iptables -P FORWARD DROP
    sudo iptables -P OUTPUT DROP
    
    # Allow loopback
    sudo iptables -A INPUT -i lo -j ACCEPT
    sudo iptables -A OUTPUT -o lo -j ACCEPT
    
    # Allow established connections
    sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    
    # Save firewall rules
    sudo iptables-save | sudo tee /etc/iptables/rules.v4 > /dev/null
    
    # Disable unnecessary services
    sudo systemctl disable --now bluetooth.service 2>/dev/null || true
    sudo systemctl disable --now cups.service 2>/dev/null || true
    
    # Set up audit logging
    sudo pacman -S --noconfirm audit
    sudo systemctl enable --now auditd
    
    success "Security configuration completed"
}

# Setup AI models (offline installation)
setup_ai_models() {
    log "Setting up AI models..."
    
    local models_dir="/opt/secure-ai-studio/models"
    
    # Create placeholder for model installation
    # In production, this would involve copying pre-downloaded models
    touch "$models_dir/.models_ready"
    
    # Set restrictive permissions on models directory
    sudo chmod 700 "$models_dir"
    
    success "AI models setup completed"
}

# Install brand assets
install_brand_assets() {
    log "Installing brand assets..."
    
    local assets_dir="/opt/secure-ai-studio/assets"
    
    # Create placeholder brand assets
    echo "COMPANY LOGO PLACEHOLDER" > "$assets_dir/branding/company_logo.txt"
    echo "WATERMARK TEMPLATE" > "$assets_dir/watermarks/default_watermark.txt"
    echo "CONTENT TEMPLATES" > "$assets_dir/templates/default_template.txt"
    
    # Set proper permissions
    chmod 600 "$assets_dir"/branding/*
    chmod 600 "$assets_dir"/watermarks/*
    chmod 644 "$assets_dir"/templates/*
    
    success "Brand assets installed"
}

# Create system services
create_services() {
    log "Creating system services..."
    
    # Create systemd service for AI engine
    sudo tee /etc/systemd/system/secure-ai-engine.service > /dev/null << EOF
[Unit]
Description=Secure AI Studio Engine
After=network.target
ConditionPathExists=!/opt/secure-ai-studio/config/network_enabled

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/secure-ai-studio
ExecStart=/home/$USER/.secure-ai/venv/bin/python /opt/secure-ai-studio/core/engine/secure_ai_engine.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    success "System services created"
}

# Setup backup system
setup_backup() {
    log "Setting up backup system..."
    
    local backup_dir="/opt/secure-ai-studio/backup"
    
    # Create backup script
    tee "$HOME/.secure-ai/scripts/backup.sh" > /dev/null << 'EOF'
#!/bin/bash
# Secure backup script

BACKUP_DIR="/opt/secure-ai-studio/backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="secure_ai_backup_$TIMESTAMP.tar.gz"

# Create backup
tar -czf "$BACKUP_DIR/$BACKUP_NAME" \
    --exclude="$BACKUP_DIR" \
    --exclude="/opt/secure-ai-studio/models" \
    /opt/secure-ai-studio

# Remove old backups (keep last 7)
cd "$BACKUP_DIR"
ls -t secure_ai_backup_*.tar.gz | tail -n +8 | xargs -r rm

echo "Backup completed: $BACKUP_NAME"
EOF
    
    chmod +x "$HOME/.secure-ai/scripts/backup.sh"
    
    # Setup cron job for daily backups
    (crontab -l 2>/dev/null; echo "0 2 * * * $HOME/.secure-ai/scripts/backup.sh") | crontab -
    
    success "Backup system configured"
}

# Create user interface launcher
create_launcher() {
    log "Creating user interface launcher..."
    
    # Create desktop entry
    tee "$HOME/.local/share/applications/secure-ai-studio.desktop" > /dev/null << EOF
[Desktop Entry]
Name=Secure AI Studio
Comment=Offline AI Content Generation Studio
Exec=/opt/secure-ai-studio/scripts/deployment/launch_studio.sh
Icon=application-x-executable
Terminal=false
Type=Application
Categories=Graphics;Office;
EOF
    
    # Create launch script
    tee "/opt/secure-ai-studio/scripts/deployment/launch_studio.sh" > /dev/null << 'EOF'
#!/bin/bash
# Launch Secure AI Studio

cd /opt/secure-ai-studio
source "$HOME/.secure-ai/venv/bin/activate"
python core/ui/main_ui.py
EOF
    
    chmod +x "/opt/secure-ai-studio/scripts/deployment/launch_studio.sh"
    
    success "User interface launcher created"
}

# Final system verification
final_verification() {
    log "Performing final system verification..."
    
    # Check directory permissions
    if [[ ! -d "/opt/secure-ai-studio" ]]; then
        error "Installation directory not found"
        exit 1
    fi
    
    # Check Python environment
    if [[ ! -d "$HOME/.secure-ai/venv" ]]; then
        error "Python virtual environment not found"
        exit 1
    fi
    
    # Test AI engine import
    source "$HOME/.secure-ai/venv/bin/activate"
    python -c "import sys; sys.path.append('/opt/secure-ai-studio/core/engine'); import secure_ai_engine" || {
        error "Failed to import AI engine"
        exit 1
    }
    
    deactivate
    
    success "Final verification passed"
}

# Main installation function
main() {
    log "Starting Secure AI Studio installation..."
    
    check_root
    check_requirements
    setup_directories
    install_dependencies
    setup_python_environment
    configure_security
    setup_ai_models
    install_brand_assets
    create_services
    setup_backup
    create_launcher
    final_verification
    
    log "Installation completed successfully!"
    echo
    success "Secure AI Studio is now ready for use"
    echo "To launch the application, run:"
    echo "  /opt/secure-ai-studio/scripts/deployment/launch_studio.sh"
    echo
    warning "Remember: This system operates in complete offline mode for security"
}

# Run main function
main "$@"