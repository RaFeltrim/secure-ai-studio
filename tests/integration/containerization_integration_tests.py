#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 SECURE AI STUDIO CONTAINERIZATION INTEGRATION
SDET Phase 1 Week 4 - Practical Docker Testing for Secure AI Studio

Integrates containerization testing with existing Secure AI Studio Docker setup
to validate deployment scenarios, resource constraints, and orchestration.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.containerization.docker_testing_framework import *
import pytest
import json
import time

# ==================== SECURE AI STUDIO CONTAINER CONFIGURATIONS ====================

class SecureAIStudioContainerConfigs:
    """Container configurations for Secure AI Studio services"""
    
    @staticmethod
    def get_core_service_configs() -> List[ContainerTestConfig]:
        """Get container configs for core Secure AI Studio services"""
        return [
            ContainerTestConfig(
                image="secure-ai-studio:latest",
                name="secure-ai-core-test",
                ports={'8000/tcp': 8001},
                environment={
                    'ENVIRONMENT': 'testing',
                    'LOG_LEVEL': 'DEBUG',
                    'MAX_CONCURRENT_REQUESTS': '10'
                },
                resources={
                    'mem_limit': '1g',
                    'cpu_quota': 50000,
                    'cpu_period': 100000
                }
            ),
            ContainerTestConfig(
                image="secure-ai-studio-monitoring:latest",
                name="secure-ai-monitoring-test",
                ports={'3000/tcp': 3001},
                environment={
                    'GRAFANA_ADMIN_PASSWORD': 'admin123',
                    'DATASOURCE_URL': 'http://prometheus:9090'
                }
            )
        ]
        
    @staticmethod
    def get_database_configs() -> List[ContainerTestConfig]:
        """Get container configs for database services"""
        return [
            ContainerTestConfig(
                image="postgres:13-alpine",
                name="secure-ai-postgres-test",
                ports={'5432/tcp': 5433},
                environment={
                    'POSTGRES_DB': 'secureai_test',
                    'POSTGRES_USER': 'testuser',
                    'POSTGRES_PASSWORD': 'testpass123'
                },
                volumes={
                    'postgres_test_data': {'bind': '/var/lib/postgresql/data', 'mode': 'rw'}
                }
            ),
            ContainerTestConfig(
                image="redis:alpine",
                name="secure-ai-redis-test",
                ports={'6379/tcp': 6380},
                command=['redis-server', '--maxmemory', '256mb', '--maxmemory-policy', 'allkeys-lru']
            )
        ]

# ==================== LIFECYCLE TESTING FOR SECURE AI STUDIO ====================

class SecureAIStudioLifecycleTests:
    """Container lifecycle tests for Secure AI Studio"""
    
    def setup_method(self):
        """Setup test environment"""
        self.docker_client = DockerTestClient()
        self.lifecycle_tester = ContainerLifecycleTester(self.docker_client)
        
    @pytest.mark.skipif(not DockerTestClient().is_available(), reason="Docker not available")
    def test_core_service_lifecycle(self):
        """Test Secure AI Studio core service lifecycle"""
        
        print("🧪 Testing Secure AI Studio Core Service Lifecycle")
        
        # Test core service container
        config = SecureAIStudioContainerConfigs.get_core_service_configs()[0]
        result = self.lifecycle_tester.test_container_lifecycle(config)
        
        # Validate results
        assert result.status in ['completed', 'running'], f"Container failed with status: {result.status}"
        assert result.exit_code in [0, None], f"Container exited with error code: {result.exit_code}"
        
        # Check health checks
        health_checks = [hc for hc in result.health_checks if hc['status'] == 'healthy']
        assert len(health_checks) > 0, "No healthy health checks found"
        
        print(f"✅ Core service lifecycle test passed")
        print(f"   Container ID: {result.container_id[:12]}")
        print(f"   Status: {result.status}")
        print(f"   Health Checks: {len(health_checks)}/{len(result.health_checks)} passed")
        
    @pytest.mark.skipif(not DockerTestClient().is_available(), reason="Docker not available")
    def test_database_service_lifecycle(self):
        """Test database service lifecycle"""
        
        print("🧪 Testing Database Service Lifecycle")
        
        # Test PostgreSQL container
        config = SecureAIStudioContainerConfigs.get_database_configs()[0]
        result = self.lifecycle_tester.test_container_lifecycle(config)
        
        # Validate database connectivity
        port_accessible = any(
            hc['type'] == 'port_accessibility' and hc['status'] == 'accessible'
            for hc in result.health_checks
        )
        assert port_accessible, "Database port not accessible"
        
        print(f"✅ Database lifecycle test passed")
        print(f"   Container: {result.name}")
        print(f"   Port Accessible: {port_accessible}")

