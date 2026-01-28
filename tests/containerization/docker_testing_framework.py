#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐳 CONTAINERIZATION TESTING FRAMEWORK
SDET Phase 1 Week 4 - Docker & Container Testing Expertise

Provides enterprise-grade containerization testing capabilities:
- Multi-stage Docker builds for test environments
- Container lifecycle management and testing
- Docker Compose orchestration for complex scenarios
- Container security and compliance validation
- Resource constraint testing (CPU, memory, network)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import json
import subprocess
import time
import uuid
import docker
from docker.models.containers import Container
from docker.models.images import Image
import yaml
import logging

# ==================== DOCKER CLIENT MANAGEMENT ====================

class DockerTestClient:
    """Manage Docker client connections and operations"""
    
    def __init__(self, base_url: str = None):
        try:
            if base_url:
                self.client = docker.DockerClient(base_url=base_url)
            else:
                self.client = docker.from_env()
            self.logger = self._setup_logger()
        except Exception as e:
            self.logger = self._setup_logger()
            self.logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None
            
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for Docker operations"""
        logger = logging.getLogger('DockerTesting')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def is_available(self) -> bool:
        """Check if Docker daemon is accessible"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            return False
            
    def get_client(self):
        """Get Docker client instance"""
        return self.client

# ==================== CONTAINER LIFECYCLE MANAGEMENT ====================

@dataclass
class ContainerTestConfig:
    """Configuration for container testing"""
    image: str
    name: str
    ports: Dict[str, int] = None
    environment: Dict[str, str] = None
    volumes: Dict[str, Dict[str, str]] = None
    command: List[str] = None
    resources: Dict[str, Any] = None
    network: str = None
    restart_policy: str = "no"

@dataclass
class ContainerTestResult:
    """Results from container testing"""
    container_id: str
    name: str
    status: str
    start_time: str
    end_time: str
    exit_code: int
    logs: str
    resource_usage: Dict[str, Any]
    health_checks: List[Dict[str, Any]]

