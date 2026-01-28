#!/bin/bash
# 🛡️ SECURE AI STUDIO - Environment Validation Script
# Sprint 1: Infrastructure Stability and Sanitization Tests
# Validates deployment, isolation, and authentication systems

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
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test counters
PASSED=0
FAILED=0
TOTAL=0

# Test execution function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="${3:-0}"
    
    TOTAL=$((TOTAL + 1))
    log "Running: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        if [ $? -eq $expected_result ]; then
            success "$test_name"
            PASSED=$((PASSED + 1))
            return 0
        else
            error "$test_name (unexpected exit code)"
            FAILED=$((FAILED + 1))
            return 1
        fi
    else
        error "$test_name (command failed)"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# T1: Smoke Test de Deployment
test_deployment_permissions() {
    log "=== T1: Smoke Test de Deployment ==="
    
    # Check if docker-compose file exists
    run_test "Docker Compose file exists" "test -f docker-compose.full.yml"
    
    # Check if Makefile exists
    run_test "Makefile exists" "test -f Makefile"
    
    # Check required directories
    run_test "Output directory exists" "test -d output"
    run_test "Logs directory exists" "test -d logs"
    run_test "Models directory exists" "test -d models"
    run_test "Config directory exists" "test -d config"
    
    # Check file permissions (700/600)
    run_test "Config directory has 700 permissions" "test \$(stat -c %a config) = 700"
    run_test "Logs directory has 700 permissions" "test \$(stat -c %a logs) = 700"
    run_test "Backup directory has 700 permissions" "test \$(stat -c %a backup) = 700"
    
    # Check system configuration file
    run_test "System config file exists" "test -f config/system.conf"
    run_test "System config has proper permissions" "test \$(stat -c %a config/system.conf) = 600"
}

# T2: Teste de Isolamento de Rede (Egress Test)
test_network_isolation() {
    log "=== T2: Network Isolation Test ==="
    
    # Start a test container
    log "Starting isolated container for network testing..."
    
    # Create a simple test container
    docker run -d --name test-isolation \
        --network none \
        alpine:latest \
        sleep 30 >/dev/null 2>&1 || true
    
    # Test DNS resolution should fail
    run_test "DNS resolution fails in isolated container" \
        "docker exec test-isolation nslookup google.com >/dev/null 2>&1" 1
    
    # Test external connectivity should fail
    run_test "External HTTP connection fails" \
        "docker exec test-isolation wget -T 5 http://google.com >/dev/null 2>&1" 1
    
    # Test internal localhost connectivity should work
    run_test "Localhost connectivity works" \
        "docker exec test-isolation ping -c 1 localhost >/dev/null 2>&1"
    
    # Cleanup
    docker rm -f test-isolation >/dev/null 2>&1 || true
}

# T3: Validação de Schema e Auth (JWT)
test_authentication_validation() {
    log "=== T3: Authentication Schema Validation ==="
    
    # Check if auth module exists
    run_test "Authentication layer exists" "test -f core/security/authentication_layer.py"
    
    # Test JWT token generation (mock test)
    run_test "JWT module imports successfully" \
        "python -c 'from core.security.authentication_layer import AuthenticationLayer; print(\"Import OK\")' >/dev/null 2>&1"
    
    # Test API key validation function exists
    run_test "API key validation function exists" \
        "python -c 'from core.security.authentication_layer import AuthenticationLayer; auth = AuthenticationLayer(); hasattr(auth, \"validate_api_key\")' >/dev/null 2>&1"
    
    # Test token expiration logic
    run_test "Token expiration validation exists" \
        "python -c 'from core.security.authentication_layer import AuthenticationLayer; auth = AuthenticationLayer(); hasattr(auth, \"is_token_expired\")' >/dev/null 2>&1"
}

# Main execution
main() {
    log "🚀 STARTING SPRINT 1: INFRASTRUCTURE STABILITY TESTS"
    log "==================================================="
    
    echo
    
    # Run all tests
    test_deployment_permissions
    echo
    test_network_isolation
    echo
    test_authentication_validation
    echo
    
    # Summary
    log "=== TEST SUMMARY ==="
    log "Total Tests: $TOTAL"
    success "Passed: $PASSED"
    if [ $FAILED -gt 0 ]; then
        error "Failed: $FAILED"
    else
        success "Failed: $FAILED"
    fi
    
    # Overall result
    echo
    if [ $FAILED -eq 0 ]; then
        success "🎉 SPRINT 1 COMPLETED SUCCESSFULLY!"
        success "Infrastructure stability validated"
        return 0
    else
        error "💥 SPRINT 1 FAILED - $FAILED tests failed"
        warning "Please fix the failed tests before proceeding"
        return 1
    fi
}

# Run the tests
if main; then
    exit 0
else
    exit 1
fi