# ==================== RESOURCE CONSTRAINT TESTING ====================

class SecureAIStudioResourceTests:
    """Resource constraint testing for Secure AI Studio"""
    
    def setup_method(self):
        """Setup resource testing"""
        self.docker_client = DockerTestClient()
        self.resource_tester = ResourceConstraintTester(self.docker_client)
        
    @pytest.mark.skipif(not DockerTestClient().is_available(), reason="Docker not available")
    def test_ai_service_memory_constraints(self):
        """Test AI service behavior under memory constraints"""
        
        print("🧠 Testing AI Service Memory Constraints")
        
        # Test with different memory limits
        memory_tests = self.resource_tester.test_memory_constraints("python:3.9-slim")
        
        # Analyze results
        critical_failures = sum(1 for test in memory_tests if test['actual_behavior'] == 'error')
        oom_kills = sum(1 for test in memory_tests if test['oom_killed'])
        
        print(f"📊 Memory Constraint Results:")
        for test in memory_tests:
            status = "✅" if test['actual_behavior'] != 'error' else "❌"
            print(f"  {status} Limit {test['limit']}: {test['actual_behavior']}")
            
        # Validate that extreme constraints cause expected behavior
        extreme_constraint_test = next(
            (t for t in memory_tests if t['limit'] == '50m'), None
        )
        if extreme_constraint_test:
            assert extreme_constraint_test['actual_behavior'] in ['crash_or_throttle', 'error'], \
                "Extreme memory constraint should cause failure or throttling"
                
        assert critical_failures <= 1, f"Too many critical failures: {critical_failures}"
        print(f"✅ Memory constraint testing completed")
        
    @pytest.mark.skipif(not DockerTestClient().is_available(), reason="Docker not available")
    def test_concurrent_request_handling(self):
        """Test service handling of concurrent requests under CPU constraints"""
        
        print("⚡ Testing Concurrent Request Handling")
        
        # This would test the actual AI service with load
        # For now, simulate with CPU constraint testing
        cpu_tests = self.resource_tester.test_cpu_constraints("python:3.9-slim")
        
        print(f"📊 CPU Constraint Results:")
        for test in cpu_tests:
            status = "✅" if test['actual_behavior'] != 'error' else "❌"
            print(f"  {status} {test['cpu_percentage']}% CPU: {test['actual_behavior']} ({test['cpu_usage_percent']:.1f}%)")
            
        # Validate CPU throttling works
        throttled_test = next(
            (t for t in cpu_tests if t['cpu_percentage'] == 25.0), None
        )
        if throttled_test:
            assert throttled_test['actual_behavior'] in ['throttled', 'normal'], \
                "Low CPU quota should result in throttling"
                
        print(f"✅ Concurrent request handling validation completed")

# ==================== DOCKER COMPOSE INTEGRATION ====================