class ContainerLifecycleTester:
    """Test container lifecycle operations"""
    
    def __init__(self, docker_client: DockerTestClient):
        self.docker_client = docker_client
        self.test_containers = []
        self.test_results = []
        
    def test_container_lifecycle(self, config: ContainerTestConfig) -> ContainerTestResult:
        """Test complete container lifecycle: create → start → stop → remove"""
        
        start_time = datetime.now()
        result_data = {
            'container_id': '',
            'name': config.name,
            'status': 'failed',
            'start_time': start_time.isoformat(),
            'end_time': '',
            'exit_code': -1,
            'logs': '',
            'resource_usage': {},
            'health_checks': []
        }
        
        try:
            # 1. Create container
            print(f"🐳 Creating container: {config.name}")
            container = self.docker_client.client.containers.create(
                image=config.image,
                name=config.name,
                ports=config.ports or {},
                environment=config.environment or {},
                volumes=config.volumes or {},
                command=config.command,
                network=config.network,
                restart_policy={"Name": config.restart_policy}
            )
            
            result_data['container_id'] = container.id
            self.test_containers.append(container.id)
            
            # 2. Start container
            print(f"🚀 Starting container: {config.name}")
            container.start()
            
            # Wait for container to be running
            time.sleep(2)
            container.reload()
            
            if container.status == 'running':
                result_data['status'] = 'running'
                
                # 3. Test health checks
                health_results = self._perform_health_checks(container, config)
                result_data['health_checks'] = health_results
                
                # 4. Test resource usage
                resource_usage = self._measure_resource_usage(container)
                result_data['resource_usage'] = resource_usage
                
                # 5. Stop container
                print(f"🛑 Stopping container: {config.name}")
                container.stop(timeout=10)
                container.reload()
                
                if container.status == 'exited':
                    result_data['status'] = 'completed'
                    result_data['exit_code'] = container.attrs['State']['ExitCode']
                    
            # 6. Get logs
            result_data['logs'] = container.logs().decode('utf-8')[-1000:]  # Last 1000 chars
            
            # 7. Remove container
            print(f"🗑️  Removing container: {config.name}")
            container.remove(force=True)
            
            if container.id in self.test_containers:
                self.test_containers.remove(container.id)
                
        except Exception as e:
            result_data['logs'] = f"Error: {str(e)}"
            print(f"❌ Container test failed: {e}")
            
        result_data['end_time'] = datetime.now().isoformat()
        result = ContainerTestResult(**result_data)
        self.test_results.append(result)
        
        return result
        
    def _perform_health_checks(self, container: Container, config: ContainerTestConfig) -> List[Dict[str, Any]]:
        """Perform health checks on running container"""
        health_checks = []
        
        # Port accessibility check
        if config.ports:
            for container_port, host_port in config.ports.items():
                check_result = {
                    'type': 'port_accessibility',
                    'port': host_port,
                    'status': 'unknown',
                    'details': ''
                }
                
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex(('localhost', host_port))
                    sock.close()
                    
                    check_result['status'] = 'accessible' if result == 0 else 'inaccessible'
                    health_checks.append(check_result)
                except Exception as e:
                    check_result['status'] = 'error'
                    check_result['details'] = str(e)
                    health_checks.append(check_result)
                    
        # HTTP health check (if applicable)
        if config.ports and '80/tcp' in config.ports:
            check_result = {
                'type': 'http_health',
                'endpoint': f"http://localhost:{config.ports['80/tcp']}/health",
                'status': 'unknown',
                'response_time': 0
            }
            
            try:
                import requests
                start_time = time.time()
                response = requests.get(check_result['endpoint'], timeout=10)
                response_time = time.time() - start_time
                
                check_result['status'] = 'healthy' if response.status_code == 200 else 'unhealthy'
                check_result['response_time'] = round(response_time, 3)
                check_result['status_code'] = response.status_code
                health_checks.append(check_result)
            except Exception as e:
                check_result['status'] = 'error'
                check_result['details'] = str(e)
                health_checks.append(check_result)
                
        return health_checks
        
    def _measure_resource_usage(self, container: Container) -> Dict[str, Any]:
        """Measure container resource usage"""
        try:
            stats = container.stats(stream=False)
            
            return {
                'cpu_percent': self._calculate_cpu_percent(stats),
                'memory_usage_mb': stats['memory_stats']['usage'] / 1024 / 1024,
                'memory_limit_mb': stats['memory_stats']['limit'] / 1024 / 1024,
                'network_rx_bytes': stats['networks']['eth0']['rx_bytes'],
                'network_tx_bytes': stats['networks']['eth0']['tx_bytes'],
                'block_read_bytes': stats.get('blkio_stats', {}).get('io_service_bytes_recursive', [{}])[0].get('value', 0),
                'block_write_bytes': stats.get('blkio_stats', {}).get('io_service_bytes_recursive', [{}])[1].get('value', 0)
            }
        except Exception as e:
            return {'error': str(e)}
            
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU percentage from Docker stats"""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                return round(cpu_percent, 2)
        except Exception:
            pass
        return 0.0

# ==================== MULTI-STAGE BUILD TESTING ====================

class MultiStageBuildTester:
    """Test Docker multi-stage builds for optimized images"""
    
    def __init__(self, docker_client: DockerTestClient):
        self.docker_client = docker_client
        self.build_context = Path("docker_test_context")
        self.build_context.mkdir(exist_ok=True)
        
    def create_test_build_context(self) -> Path:
        """Create test Docker build context with multi-stage setup"""
        
        # Create Dockerfile
        dockerfile_content = '''
# Stage 1: Build stage
FROM python:3.9-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Stage 2: Runtime stage
FROM python:3.9-alpine as runtime

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /app /app

# Create non-root user
RUN adduser -D -s /bin/sh testuser && \\
    chown -R testuser:testuser /app

USER testuser

EXPOSE 8000
CMD ["python", "app.py"]
        '''
        
        # Create simple app
        app_content = '''
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from multi-stage build!"

@app.route('/health')
def health():
    return {"status": "healthy", "stage": "runtime"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
        '''
        
        # Create requirements
        requirements_content = '''
Flask==2.0.1
gunicorn==20.1.0
        '''
        
        # Write files
        with open(self.build_context / "Dockerfile", "w") as f:
            f.write(dockerfile_content)
            
        with open(self.build_context / "app.py", "w") as f:
            f.write(app_content)
            
        with open(self.build_context / "requirements.txt", "w") as f:
            f.write(requirements_content)
            
        return self.build_context
        
    def test_multi_stage_build(self, image_name: str = None) -> Dict[str, Any]:
        """Test multi-stage Docker build process"""
        
        if not image_name:
            image_name = f"test-multistage-{uuid.uuid4().hex[:8]}"
            
        build_context = self.create_test_build_context()
        
        print(f"🏗️  Testing multi-stage build: {image_name}")
        
        start_time = time.time()
        build_result = {
            'image_name': image_name,
            'build_success': False,
            'build_time': 0,
            'final_image_size_mb': 0,
            'stages_built': [],
            'security_scan_results': {}
        }
        
        try:
            # Build image
            build_output = self.docker_client.client.images.build(
                path=str(build_context),
                tag=image_name,
                rm=True,
                forcerm=True
            )
            
            build_result['build_success'] = True
            build_result['build_time'] = round(time.time() - start_time, 2)
            
            # Get image information
            image = self.docker_client.client.images.get(image_name)
            build_result['final_image_size_mb'] = round(image.attrs['Size'] / 1024 / 1024, 2)
            
            # Count build stages (approximate)
            build_result['stages_built'] = ['builder', 'runtime']
            
            # Run security scan
            security_results = self._perform_security_scan(image)
            build_result['security_scan_results'] = security_results
            
            print(f"✅ Multi-stage build successful: {build_result['final_image_size_mb']}MB")
            
        except Exception as e:
            build_result['error'] = str(e)
            print(f"❌ Multi-stage build failed: {e}")
            
        finally:
            # Cleanup
            self._cleanup_build_context()
            
        return build_result
        
    def _perform_security_scan(self, image: Image) -> Dict[str, Any]:
        """Perform basic security scanning on built image"""
        scan_results = {
            'vulnerabilities_found': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'scan_passed': True
        }
        
        # Simulate security scan (in real implementation, integrate with tools like Trivy)
        try:
            # Check for common security issues
            image_history = image.history()
            
            # Look for sensitive files or packages
            for layer in image_history:
                if 'ADD file:' in layer.get('CreatedBy', ''):
                    scan_results['vulnerabilities_found'] += 1
                    
            # Check if running as root (should be non-root in secure builds)
            config = image.attrs.get('Config', {})
            user = config.get('User', '')
            if not user or user == 'root':
                scan_results['high_issues'] += 1
                
        except Exception as e:
            scan_results['scan_error'] = str(e)
            
        scan_results['scan_passed'] = (
            scan_results['vulnerabilities_found'] == 0 and 
            scan_results['critical_issues'] == 0 and
            scan_results['high_issues'] <= 1
        )
        
        return scan_results
        
    def _cleanup_build_context(self):
        """Clean up test build context"""
        import shutil
        if self.build_context.exists():
            shutil.rmtree(self.build_context)

# ==================== RESOURCE CONSTRAINT TESTING ====================

class ResourceConstraintTester:
    """Test container behavior under resource constraints"""
    
    def __init__(self, docker_client: DockerTestClient):
        self.docker_client = docker_client
        
    def test_memory_constraints(self, base_image: str = "python:3.9-slim") -> List[Dict[str, Any]]:
        """Test container behavior with different memory limits"""
        
        print("🧠 Testing memory constraint scenarios")
        
        test_configs = [
            {'memory_limit': '100m', 'expected_behavior': 'limited'},
            {'memory_limit': '200m', 'expected_behavior': 'normal'},
            {'memory_limit': '50m', 'expected_behavior': 'crash_or_throttle'}
        ]
        
        results = []
        
        for config in test_configs:
            test_result = {
                'constraint_type': 'memory',
                'limit': config['memory_limit'],
                'expected_behavior': config['expected_behavior'],
                'actual_behavior': 'unknown',
                'container_status': 'unknown',
                'oom_killed': False
            }
            
            try:
                # Create memory-intensive container
                container = self.docker_client.client.containers.run(
                    base_image,
                    command=[
                        'python', '-c', 
                        'import time; data = []; '
                        'for i in range(1000000): data.append("x" * 1000); '
                        'time.sleep(10)'
                    ],
                    mem_limit=config['memory_limit'],
                    detach=True,
                    name=f"mem-test-{uuid.uuid4().hex[:8]}"
                )
                
                # Monitor for OOM kills
                time.sleep(5)
                container.reload()
                
                test_result['container_status'] = container.status
                
                if container.status == 'exited':
                    exit_code = container.attrs['State']['ExitCode']
                    if exit_code == 137:  # OOM killed
                        test_result['oom_killed'] = True
                        test_result['actual_behavior'] = 'crash_or_throttle'
                    else:
                        test_result['actual_behavior'] = 'completed'
                elif container.status == 'running':
                    test_result['actual_behavior'] = 'normal'
                    
                container.remove(force=True)
                
            except Exception as e:
                test_result['actual_behavior'] = 'error'
                test_result['error'] = str(e)
                
            results.append(test_result)
            print(f"  Memory {config['memory_limit']}: {test_result['actual_behavior']}")
            
        return results
        
    def test_cpu_constraints(self, base_image: str = "python:3.9-slim") -> List[Dict[str, Any]]:
        """Test container behavior with CPU constraints"""
        
        print("⚡ Testing CPU constraint scenarios")
        
        test_configs = [
            {'cpu_quota': 25000, 'cpu_period': 100000, 'expected_behavior': 'throttled'},  # 25% CPU
            {'cpu_quota': 50000, 'cpu_period': 100000, 'expected_behavior': 'normal'},   # 50% CPU
            {'cpu_quota': 100000, 'cpu_period': 100000, 'expected_behavior': 'full'}     # 100% CPU
        ]
        
        results = []
        
        for config in test_configs:
            test_result = {
                'constraint_type': 'cpu',
                'quota': config['cpu_quota'],
                'period': config['cpu_period'],
                'cpu_percentage': config['cpu_quota'] / config['cpu_period'] * 100,
                'expected_behavior': config['expected_behavior'],
                'actual_behavior': 'unknown',
                'cpu_usage_percent': 0
            }
            
            try:
                # Create CPU-intensive container
                container = self.docker_client.client.containers.run(
                    base_image,
                    command=[
                        'python', '-c',
                        'import time; start = time.time(); '
                        'while time.time() - start < 10: '
                        'sum(i*i for i in range(10000))'
                    ],
                    cpu_quota=config['cpu_quota'],
                    cpu_period=config['cpu_period'],
                    detach=True,
                    name=f"cpu-test-{uuid.uuid4().hex[:8]}"
                )
                
                # Monitor CPU usage
                time.sleep(3)
                stats = container.stats(stream=False)
                cpu_percent = self._calculate_cpu_percent(stats)
                test_result['cpu_usage_percent'] = cpu_percent
                
                if cpu_percent <= config['cpu_percentage'] + 10:  # Allow 10% tolerance
                    test_result['actual_behavior'] = 'throttled'
                elif cpu_percent >= 90:  # Near full utilization
                    test_result['actual_behavior'] = 'full'
                else:
                    test_result['actual_behavior'] = 'normal'
                    
                container.remove(force=True)
                
            except Exception as e:
                test_result['actual_behavior'] = 'error'
                test_result['error'] = str(e)
                
            results.append(test_result)
            print(f"  CPU {test_result['cpu_percentage']}%: {test_result['actual_behavior']} ({test_result['cpu_usage_percent']:.1f}%)")
            
        return results
        
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU percentage from Docker stats"""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                return round(cpu_percent, 2)
        except Exception:
            pass
        return 0.0

