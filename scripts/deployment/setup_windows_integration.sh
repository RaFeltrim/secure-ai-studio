#!/bin/bash
# 🛡️ SECURE AI STUDIO - Windows Integration Script
# Bridge between Windows host and Linux WSL2 environment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
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

# Check if running in WSL2
check_wsl2() {
    if ! grep -q microsoft /proc/version 2>/dev/null; then
        error "This script must be run in WSL2 environment"
        exit 1
    fi
}

# Setup Windows-WLS integration
setup_windows_integration() {
    log "Setting up Windows-WSL integration..."
    
    # Create shared directories
    local shared_dirs=(
        "/mnt/c/Users/$(whoami)/Documents/SecureAI_Output"
        "/mnt/c/Users/$(whoami)/Documents/SecureAI_Assets"
        "/mnt/c/Users/$(whoami)/Documents/SecureAI_Backup"
    )
    
    for dir in "${shared_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            chmod 755 "$dir"
            log "Created shared directory: $dir"
        fi
    done
    
    # Create symbolic links for easy access
    ln -sf "/mnt/c/Users/$(whoami)/Documents/SecureAI_Output" "/opt/secure-ai-studio/windows_output" 2>/dev/null || true
    ln -sf "/mnt/c/Users/$(whoami)/Documents/SecureAI_Assets" "/opt/secure-ai-studio/windows_assets" 2>/dev/null || true
    
    success "Windows integration setup completed"
}

# Configure display server (VcXsrv)
configure_display() {
    log "Configuring display server..."
    
    # Check if VcXsrv is running
    if ! pgrep -f "vcxsrv" > /dev/null 2>&1; then
        warning "VcXsrv not detected. GUI applications may not work."
        warning "Please start VcXsrv with: :0 -clipboard -multiwindow"
    else
        export DISPLAY=:0
        log "Display server configured: $DISPLAY"
    fi
}

# Setup file sharing permissions
setup_file_permissions() {
    log "Setting up file sharing permissions..."
    
    # Add user to relevant groups
    sudo usermod -a -G audio,video,input "$(whoami)" 2>/dev/null || true
    
    # Set proper umask for shared files
    echo "umask 022" >> "$HOME/.bashrc"
    
    success "File permissions configured"
}