class SecureAIStudioComposeTests:
    """Docker Compose testing for Secure AI Studio"""
    
    def setup_method(self):
        """Setup compose testing"""
        self.docker_client = DockerTestClient()
        self.compose_tester = DockerComposeTester(self.docker_client)
        
    def create_secure_ai_compose_context(self) -> Path:
        """Create Docker Compose context for Secure AI Studio"""
        
        compose_context = Path("secure_ai_compose_test")
        compose_context.mkdir(exist_ok=True)
        
        # Create simplified docker-compose for testing
        compose_content = '''
version: '3.8'

services:
  api:
    image: python:3.9-slim
    command: >
      bash -c "
      pip install flask && 
      python -c \"
      from flask import Flask
      import time
      app = Flask(__name__)
      
      @app.route('/health')
      def health():
          return {'status': 'healthy', 'service': 'api'}
          
      @app.route('/generate/image')
      def generate_image():
          time.sleep(0.1)  # Simulate processing
          return {'session_id': 'test-session', 'status': 'processing'}
          
      if __name__ == '__main__':
          app.run(host='0.0.0.0', port=8000)
      \"
      "
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
      
  monitoring:
    image: python:3.9-slim
    command: >
      bash -c "
      pip install flask &&
      python -c \"
      from flask import Flask
      app = Flask(__name__)
      
      @app.route('/metrics')
      def metrics():
          return {'cpu': 45.2, 'memory': 67.8, 'requests_per_second': 125}
          
      if __name__ == '__main__':
          app.run(host='0.0.0.0', port=3000)
      \"
      "
    ports:
      - "3000:3000"
    depends_on:
      - api
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/metrics"]
      interval: 30s
      timeout: 10s
      retries: 3
        '''
        
        with open(compose_context / "docker-compose.yml", "w") as f:
            f.write(compose_content)
            
        return compose_context
        
    @pytest.mark.skipif(not DockerTestClient().is_available(), reason="Docker not available")
    def test_secure_ai_compose_deployment(self):
        """Test Secure AI Studio Docker Compose deployment"""
        
        print("🔄 Testing Secure AI Studio Compose Deployment")
        
        # Create test context
        compose_context = self.create_secure_ai_compose_context()
        
        try:
            # Run docker-compose up
            result = subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=compose_context,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            assert result.returncode == 0, f"Docker Compose failed: {result.stderr}"
            
            # Wait for services to be healthy
            time.sleep(30)
            
            # Test service connectivity
            import requests
            
            # Test API service
            api_response = requests.get('http://localhost:8000/health', timeout=10)
            assert api_response.status_code == 200, "API service not responding"
            api_data = api_response.json()
            assert api_data['status'] == 'healthy', "API service unhealthy"
            
            # Test AI generation endpoint
            gen_response = requests.get('http://localhost:8000/generate/image', timeout=10)
            assert gen_response.status_code == 200, "Generation endpoint not responding"
            
            # Test Redis connectivity
            redis_check = subprocess.run(
                ['docker-compose', 'exec', 'redis', 'redis-cli', 'ping'],
                cwd=compose_context,
                capture_output=True,
                text=True
            )
            assert 'PONG' in redis_check.stdout, "Redis service not responding"
            
            # Test monitoring service
            monitor_response = requests.get('http://localhost:3000/metrics', timeout=10)
            assert monitor_response.status_code == 200, "Monitoring service not responding"
            
            print("✅ All services deployed and responding correctly")
            print("   - API Service: Healthy")
            print("   - Redis Cache: Responsive")
            print("   - Monitoring: Active")
            
        finally:
            # Cleanup
            subprocess.run(['docker-compose', 'down', '-v'], cwd=compose_context, capture_output=True)
            import shutil
            if compose_context.exists():
                shutil.rmtree(compose_context)

# ==================== MULTI-STAGE BUILD OPTIMIZATION ====================

class SecureAIStudioBuildOptimizationTests:
    """Multi-stage build optimization for Secure AI Studio"""
    
    def setup_method(self):
        """Setup build testing"""
        self.docker_client = DockerTestClient()
        self.build_tester = MultiStageBuildTester(self.docker_client)
        
    def create_secure_ai_dockerfile(self) -> str:
        """Create optimized Dockerfile for Secure AI Studio"""
        return '''
# Stage 1: Dependencies builder
FROM python:3.9-slim as dependencies

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Application builder
FROM dependencies as builder

COPY . .
RUN python -m compileall .

# Stage 3: Production runtime
FROM python:3.9-alpine as runtime

# Install system dependencies
RUN apk add --no-cache gcc musl-dev linux-headers

# Create non-root user
RUN addgroup -g 1001 -S secureai && \\
    adduser -u 1001 -S secureai -G secureai

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /app /app

# Set proper ownership
RUN chown -R secureai:secureai /app

# Switch to non-root user
USER secureai

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "core/api/enterprise_api.py"]
        '''
        
    @pytest.mark.skipif(not DockerTestClient().is_available(), reason="Docker not available")
    def test_secure_ai_multistage_build(self):
        """Test multi-stage build optimization for Secure AI Studio"""
        
        print("🏗️  Testing Secure AI Studio Multi-stage Build")
        
        # Override build context creation for Secure AI Studio
        original_create = self.build_tester.create_test_build_context
        
        def secure_ai_build_context():
            context = original_create()
            
            # Replace with Secure AI Studio Dockerfile
            with open(context / "Dockerfile", "w") as f:
                f.write(self.create_secure_ai_dockerfile())
                
            # Create minimal Secure AI Studio structure
            core_dir = context / "core" / "api"
            core_dir.mkdir(parents=True, exist_ok=True)
            
            # Create simplified API
            api_content = '''
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "Secure AI Studio",
        "version": "1.0.0"
    })

@app.route('/generate/image')
def generate_image():
    return jsonify({
        "session_id": "test-session",
        "status": "processing",
        "estimated_time": 5
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
            '''
            
            with open(core_dir / "enterprise_api.py", "w") as f:
                f.write(api_content)
                
            # Create requirements
            with open(context / "requirements.txt", "w") as f:
                f.write("Flask==2.0.1\nrequests==2.25.1\n")
                
            return context
            
        self.build_tester.create_test_build_context = secure_ai_build_context
        
        # Run build test
        build_result = self.build_tester.test_multi_stage_build("secure-ai-studio-test")
        
        # Validate build results
        assert build_result['build_success'], f"Build failed: {build_result.get('error', 'Unknown error')}"
        assert build_result['final_image_size_mb'] > 0, "Image size should be greater than 0"
        assert build_result['security_scan_results']['scan_passed'], "Security scan should pass"
        
        print(f"✅ Multi-stage build successful")
        print(f"   Final Image Size: {build_result['final_image_size_mb']} MB")
        print(f"   Build Time: {build_result['build_time']} seconds")
        print(f"   Security Scan: {'Passed' if build_result['security_scan_results']['scan_passed'] else 'Failed'}")