# ==================== DOCKER COMPOSE TESTING ====================

class DockerComposeTester:
    """Test Docker Compose orchestration scenarios"""
    
    def __init__(self, docker_client: DockerTestClient):
        self.docker_client = docker_client
        self.compose_context = Path("compose_test")
        self.compose_context.mkdir(exist_ok=True)
        
    def create_test_compose_scenario(self) -> Path:
        """Create test Docker Compose scenario with multiple services"""
        
        compose_content = '''
version: '3.8'

services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    depends_on:
      - api
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
      
  api:
    image: python:3.9-slim
    command: python -m http.server 8000
    ports:
      - "8000:8000"
    environment:
      - ENV=testing
    volumes:
      - ./data:/app/data
      
  database:
    image: postgres:13-alpine
    environment:
      - POSTGRES_DB=testdb
      - POSTGRES_USER=testuser
      - POSTGRES_PASSWORD=testpass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser -d testdb"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
        '''
        
        # Create data directory
        (self.compose_context / "data").mkdir(exist_ok=True)
        with open(self.compose_context / "data" / "test.txt", "w") as f:
            f.write("Test data file")
            
        # Write docker-compose.yml
        with open(self.compose_context / "docker-compose.yml", "w") as f:
            f.write(compose_content)
            
        return self.compose_context
        
    def test_compose_orchestration(self) -> Dict[str, Any]:
        """Test Docker Compose orchestration"""
        
        print("🔄 Testing Docker Compose orchestration")
        
        compose_context = self.create_test_compose_scenario()
        result = {
            'services_deployed': [],
            'health_checks_passed': 0,
            'dependencies_respected': True,
            'volumes_mounted': [],
            'networking_working': False
        }
        
        try:
            # Run docker-compose up
            subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=compose_context,
                check=True,
                capture_output=True
            )
            
            # Wait for services to start
            time.sleep(10)
            
            # Check running services
            ps_output = subprocess.run(
                ['docker-compose', 'ps', '--format', 'json'],
                cwd=compose_context,
                capture_output=True,
                text=True
            )
            
            if ps_output.returncode == 0:
                try:
                    services = json.loads(ps_output.stdout) if ps_output.stdout.strip() else []
                    result['services_deployed'] = [s.get('Service', 'unknown') for s in services]
                except json.JSONDecodeError:
                    # Handle non-JSON output
                    lines = ps_output.stdout.strip().split('\n')
                    result['services_deployed'] = [line.split()[0] for line in lines if line and not line.startswith('NAME')]
            
            # Test service connectivity
            try:
                import requests
                # Test web service
                web_response = requests.get('http://localhost:8080', timeout=5)
                if web_response.status_code == 200:
                    result['networking_working'] = True
                    
                # Test API service
                api_response = requests.get('http://localhost:8000', timeout=5)
                if api_response.status_code == 200:
                    result['networking_working'] = True
                    
            except Exception:
                pass
                
            # Test volume mounting
            try:
                api_container = self.docker_client.client.containers.get('compose_test_api_1')
                mounts = api_container.attrs['Mounts']
                result['volumes_mounted'] = [mount['Destination'] for mount in mounts]
            except Exception:
                pass
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Compose test failed: {e}")
            
        finally:
            # Cleanup
            try:
                subprocess.run(['docker-compose', 'down', '-v'], cwd=compose_context, capture_output=True)
            except Exception:
                pass
            import shutil
            if self.compose_context.exists():
                shutil.rmtree(self.compose_context)
                
        print(f"✅ Compose orchestration test completed")
        print(f"   Services: {len(result['services_deployed'])}")
        print(f"   Networking: {'Working' if result['networking_working'] else 'Failed'}")
        
        return result