# Create Windows batch scripts
create_windows_scripts() {
    log "Creating Windows integration scripts..."
    
    local windows_scripts_dir="/mnt/c/Users/$(whoami)/Documents/SecureAI_Scripts"
    mkdir -p "$windows_scripts_dir"
    
    # Create main launcher
    tee "$windows_scripts_dir/launch_secure_ai.bat" > /dev/null << 'EOF'
@echo off
title Secure AI Studio Launcher
color 0A

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║                   SECURE AI STUDIO                           ║
echo ║              OFFLINE CONTENT GENERATION                      ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo Checking system requirements...
wsl -l -v | findstr -i "arch\|cachyos" >nul
if %errorlevel% neq 0 (
    echo ❌ CachyOS/Arch Linux not found in WSL
    echo Please install CachyOS WSL2 distribution
    pause
    exit /b 1
)

echo ✅ Linux environment available

echo Starting Secure AI Studio...
wsl -d archlinux -u $(whoami) bash -c "cd /opt/secure-ai-studio && source ~/.secure-ai/venv/bin/activate && python core/ui/main_ui.py"

echo.
echo Secure AI Studio session ended
pause
EOF

    # Create management console
    tee "$windows_scripts_dir/manage_secure_ai.bat" > /dev/null << 'EOF'
@echo off
title Secure AI Studio Management Console
color 0B

:menu
cls
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║              SECURE AI STUDIO MANAGEMENT                     ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Select operation:
echo 1. Start Secure AI Studio
echo 2. Check System Status
echo 3. View Recent Logs
echo 4. Backup System
echo 5. Update Models
echo 6. Exit
echo.

choice /c 123456 /m "Enter choice"

if %errorlevel%==1 goto :start_studio
if %errorlevel%==2 goto :system_status
if %errorlevel%==3 goto :view_logs
if %errorlevel%==4 goto :backup_system
if %errorlevel%==5 goto :update_models
if %errorlevel%==6 goto :exit

:start_studio
echo Starting Secure AI Studio...
wsl -d archlinux -u $(whoami) /opt/secure-ai-studio/scripts/deployment/launch_studio.sh
goto :menu

:system_status
echo.
echo === SYSTEM STATUS ===
wsl -d archlinux -u $(whoami) bash -c "df -h /opt/secure-ai-studio"
wsl -d archlinux -u $(whoami) bash -c "free -h"
wsl -d archlinux -u $(whoami) bash -c "ps aux | grep -i 'secure\|ai' | head -10"
echo.
pause
goto :menu

:view_logs
echo.
echo === RECENT LOGS ===
wsl -d archlinux -u $(whoami) bash -c "tail -20 /opt/secure-ai-studio/logs/*.log"
echo.
pause
goto :menu

:backup_system
echo.
echo === SYSTEM BACKUP ===
wsl -d archlinux -u $(whoami) ~/.secure-ai/scripts/backup.sh
echo Backup completed
pause
goto :menu

:update_models
echo.
echo === MODEL UPDATE ===
echo Updating AI models...
wsl -d archlinux -u $(whoami) bash -c "cd /opt/secure-ai-studio && source ~/.secure-ai/venv/bin/activate && python scripts/maintenance/update_models.py"
echo Models updated
pause
goto :menu

:exit
echo Goodbye!
exit /b 0
EOF

    # Make scripts executable from Windows
    chmod +x "$windows_scripts_dir"/*.bat 2>/dev/null || true
    
    success "Windows scripts created in: $windows_scripts_dir"
}

# Setup automatic startup
setup_autostart() {
    log "Setting up automatic startup..."
    
    # Create autostart script
    tee "$HOME/.secure-ai/scripts/autostart.sh" > /dev/null << 'EOF'
#!/bin/bash
# Secure AI Studio autostart script

# Check if system is properly configured
if [[ ! -f "/opt/secure-ai-studio/.installed" ]]; then
    echo "System not properly installed"
    exit 1
fi

# Start essential services
systemctl --user start secure-ai-engine.service 2>/dev/null || true

# Verify display server
if [[ -z "$DISPLAY" ]]; then
    export DISPLAY=:0
fi

echo "Secure AI Studio autostart completed"
EOF
    
    chmod +x "$HOME/.secure-ai/scripts/autostart.sh"
    
    # Add to user's bash profile
    if ! grep -q "secure-ai-autostart" "$HOME/.bashrc"; then
        echo "# Secure AI Studio autostart" >> "$HOME/.bashrc"
        echo "~/.secure-ai/scripts/autostart.sh" >> "$HOME/.bashrc"
    fi
    
    success "Autostart configured"
}

# Performance optimization
optimize_performance() {
    log "Optimizing system performance..."
    
    # Configure swappiness
    echo 'vm.swappiness=1' | sudo tee -a /etc/sysctl.conf > /dev/null
    
    # Optimize I/O scheduler
    echo 'deadline' | sudo tee /sys/block/sda/queue/scheduler > /dev/null 2>&1 || true
    
    # Set CPU governor to performance
    echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null 2>&1 || true
    
    success "Performance optimization completed"
}

# Final integration verification
final_verification() {
    log "Performing final integration verification..."
    
    # Test WSL2 connectivity
    wsl -d archlinux -u "$(whoami)" echo "WSL2 connectivity test" > /dev/null || {
        error "WSL2 connectivity test failed"
        exit 1
    }
    
    # Test shared directory access
    if [[ ! -d "/mnt/c/Users/$(whoami)/Documents/SecureAI_Output" ]]; then
        warning "Shared directories not accessible from Linux"
    fi
    
    # Test display configuration
    if [[ -n "$DISPLAY" ]] && command -v xset > /dev/null 2>&1; then
        timeout 5 xset q > /dev/null 2>&1 && success "Display server accessible" || warning "Display server not responding"
    fi
    
    success "Integration verification completed"
}

# Main function
main() {
    log "Starting Windows-WSL integration setup..."
    
    check_wsl2
    setup_windows_integration
    configure_display
    setup_file_permissions
    create_windows_scripts
    setup_autostart
    optimize_performance
    final_verification
    
    log "Windows-WSL integration completed successfully!"
    echo
    success "Secure AI Studio Windows integration is ready"
    echo "Access your scripts at: /mnt/c/Users/$(whoami)/Documents/SecureAI_Scripts"
    echo "Shared output directory: /mnt/c/Users/$(whoami)/Documents/SecureAI_Output"
}

# Run main function
main "$@"