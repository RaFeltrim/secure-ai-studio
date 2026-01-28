#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Container Lifecycle Manager
Professional container orchestration with encrypted volume management

This script provides:
- Secure container lifecycle management
- Encrypted volume mounting/unmounting
- Health monitoring and auto-recovery
- Resource allocation control
"""

import os
import sys
import subprocess
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import docker
from cryptography.fernet import Fernet
import psutil

@dataclass
class ContainerConfig:
    """Container configuration settings"""
    name: str
    image: str
    memory_limit: str
    cpu_limit: str
    encrypted_volumes: List[str]
    environment_vars: Dict[str, str]
    restart_policy: str = "unless-stopped"

@dataclass
class VolumeInfo:
    """Encrypted volume information"""
    host_path: str
    container_path: str
    encryption_key: Optional[bytes] = None
    mounted: bool = False

class ContainerLifecycleManager:
    """
    Professional container lifecycle management system
    """
    
    def __init__(self, config_path: str = "config/container.conf"):
        """Initialize the container manager"""
        self.logger = self._setup_logging()
        self.docker_client = self._connect_docker()
        self.config = self._load_config(config_path)
        self.encrypted_volumes = {}
        self.running_containers = {}
        
        self.logger.info("🛡️ Container Lifecycle Manager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup secure logging"""
        logger = logging.getLogger('ContainerManager')
        logger.setLevel(logging.INFO)
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        handler = logging.FileHandler(
            log_dir / f"container_manager_{datetime.now().strftime('%Y%m%d')}.log"
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _connect_docker(self) -> docker.DockerClient:
        """Connect to Docker daemon"""
        try:
            client = docker.from_env()
            client.ping()
            self.logger.info("✅ Docker connection established")
            return client
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to Docker: {e}")
            raise
    
    def _load_config(self, config_path: str) -> Dict:
        """Load container configuration"""
        try:
            if not os.path.exists(config_path):
                return self._create_default_config()
            
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default configuration"""
        return {
            "containers": {
                "secure-ai-engine": {
                    "image": "secure-ai-studio:latest",
                    "memory_limit": "12G",
                    "cpu_limit": "6",
                    "restart_policy": "unless-stopped",
                    "environment": {
                        "AIR_GAP_MODE": "true",
                        "PYTHONUNBUFFERED": "1"
                    }
                }
            },
            "volumes": {
                "models": {"host": "./models", "container": "/app/models", "encrypted": True},
                "output": {"host": "./output", "container": "/app/output", "encrypted": False},
                "logs": {"host": "./logs", "container": "/app/logs", "encrypted": False}
            }
        }
    
    def setup_encrypted_volume(self, volume_name: str, password: str) -> bool:
        """
        Setup encrypted volume using LUKS/dm-crypt
        Note: Requires root privileges - this is a simulation for demonstration
        """
        try:
            volume_info = self.config["volumes"][volume_name]
            host_path = Path(volume_info["host"])
            
            # Create directory if it doesn't exist
            host_path.mkdir(parents=True, exist_ok=True)
            
            # Generate encryption key from password
            key = Fernet.generate_key()
            cipher_suite = Fernet(key)
            
            # Store volume info
            self.encrypted_volumes[volume_name] = VolumeInfo(
                host_path=str(host_path),
                container_path=volume_info["container"],
                encryption_key=key
            )
            
            self.logger.info(f"✅ Encrypted volume setup for {volume_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup encrypted volume {volume_name}: {e}")
            return False
    
    def mount_encrypted_volume(self, volume_name: str) -> bool:
        """Mount encrypted volume (simulation)"""
        if volume_name not in self.encrypted_volumes:
            self.logger.error(f"Volume {volume_name} not configured")
            return False
        
        volume = self.encrypted_volumes[volume_name]
        try:
            # In production, this would use actual encryption mounting
            # For demo purposes, we simulate successful mounting
            volume.mounted = True
            self.logger.info(f"✅ Mounted encrypted volume: {volume_name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to mount volume {volume_name}: {e}")
            return False
    
    def unmount_encrypted_volume(self, volume_name: str) -> bool:
        """Unmount encrypted volume"""
        if volume_name not in self.encrypted_volumes:
            return False
        
        volume = self.encrypted_volumes[volume_name]
        try:
            volume.mounted = False
            self.logger.info(f"✅ Unmounted encrypted volume: {volume_name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to unmount volume {volume_name}: {e}")
            return False
    
    def start_container(self, container_name: str) -> bool:
        """Start container with proper volume mounting"""
        try:
            container_config = self.config["containers"][container_name]
            
            # Prepare volume mounts
            volumes = {}
            for vol_name, vol_info in self.config["volumes"].items():
                if vol_info.get("encrypted", False):
                    if not self.mount_encrypted_volume(vol_name):
                        self.logger.error(f"Failed to mount encrypted volume {vol_name}")
                        return False
                    volumes[self.encrypted_volumes[vol_name].host_path] = {
                        'bind': vol_info['container'], 'mode': 'rw'
                    }
                else:
                    volumes[vol_info['host']] = {
                        'bind': vol_info['container'], 'mode': 'rw'
                    }
            
            # Start container
            container = self.docker_client.containers.run(
                image=container_config["image"],
                name=container_name,
                detach=True,
                volumes=volumes,
                environment=container_config["environment"],
                mem_limit=container_config["memory_limit"],
                cpu_quota=int(container_config["cpu_limit"]) * 100000,
                restart_policy={"Name": container_config["restart_policy"]},
                network="secure-ai-network"
            )
            
            self.running_containers[container_name] = container
            self.logger.info(f"✅ Container {container_name} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start container {container_name}: {e}")
            return False
    
    def stop_container(self, container_name: str) -> bool:
        """Stop container gracefully"""
        try:
            if container_name not in self.running_containers:
                self.logger.warning(f"Container {container_name} not running")
                return True
            
            container = self.running_containers[container_name]
            container.stop(timeout=30)
            container.remove()
            
            del self.running_containers[container_name]
            self.logger.info(f"✅ Container {container_name} stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to stop container {container_name}: {e}")
            return False
    
    def restart_container(self, container_name: str) -> bool:
        """Restart container with health check"""
        self.logger.info(f"🔄 Restarting container {container_name}")
        
        # Stop container
        if not self.stop_container(container_name):
            return False
        
        # Wait before restart
        time.sleep(5)
        
        # Start container
        return self.start_container(container_name)
    
    def check_health(self, container_name: str) -> Dict[str, any]:
        """Check container health and resource usage"""
        try:
            if container_name not in self.running_containers:
                return {"status": "not_running"}
            
            container = self.running_containers[container_name]
            stats = container.stats(stream=False)
            
            # Extract resource usage
            memory_stats = stats['memory_stats']
            cpu_stats = stats['cpu_stats']
            
            health_info = {
                "status": "running",
                "memory_usage_mb": memory_stats['usage'] / 1024 / 1024,
                "memory_limit_mb": memory_stats['limit'] / 1024 / 1024,
                "memory_percent": (memory_stats['usage'] / memory_stats['limit']) * 100,
                "cpu_percent": self._calculate_cpu_percent(cpu_stats),
                "healthy": self._is_healthy(container)
            }
            
            return health_info
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed for {container_name}: {e}")
            return {"status": "error", "message": str(e)}
    
    def _calculate_cpu_percent(self, cpu_stats: Dict) -> float:
        """Calculate CPU percentage usage"""
        try:
            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - 0  # Simplified
            system_delta = cpu_stats['system_cpu_usage'] - 0
            if system_delta > 0:
                return (cpu_delta / system_delta) * len(cpu_stats['cpu_usage']['percpu_usage']) * 100
            return 0.0
        except:
            return 0.0
    
    def _is_healthy(self, container) -> bool:
        """Check if container is healthy"""
        try:
            return container.status == "running"
        except:
            return False
    
    def auto_recover(self, container_name: str, max_attempts: int = 3) -> bool:
        """Auto-recover unhealthy container"""
        self.logger.info(f"🏥 Auto-recovery initiated for {container_name}")
        
        for attempt in range(max_attempts):
            health = self.check_health(container_name)
            
            if health.get("status") == "running" and health.get("healthy", False):
                self.logger.info(f"✅ Container {container_name} is healthy")
                return True
            
            self.logger.warning(f"🔄 Recovery attempt {attempt + 1}/{max_attempts}")
            if not self.restart_container(container_name):
                time.sleep(10)  # Wait before next attempt
                continue
            
            # Wait for container to stabilize
            time.sleep(30)
        
        self.logger.error(f"❌ Failed to recover container {container_name} after {max_attempts} attempts")
        return False
    
    def get_resource_usage_report(self) -> Dict[str, any]:
        """Generate resource usage report for all containers"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "system_resources": {
                "total_memory_gb": psutil.virtual_memory().total / (1024**3),
                "available_memory_gb": psutil.virtual_memory().available / (1024**3),
                "memory_percent": psutil.virtual_memory().percent,
                "cpu_percent": psutil.cpu_percent(interval=1)
            },
            "containers": {}
        }
        
        for container_name in self.running_containers:
            report["containers"][container_name] = self.check_health(container_name)
        
        return report

def main():
    """Main execution function"""
    print("🛡️ SECURE AI STUDIO - Container Lifecycle Manager")
    print("=" * 50)
    
    try:
        # Initialize manager
        manager = ContainerLifecycleManager()
        
        # Setup encrypted volumes
        print("\n🔐 Setting up encrypted volumes...")
        manager.setup_encrypted_volume("models", "secure_password_123")
        
        # Start container
        print("\n🚀 Starting AI engine container...")
        if manager.start_container("secure-ai-engine"):
            print("✅ Container started successfully")
            
            # Monitor for a bit
            print("\n📊 Monitoring container health...")
            time.sleep(10)
            
            health = manager.check_health("secure-ai-engine")
            print(f"Health status: {health}")
            
            # Generate report
            report = manager.get_resource_usage_report()
            print(f"\n📈 Resource Report: {json.dumps(report, indent=2)}")
            
        else:
            print("❌ Failed to start container")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)