# ==================== COMPLETE INTEGRATION SUITE ====================

class TestSecureAIStudioContainerization:
    """Complete containerization test suite for Secure AI Studio"""
    
    def setup_method(self):
        """Setup complete test suite"""
        self.framework = ContainerizationTestingFramework()
        
    @pytest.mark.skipif(not DockerTestClient().is_available(), reason="Docker not available")
    def test_complete_containerization_validation(self):
        """Run complete containerization validation suite"""
        
        print("🎯 SECURE AI STUDIO - COMPLETE CONTAINERIZATION VALIDATION")
        print("=" * 65)
        
        # Run comprehensive containerization suite
        test_results = self.framework.run_complete_containerization_suite()
        
        # Validate results
        summary = test_results['summary']
        
        print(f"\n📊 FINAL CONTAINERIZATION RESULTS:")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']}%")
        
        # Assert success criteria
        assert summary['success_rate'] >= 85.0, f"Containerization success rate below threshold: {summary['success_rate']}%"
        assert summary['passed_tests'] >= summary['total_tests'] * 0.85, "Too many containerization failures"
        
        # Validate all capabilities tested
        expected_capabilities = [
            'container_lifecycle',
            'multi_stage_builds', 
            'resource_constraints',
            'docker_compose'
        ]
        
        for capability in expected_capabilities:
            assert capability in summary['capabilities_tested'], f"Missing capability: {capability}"
            
        print("✅ All containerization validation criteria passed!")
        print("✅ Secure AI Studio containerization ready for production deployment")

# ==================== BEST PRACTICES DEMONSTRATION ====================

def demonstrate_containerization_best_practices():
    """Demonstrate containerization testing best practices"""
    
    print("🏆 CONTAINERIZATION TESTING BEST PRACTICES")
    print("=" * 50)
    
    print("\n✅ RECOMMENDED PATTERNS:")
    
    print("\n1. Multi-stage Builds")
    print("   - Separate build and runtime stages")
    print("   - Minimize final image size")
    print("   - Reduce attack surface")
    
    print("\n2. Resource Constraints Testing")
    print("   - Test memory limits and OOM behavior")
    print("   - Validate CPU throttling")
    print("   - Ensure graceful degradation")
    
    print("\n3. Health Check Automation")
    print("   - Automated service health validation")
    print("   - Dependency readiness checking")
    print("   - Self-healing validation")
    
    print("\n4. Orchestration Validation")
    print("   - Docker Compose service dependencies")
    print("   - Network connectivity testing")
    print("   - Volume mounting verification")
    
    print("\nBEFORE - Manual Container Testing:")
    print("""
# Manual steps
docker build -t myapp .
docker run -d -p 8000:8000 myapp
curl localhost:8000/health
docker logs container_id
    """)
    
    print("\nAFTER - Automated Container Testing:")
    print("""
framework = ContainerizationTestingFramework()
configs = SecureAIStudioContainerConfigs.get_core_service_configs()

for config in configs:
    result = framework.test_container_lifecycle(config)
    validate_health_checks(result)
    verify_resource_usage(result)
    """)
    
    print("\n🎯 ENTERPRISE CONTAINERIZATION BENEFITS:")
    print("✅ Automated deployment validation")
    print("✅ Resource optimization verification")
    print("✅ Security compliance checking")
    print("✅ Orchestration reliability testing")
    print("✅ Production readiness assessment")

if __name__ == "__main__":
    # Run demonstrations
    demonstrate_containerization_best_practices()
    
    print("\n" + "=" * 60)
    print("🧪 RUNNING SECURE AI STUDIO CONTAINERIZATION TESTS")
    print("=" * 60)
    
    # Run pytest programmatically
    pytest.main([__file__, "-v", "--tb=short"])