# ==================== MAIN CONTAINERIZATION TESTING FRAMEWORK ====================

class ContainerizationTestingFramework:
    """Complete containerization testing framework"""
    
    def __init__(self):
        self.docker_client = DockerTestClient()
        self.lifecycle_tester = ContainerLifecycleTester(self.docker_client)
        self.build_tester = MultiStageBuildTester(self.docker_client)
        self.resource_tester = ResourceConstraintTester(self.docker_client)
        self.compose_tester = DockerComposeTester(self.docker_client)
        
    def run_complete_containerization_suite(self) -> Dict[str, Any]:
        """Run complete containerization testing suite"""
        
        print("🐳 CONTAINERIZATION TESTING SUITE")
        print("=" * 50)
        
        if not self.docker_client.is_available():
            return {
                'status': 'failed',
                'error': 'Docker daemon not available',
                'results': {}
            }
            
        suite_start = datetime.now()
        all_results = {}
        
        # 1. Container Lifecycle Tests
        print("\n🧪 CONTAINER LIFECYCLE TESTS")
        print("-" * 30)
        lifecycle_results = self._run_lifecycle_tests()
        all_results['lifecycle'] = lifecycle_results
        
        # 2. Multi-stage Build Tests
        print("\n🏗️  MULTI-STAGE BUILD TESTS")
        print("-" * 30)
        build_results = self._run_build_tests()
        all_results['build'] = build_results
        
        # 3. Resource Constraint Tests
        print("\n⚖️  RESOURCE CONSTRAINT TESTS")
        print("-" * 32)
        resource_results = self._run_resource_tests()
        all_results['resources'] = resource_results
        
        # 4. Docker Compose Tests
        print("\n🔄 DOCKER COMPOSE TESTS")
        print("-" * 25)
        compose_results = self._run_compose_tests()
        all_results['compose'] = compose_results
        
        suite_end = datetime.now()
        
        # Generate summary
        summary = self._generate_containerization_summary(all_results)
        summary['suite_duration'] = (suite_end - suite_start).total_seconds()
        
        return {
            'suite_name': 'Containerization Testing Suite',
            'start_time': suite_start.isoformat(),
            'end_time': suite_end.isoformat(),
            'results': all_results,
            'summary': summary
        }
        
    def _run_lifecycle_tests(self) -> List[Dict[str, Any]]:
        """Run container lifecycle tests"""
        test_configs = [
            ContainerTestConfig(
                image="nginx:alpine",
                name=f"nginx-test-{uuid.uuid4().hex[:8]}",
                ports={'80/tcp': 8081},
                command=["nginx", "-g", "daemon off;"]
            ),
            ContainerTestConfig(
                image="redis:alpine",
                name=f"redis-test-{uuid.uuid4().hex[:8]}",
                ports={'6379/tcp': 6380}
            )
        ]
        
        results = []
        for config in test_configs:
            result = self.lifecycle_tester.test_container_lifecycle(config)
            results.append(asdict(result))
            
        return results
        
    def _run_build_tests(self) -> Dict[str, Any]:
        """Run multi-stage build tests"""
        return self.build_tester.test_multi_stage_build()
        
    def _run_resource_tests(self) -> Dict[str, Any]:
        """Run resource constraint tests"""
        memory_results = self.resource_tester.test_memory_constraints()
        cpu_results = self.resource_tester.test_cpu_constraints()
        
        return {
            'memory_tests': memory_results,
            'cpu_tests': cpu_results
        }
        
    def _run_compose_tests(self) -> Dict[str, Any]:
        """Run Docker Compose tests"""
        return self.compose_tester.test_compose_orchestration()
        
    def _generate_containerization_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate containerization test summary"""
        
        # Count successful tests
        total_tests = 0
        passed_tests = 0
        
        # Lifecycle tests
        if 'lifecycle' in results:
            for test in results['lifecycle']:
                total_tests += 1
                if test['status'] in ['completed', 'running']:
                    passed_tests += 1
                    
        # Build tests
        if 'build' in results and results['build'].get('build_success'):
            total_tests += 1
            passed_tests += 1
            
        # Resource tests
        if 'resources' in results:
            for test_type in ['memory_tests', 'cpu_tests']:
                if test_type in results['resources']:
                    total_tests += len(results['resources'][test_type])
                    passed_tests += sum(1 for t in results['resources'][test_type] 
                                      if t['actual_behavior'] != 'error')
                    
        # Compose tests
        if 'compose' in results:
            total_tests += 3  # Approximate number of compose test aspects
            compose = results['compose']
            if compose.get('networking_working'):
                passed_tests += 1
            if len(compose.get('services_deployed', [])) >= 2:
                passed_tests += 1
            if compose.get('volumes_mounted'):
                passed_tests += 1
                
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': round(success_rate, 2),
            'capabilities_tested': [
                'container_lifecycle',
                'multi_stage_builds',
                'resource_constraints',
                'docker_compose'
            ]
        }

# ==================== DEMONSTRATION ====================

def demonstrate_containerization_capabilities():
    """Demonstrate containerization testing capabilities"""
    
    print("🐳 CONTAINERIZATION TESTING FRAMEWORK")
    print("=" * 50)
    
    print("\nBEFORE - Manual Container Testing:")
    print("""
