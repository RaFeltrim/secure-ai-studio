#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - PyTorch Memory Health Monitor
Advanced memory monitoring with auto-restart capabilities

Features:
- Real-time PyTorch GPU/CPU memory monitoring
- Threshold-based alerting system
- Automatic service restart on memory leaks
- Performance degradation detection
"""

import os
import sys
import time
import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import psutil
import GPUtil
import torch
from collections import deque

@dataclass
class MemoryMetrics:
    """Memory usage metrics data class"""
    timestamp: datetime
    ram_usage_mb: float
    ram_percent: float
    gpu_memory_mb: Optional[float] = None
    gpu_utilization: Optional[float] = None
    torch_allocated_mb: Optional[float] = None
    torch_reserved_mb: Optional[float] = None
    leak_detected: bool = False

class PyTorchMemoryMonitor:
    """
    Advanced PyTorch memory monitoring system
    """
    
    def __init__(self, config_path: str = "config/memory_monitor.conf"):
        """Initialize memory monitor"""
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.metrics_history = deque(maxlen=self.config['history_size'])
        self.alert_callbacks = []
        self.restart_callbacks = []
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Thresholds
        self.ram_threshold_percent = self.config['ram_threshold_percent']
        self.gpu_threshold_percent = self.config['gpu_threshold_percent']
        self.torch_leak_threshold_mb = self.config['torch_leak_threshold_mb']
        
        self.logger.info("🧠 PyTorch Memory Monitor initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging system"""
        logger = logging.getLogger('MemoryMonitor')
        logger.setLevel(logging.INFO)
        
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        handler = logging.FileHandler(
            log_dir / f"memory_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_config(self, config_path: str) -> Dict:
        """Load monitor configuration"""
        default_config = {
            'monitoring_interval': 5,  # seconds
            'history_size': 1000,
            'ram_threshold_percent': 85.0,
            'gpu_threshold_percent': 80.0,
            'torch_leak_threshold_mb': 500.0,
            'auto_restart_enabled': True,
            'alert_cooldown_seconds': 300,
            'performance_window_size': 10
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                return default_config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return default_config
    
    def add_alert_callback(self, callback: Callable[[Dict], None]):
        """Add callback for memory alerts"""
        self.alert_callbacks.append(callback)
    
    def add_restart_callback(self, callback: Callable[[], bool]):
        """Add callback for auto-restart"""
        self.restart_callbacks.append(callback)
    
    def start_monitoring(self):
        """Start memory monitoring thread"""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("✅ Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        self.logger.info("🛑 Memory monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        last_alert_time = 0
        performance_window = deque(maxlen=self.config['performance_window_size'])
        
        while self.monitoring_active:
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                performance_window.append(metrics.ram_percent)
                
                # Check thresholds
                alert_needed = self._check_thresholds(metrics, performance_window)
                
                # Handle alerts
                current_time = time.time()
                if alert_needed and (current_time - last_alert_time) > self.config['alert_cooldown_seconds']:
                    self._trigger_alert(metrics)
                    last_alert_time = current_time
                    
                    # Auto-restart if enabled
                    if self.config['auto_restart_enabled']:
                        self._attempt_auto_restart()
                
                # Sleep until next check
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                time.sleep(self.config['monitoring_interval'])
    
    def _collect_metrics(self) -> MemoryMetrics:
        """Collect comprehensive memory metrics"""
        timestamp = datetime.now()
        
        # System RAM metrics
        ram = psutil.virtual_memory()
        ram_usage_mb = ram.used / (1024 * 1024)
        ram_percent = ram.percent
        
        # GPU metrics (if available)
        gpu_memory_mb = None
        gpu_utilization = None
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # First GPU
                gpu_memory_mb = gpu.memoryUsed
                gpu_utilization = gpu.load * 100
        except:
            pass
        
        # PyTorch specific metrics
        torch_allocated_mb = None
        torch_reserved_mb = None
        try:
            if torch.cuda.is_available():
                torch_allocated_mb = torch.cuda.memory_allocated() / (1024 * 1024)
                torch_reserved_mb = torch.cuda.memory_reserved() / (1024 * 1024)
            else:
                # CPU memory tracking (approximate)
                if hasattr(torch, 'get_num_threads'):
                    # This is a simplified approximation
                    torch_allocated_mb = psutil.Process().memory_info().rss / (1024 * 1024)
        except:
            pass
        
        return MemoryMetrics(
            timestamp=timestamp,
            ram_usage_mb=ram_usage_mb,
            ram_percent=ram_percent,
            gpu_memory_mb=gpu_memory_mb,
            gpu_utilization=gpu_utilization,
            torch_allocated_mb=torch_allocated_mb,
            torch_reserved_mb=torch_reserved_mb
        )
    
    def _check_thresholds(self, metrics: MemoryMetrics, performance_window: deque) -> bool:
        """Check if memory thresholds are exceeded"""
        alerts = []
        
        # RAM threshold check
        if metrics.ram_percent > self.ram_threshold_percent:
            alerts.append(f"RAM usage {metrics.ram_percent:.1f}% exceeds threshold {self.ram_threshold_percent}%")
        
        # GPU threshold check
        if metrics.gpu_memory_mb and metrics.gpu_utilization:
            if metrics.gpu_utilization > self.gpu_threshold_percent:
                alerts.append(f"GPU utilization {metrics.gpu_utilization:.1f}% exceeds threshold {self.gpu_threshold_percent}%")
        
        # PyTorch memory leak detection
        if metrics.torch_allocated_mb and len(self.metrics_history) > 10:
            recent_allocations = [m.torch_allocated_mb for m in list(self.metrics_history)[-10:] if m.torch_allocated_mb]
            if len(recent_allocations) >= 5:
                avg_allocation = sum(recent_allocations[-5:]) / 5
                current_allocation = metrics.torch_allocated_mb
                
                if current_allocation > avg_allocation + self.torch_leak_threshold_mb:
                    alerts.append(f"Potential PyTorch memory leak detected: {current_allocation:.1f}MB vs average {avg_allocation:.1f}MB")
                    metrics.leak_detected = True
        
        # Performance degradation check
        if len(performance_window) == self.config['performance_window_size']:
            recent_avg = sum(list(performance_window)[-5:]) / 5
            older_avg = sum(list(performance_window)[:5]) / 5
            
            if recent_avg > older_avg + 10:  # 10% increase
                alerts.append(f"Performance degradation detected: RAM usage increased from {older_avg:.1f}% to {recent_avg:.1f}%")
        
        if alerts:
            for alert in alerts:
                self.logger.warning(f"🚨 ALERT: {alert}")
            return True
        
        return False
    
    def _trigger_alert(self, metrics: MemoryMetrics):
        """Trigger alert callbacks"""
        alert_data = {
            'timestamp': metrics.timestamp.isoformat(),
            'metrics': asdict(metrics),
            'alert_type': 'MEMORY_THRESHOLD_EXCEEDED' if not metrics.leak_detected else 'MEMORY_LEAK_DETECTED'
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def _attempt_auto_restart(self):
        """Attempt auto-restart of services"""
        self.logger.warning("🔄 Attempting auto-restart due to memory issues")
        
        success_count = 0
        for callback in self.restart_callbacks:
            try:
                if callback():
                    success_count += 1
            except Exception as e:
                self.logger.error(f"Restart callback error: {e}")
        
        if success_count > 0:
            self.logger.info(f"✅ Auto-restart completed successfully for {success_count} services")
        else:
            self.logger.error("❌ Auto-restart failed for all services")
    
    def get_current_status(self) -> Dict:
        """Get current memory status"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        latest = self.metrics_history[-1]
        return {
            "status": "ok" if latest.ram_percent < self.ram_threshold_percent else "warning",
            "timestamp": latest.timestamp.isoformat(),
            "ram_usage_mb": latest.ram_usage_mb,
            "ram_percent": latest.ram_percent,
            "gpu_memory_mb": latest.gpu_memory_mb,
            "gpu_utilization": latest.gpu_utilization,
            "torch_allocated_mb": latest.torch_allocated_mb,
            "torch_reserved_mb": latest.torch_reserved_mb,
            "leak_detected": latest.leak_detected
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict:
        """Generate performance report for specified time period"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        relevant_metrics = [
            m for m in self.metrics_history 
            if m.timestamp.timestamp() >= cutoff_time
        ]
        
        if not relevant_metrics:
            return {"error": "No data for specified time period"}
        
        ram_usage = [m.ram_percent for m in relevant_metrics]
        torch_memory = [m.torch_allocated_mb for m in relevant_metrics if m.torch_allocated_mb]
        
        return {
            "period_hours": hours,
            "total_samples": len(relevant_metrics),
            "ram_statistics": {
                "min_percent": min(ram_usage),
                "max_percent": max(ram_usage),
                "average_percent": sum(ram_usage) / len(ram_usage),
                "threshold_exceeded_count": sum(1 for usage in ram_usage if usage > self.ram_threshold_percent)
            },
            "torch_statistics": {
                "samples": len(torch_memory),
                "min_mb": min(torch_memory) if torch_memory else 0,
                "max_mb": max(torch_memory) if torch_memory else 0,
                "average_mb": sum(torch_memory) / len(torch_memory) if torch_memory else 0
            } if torch_memory else {"samples": 0}
        }

class MemoryHealthDashboard:
    """Simple dashboard for memory monitoring"""
    
    def __init__(self, monitor: PyTorchMemoryMonitor):
        self.monitor = monitor
    
    def print_status(self):
        """Print current memory status"""
        status = self.monitor.get_current_status()
        
        print("\n" + "="*60)
        print("🧠 PYTORCH MEMORY HEALTH DASHBOARD")
        print("="*60)
        print(f"🕒 Last Update: {status.get('timestamp', 'N/A')}")
        print(f"📊 Status: {status.get('status', 'Unknown').upper()}")
        print(f"💾 RAM Usage: {status.get('ram_percent', 0):.1f}% ({status.get('ram_usage_mb', 0):.1f} MB)")
        print(f"🎮 GPU Memory: {status.get('gpu_memory_mb', 0):.1f} MB")
        print(f"⚡ GPU Utilization: {status.get('gpu_utilization', 0):.1f}%")
        print(f"🔥 Torch Allocated: {status.get('torch_allocated_mb', 0):.1f} MB")
        print(f"🔒 Torch Reserved: {status.get('torch_reserved_mb', 0):.1f} MB")
        print(f"⚠️  Leak Detected: {'YES' if status.get('leak_detected', False) else 'NO'}")
        
        if status.get('status') == 'warning':
            print("\n🚨 WARNING: Memory usage above threshold!")
        
        print("="*60)

def main():
    """Main execution for testing"""
    print("🧠 PYTORCH MEMORY HEALTH MONITOR")
    print("=" * 40)
    
    # Initialize monitor
    monitor = PyTorchMemoryMonitor()
    
    # Add sample callbacks
    def alert_handler(alert_data):
        print(f"🔔 ALERT RECEIVED: {alert_data['alert_type']}")
    
    def restart_handler():
        print("🔄 RESTART TRIGGERED")
        return True  # Simulate successful restart
    
    monitor.add_alert_callback(alert_handler)
    monitor.add_restart_callback(restart_handler)
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Create dashboard
    dashboard = MemoryHealthDashboard(monitor)
    
    try:
        # Monitor for 30 seconds
        for i in range(6):
            dashboard.print_status()
            time.sleep(5)
        
        # Generate report
        report = monitor.get_performance_report(hours=1)
        print(f"\n📈 Performance Report: {json.dumps(report, indent=2)}")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitor...")
    finally:
        monitor.stop_monitoring()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)