#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Comprehensive Environment Validator
Enhanced Sprint 1 testing with detailed validation and reporting

Features:
- Deployment validation with permission checking
- Network isolation verification  
- Authentication system validation
- Detailed reporting in multiple formats
- Integration with existing infrastructure
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
import docker
from dataclasses import dataclass, asdict

@dataclass
class TestResult:
    """Individual test result"""
    name: str
    passed: bool
    message: str
    execution_time: float
    details: Dict[str, Any]

@dataclass
class TestSuiteReport:
    """Complete test suite results"""
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    test_results: List[TestResult]
    environment_info: Dict[str, str]

class EnvironmentValidator:
    """
    Comprehensive environment validation for Sprint 1
    """
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception:
            pass
    
    def run_comprehensive_validation(self) -> TestSuiteReport:
        """Run all Sprint 1 validation tests"""
        
        print("🚀 SECURE AI STUDIO - SPRINT 1 ENVIRONMENT VALIDATION")
        print("=" * 55)
        
        # Run all test categories
        self._validate_deployment()
        self._validate_network_isolation()
        self._validate_authentication()
        self._validate_monitoring()
        
        # Generate report
        return self._generate_report()
    
    def _validate_deployment(self):
        """T1: Comprehensive deployment validation"""
        print("\n📋 T1: DEPLOYMENT VALIDATION")
        print("-" * 30)
        
        # File structure validation
        required_files = [
            "Dockerfile",
            "docker-compose.full.yml",
            "Makefile",
            "config/system.conf",
            "core/engine/secure_ai_engine.py",
            "core/monitoring/internal_monitoring_agent.py"
        ]
        
        for file_path in required_files:
            self._run_test(
                f"File exists: {file_path}",
                lambda: Path(file_path).exists(),
                f"Checking existence of {file_path}"
            )
        
        # Directory structure validation
        required_dirs = ["output", "logs", "models", "config", "backup"]
        for dir_name in required_dirs:
            self._run_test(
                f"Directory exists: {dir_name}",
                lambda d=dir_name: Path(d).is_dir(),
                f"Checking directory {dir_name}"
            )
        
        # Permission validation
        permission_tests = [
            ("config", 0o700),
            ("logs", 0o700),
            ("backup", 0o700),
            ("config/system.conf", 0o600)
        ]
        
        for path, expected_perm in permission_tests:
            self._run_test(
                f"Permission check: {path}",
                lambda p=path, ep=expected_perm: self._check_permissions(p, ep),
                f"Validating permissions for {path}"
            )
        
        # Docker validation
        self._run_test(
            "Docker daemon accessible",
            lambda: self.docker_client is not None,
            "Checking Docker connectivity"
        )
        
        if self.docker_client:
            self._run_test(
                "Docker version check",
                lambda: self._check_docker_version(),
                "Verifying Docker version compatibility"
            )
    
    def _validate_network_isolation(self):
        """T2: Network isolation validation"""
        print("\n🌐 T2: NETWORK ISOLATION VALIDATION")
        print("-" * 35)
        
        if not self.docker_client:
            self._run_test(
                "Network isolation test skipped",
                lambda: False,
                "Docker not available"
            )
            return
        
        # Test isolated network
        self._run_test(
            "Isolated container network test",
            lambda: self._test_isolated_container(),
            "Testing network isolation with --network none"
        )
        
        # Test DNS blocking
        self._run_test(
            "DNS resolution blocking test",
            lambda: self._test_dns_blocking(),
            "Verifying DNS requests are blocked"
        )
        
        # Test external connectivity
        self._run_test(
            "External connectivity blocking test",
            lambda: self._test_external_connectivity(),
            "Verifying external connections are blocked"
        )
    
    def _validate_authentication(self):
        """T3: Authentication system validation"""
        print("\n🔐 T3: AUTHENTICATION VALIDATION")
        print("-" * 32)
        
        # Module existence
        self._run_test(
            "Authentication module exists",
            lambda: Path("core/security/authentication_layer.py").exists(),
            "Checking authentication layer file"
        )
        
        # Import validation
        self._run_test(
            "Authentication module imports",
            lambda: self._test_auth_imports(),
            "Testing authentication module imports"
        )
        
        # Function validation
        auth_functions = [
            "generate_jwt_token",
            "validate_api_key", 
            "is_token_expired",
            "hash_password"
        ]
        
        for func_name in auth_functions:
            self._run_test(
                f"Function exists: {func_name}",
                lambda f=func_name: self._check_auth_function(f),
                f"Checking authentication function {func_name}"
            )
        
        # Token generation test
        self._run_test(
            "JWT token generation",
            lambda: self._test_token_generation(),
            "Testing JWT token creation"
        )
    
    def _validate_monitoring(self):
        """Additional monitoring validation"""
        print("\n📊 MONITORING VALIDATION")
        print("-" * 25)
        
        # Monitoring agent
        self._run_test(
            "Monitoring agent exists",
            lambda: Path("core/monitoring/internal_monitoring_agent.py").exists(),
            "Checking monitoring agent file"
        )
        
        # Metrics directory
        self._run_test(
            "Metrics directory exists",
            lambda: Path("metrics").exists() or self._create_metrics_dir(),
            "Checking/creating metrics directory"
        )
        
        # Telemetry capability
        self._run_test(
            "Telemetry collection capability",
            lambda: self._test_telemetry_capability(),
            "Testing telemetry data collection"
        )
    
    def _run_test(self, name: str, test_func, description: str = ""):
        """Execute individual test"""
        start_time = time.time()
        
        try:
            result = test_func()
            execution_time = time.time() - start_time
            
            test_result = TestResult(
                name=name,
                passed=bool(result),
                message="PASS" if result else "FAIL",
                execution_time=execution_time,
                details={"description": description, "result": str(result)}
            )
            
            self.results.append(test_result)
            
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {name} ({execution_time:.3f}s)")
            
        except Exception as e:
            execution_time = time.time() - start_time
            test_result = TestResult(
                name=name,
                passed=False,
                message=f"ERROR: {str(e)}",
                execution_time=execution_time,
                details={"description": description, "error": str(e)}
            )
            
            self.results.append(test_result)
            print(f"❌ ERROR {name} ({execution_time:.3f}s) - {e}")
    
    def _check_permissions(self, path: str, expected_perm: int) -> bool:
        """Check file/directory permissions"""
        try:
            file_path = Path(path)
            if not file_path.exists():
                return False
            
            stat_info = file_path.stat()
            actual_perm = stat_info.st_mode & 0o777
            return actual_perm == expected_perm
        except Exception:
            return False
    
    def _check_docker_version(self) -> bool:
        """Check Docker version compatibility"""
        try:
            version_info = self.docker_client.version()
            version_str = version_info.get('Version', '')
            # Check if version is reasonable (not empty and numeric)
            return bool(version_str and any(c.isdigit() for c in version_str))
        except Exception:
            return False
    
    def _test_isolated_container(self) -> bool:
        """Test network isolation with isolated container"""
        try:
            # Create isolated container
            container = self.docker_client.containers.run(
                "alpine:latest",
                "sleep 10",
                network_mode="none",
                detach=True,
                name="test_isolation_sprint1"
            )
            
            # Test should fail due to no network
            try:
                container.exec_run("ping -c 1 8.8.8.8", timeout=5)
                success = False  # Should have failed
            except Exception:
                success = True  # Expected failure
            
            # Cleanup
            container.stop()
            container.remove()
            
            return success
            
        except Exception:
            return False
    
    def _test_dns_blocking(self) -> bool:
        """Test DNS resolution blocking"""
        try:
            container = self.docker_client.containers.run(
                "alpine:latest",
                "sleep 10",
                network_mode="none",
                detach=True,
                name="test_dns_block"
            )
            
            # DNS should fail in isolated network
            exit_code, output = container.exec_run("nslookup google.com")
            success = exit_code != 0  # Should fail
            
            container.stop()
            container.remove()
            return success
            
        except Exception:
            return False
    
    def _test_external_connectivity(self) -> bool:
        """Test external connectivity blocking"""
        try:
            container = self.docker_client.containers.run(
                "alpine:latest",
                "sleep 10",
                network_mode="none",
                detach=True,
                name="test_ext_conn"
            )
            
            # External connection should fail
            exit_code, output = container.exec_run("wget -T 5 http://google.com -O /dev/null")
            success = exit_code != 0  # Should fail
            
            container.stop()
            container.remove()
            return success
            
        except Exception:
            return False
    
    def _test_auth_imports(self) -> bool:
        """Test authentication module imports"""
        try:
            from core.security.authentication_layer import AuthenticationLayer
            return True
        except ImportError:
            return False
        except Exception:
            return False
    
    def _check_auth_function(self, func_name: str) -> bool:
        """Check if authentication function exists"""
        try:
            from core.security.authentication_layer import AuthenticationLayer
            auth = AuthenticationLayer()
            return hasattr(auth, func_name)
        except Exception:
            return False
    
    def _test_token_generation(self) -> bool:
        """Test JWT token generation"""
        try:
            from core.security.authentication_layer import AuthenticationLayer, User
            auth = AuthenticationLayer()
            user = User(user_id="test_user", username="tester", role="admin")
            token = auth.generate_jwt_token(user)
            return bool(token and isinstance(token, str))
        except Exception:
            return False
    
    def _create_metrics_dir(self) -> bool:
        """Create metrics directory if it doesn't exist"""
        try:
            Path("metrics").mkdir(exist_ok=True)
            return True
        except Exception:
            return False
    
    def _test_telemetry_capability(self) -> bool:
        """Test telemetry collection capability"""
        try:
            from core.monitoring.internal_monitoring_agent import MonitoringAgent
            agent = MonitoringAgent()
            return hasattr(agent, 'start_session') and hasattr(agent, 'start_step')
        except Exception:
            return False
    
    def _generate_report(self) -> TestSuiteReport:
        """Generate comprehensive test report"""
        total_time = time.time() - self.start_time
        passed_count = sum(1 for r in self.results if r.passed)
        failed_count = len(self.results) - passed_count
        success_rate = (passed_count / len(self.results) * 100) if self.results else 0
        
        report = TestSuiteReport(
            timestamp=datetime.now().isoformat(),
            total_tests=len(self.results),
            passed_tests=passed_count,
            failed_tests=failed_count,
            success_rate=success_rate,
            test_results=self.results,
            environment_info={
                "platform": sys.platform,
                "python_version": sys.version,
                "validation_duration": f"{total_time:.2f} seconds"
            }
        )
        
        return report

def main():
    """Main validation execution"""
    validator = EnvironmentValidator()
    report = validator.run_comprehensive_validation()
    
    # Display summary
    print(f"\n{'='*55}")
    print("📊 SPRINT 1 VALIDATION SUMMARY")
    print(f"{'='*55}")
    print(f"Total Tests: {report.total_tests}")
    print(f"✅ Passed: {report.passed_tests}")
    print(f"❌ Failed: {report.failed_tests}")
    print(f"📈 Success Rate: {report.success_rate:.1f}%")
    print(f"⏱️  Total Time: {report.environment_info['validation_duration']}")
    
    # Overall result
    if report.failed_tests == 0:
        print(f"\n🎉 SPRINT 1 COMPLETED SUCCESSFULLY!")
        print("✅ All infrastructure validations passed")
        print("✅ Environment is stable and ready for production")
        return True
    else:
        print(f"\n💥 SPRINT 1 FAILED - {report.failed_tests} tests failed")
        print("❌ Please address the failed tests before proceeding")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)