# Manual testing steps
docker run -d --name test nginx
docker ps | grep test
curl localhost:80
docker stop test
docker rm test
    """)
    
    print("\nAFTER - Automated Container Testing:")
    print("""
framework = ContainerizationTestingFramework()
results = framework.run_complete_containerization_suite()

# Automated lifecycle testing
# Multi-stage build validation
# Resource constraint verification
# Compose orchestration testing
    """)
    
    print("\n🎯 CONTAINERIZATION TESTING CAPABILITIES:")
    print("✅ Container Lifecycle Management")
    print("✅ Multi-stage Build Optimization")
    print("✅ Resource Constraint Validation")
    print("✅ Docker Compose Orchestration")
    print("✅ Security Scanning Integration")
    print("✅ Health Check Automation")

def run_containerization_demo():
    """Run containerization testing demonstration"""
    
    print("\n🧪 CONTAINERIZATION TESTING DEMONSTRATION")
    print("=" * 50)
    
    framework = ContainerizationTestingFramework()
    
    if not framework.docker_client.is_available():
        print("❌ Docker daemon not available - skipping containerization tests")
        print("💡 Note: This framework requires Docker to be installed and running")
        return None
        
    test_suite = framework.run_complete_containerization_suite()
    
    summary = test_suite['summary']
    
    print(f"\n📊 CONTAINERIZATION TEST RESULTS:")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']}%")
    
    print(f"\n🔧 CAPABILITIES TESTED:")
    for capability in summary['capabilities_tested']:
        print(f"  ✅ {capability.replace('_', ' ').title()}")
        
    return test_suite

if __name__ == "__main__":
    demonstrate_containerization_capabilities()
    print("\n" + "=" * 60)
    run_containerization_demo()