#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Internal Monitoring Agent
Telemetry collection for generation pipeline steps and system metrics

Features:
- Step-by-step generation pipeline timing
- Hardware telemetry (CPU temperature, memory, disk I/O)
- Performance metrics export (JSON/CSV)
- Trend analysis data collection
- Real-time metric streaming
"""

import time
import json
import psutil
import GPUtil
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import csv

@dataclass
class PipelineStep:
    """Individual pipeline step timing"""
    step_name: str
    start_time: float
    end_time: float
    duration: float
    memory_usage_start: float  # MB
    memory_usage_end: float    # MB
    cpu_percent_start: float
    cpu_percent_end: float
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class GenerationSession:
    """Complete generation session with all steps"""
    session_id: str
    start_timestamp: str
    end_timestamp: str
    total_duration: float
    steps: List[PipelineStep]
    input_parameters: Dict[str, Any]
    output_files: List[str]
    system_metrics: Dict[str, Any]
    success: bool = True

@dataclass
class HardwareMetrics:
    """Current hardware metrics"""
    timestamp: float
    cpu_percent: float
    cpu_temp: Optional[float]  # Celsius
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    gpu_memory_mb: Optional[float]
    gpu_utilization: Optional[float]
    network_bytes_sent: float
    network_bytes_recv: float

class MonitoringAgent:
    """
    Internal monitoring agent for pipeline telemetry
    """
    
    def __init__(self, export_directory: str = "metrics"):
        """Initialize monitoring agent"""
        self.export_dir = Path(export_directory)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logging()
        
        # Active sessions tracking
        self.active_sessions = {}
        self.completed_sessions = []
        
        # Hardware monitoring
        self.hardware_history = []
        self.monitoring_active = False
        self.monitor_thread = None
        
        # System counters for deltas
        self.last_disk_io = psutil.disk_io_counters()
        self.last_net_io = psutil.net_io_counters()
        
        self.logger.info("📊 Monitoring Agent initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('MonitoringAgent')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(self.export_dir / "monitoring_agent.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def start_session(self, session_id: str, input_parameters: Dict[str, Any]) -> str:
        """Start a new generation session"""
        if session_id in self.active_sessions:
            self.logger.warning(f"Session {session_id} already exists, overwriting")
        
        self.active_sessions[session_id] = {
            'session_id': session_id,
            'start_timestamp': datetime.now().isoformat(),
            'input_parameters': input_parameters,
            'steps': [],
            'output_files': [],
            'system_start_metrics': self._collect_system_snapshot()
        }
        
        self.logger.info(f"🎬 Started monitoring session: {session_id}")
        return session_id
    
    def start_step(self, session_id: str, step_name: str) -> float:
        """Start timing a pipeline step"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        start_time = time.time()
        
        # Collect initial metrics
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        step_data = {
            'step_name': step_name,
            'start_time': start_time,
            'memory_usage_start': memory_mb,
            'cpu_percent_start': cpu_percent
        }
        
        self.active_sessions[session_id]['steps'].append(step_data)
        self.logger.debug(f"⏱️  Started step '{step_name}' for session {session_id}")
        
        return start_time
    
    def end_step(self, session_id: str, step_name: str, start_time: float, 
                 success: bool = True, error_message: str = None):
        """End timing a pipeline step"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Collect final metrics
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Find the step and update it
        for step in self.active_sessions[session_id]['steps']:
            if step['step_name'] == step_name and 'end_time' not in step:
                step.update({
                    'end_time': end_time,
                    'duration': duration,
                    'memory_usage_end': memory_mb,
                    'cpu_percent_end': cpu_percent,
                    'success': success,
                    'error_message': error_message
                })
                break
        
        self.logger.info(f"✅ Completed step '{step_name}' in {duration:.3f}s (session: {session_id})")
    
    def add_output_file(self, session_id: str, file_path: str):
        """Add generated output file to session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['output_files'].append(file_path)
    
    def end_session(self, session_id: str, success: bool = True) -> GenerationSession:
        """End generation session and create complete record"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session_data = self.active_sessions[session_id]
        end_time = datetime.now().isoformat()
        
        # Calculate total duration
        start_dt = datetime.fromisoformat(session_data['start_timestamp'])
        end_dt = datetime.fromisoformat(end_time)
        total_duration = (end_dt - start_dt).total_seconds()
        
        # Create pipeline steps
        steps = []
        for step_data in session_data['steps']:
            if 'end_time' in step_data:  # Only completed steps
                steps.append(PipelineStep(
                    step_name=step_data['step_name'],
                    start_time=step_data['start_time'],
                    end_time=step_data['end_time'],
                    duration=step_data['duration'],
                    memory_usage_start=step_data['memory_usage_start'],
                    memory_usage_end=step_data['memory_usage_end'],
                    cpu_percent_start=step_data['cpu_percent_start'],
                    cpu_percent_end=step_data['cpu_percent_end'],
                    success=step_data.get('success', True),
                    error_message=step_data.get('error_message')
                ))
        
        # Create session record
        session_record = GenerationSession(
            session_id=session_id,
            start_timestamp=session_data['start_timestamp'],
            end_timestamp=end_time,
            total_duration=total_duration,
            steps=steps,
            input_parameters=session_data['input_parameters'],
            output_files=session_data['output_files'],
            system_metrics=self._collect_system_snapshot(),
            success=success
        )
        
        # Move to completed sessions
        self.completed_sessions.append(session_record)
        del self.active_sessions[session_id]
        
        # Export session data
        self._export_session(session_record)
        
        self.logger.info(f"🏁 Ended session {session_id} - Total time: {total_duration:.3f}s")
        return session_record
    
    def _collect_system_snapshot(self) -> Dict[str, Any]:
        """Collect current system metrics snapshot"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            if self.last_disk_io:
                disk_read_mb = (disk_io.read_bytes - self.last_disk_io.read_bytes) / (1024 * 1024)
                disk_write_mb = (disk_io.write_bytes - self.last_disk_io.write_bytes) / (1024 * 1024)
            else:
                disk_read_mb = disk_write_mb = 0
            self.last_disk_io = disk_io
            
            # Network I/O metrics
            net_io = psutil.net_io_counters()
            if self.last_net_io:
                net_sent_mb = (net_io.bytes_sent - self.last_net_io.bytes_sent) / (1024 * 1024)
                net_recv_mb = (net_io.bytes_recv - self.last_net_io.bytes_recv) / (1024 * 1024)
            else:
                net_sent_mb = net_recv_mb = 0
            self.last_net_io = net_io
            
            # GPU metrics
            gpu_memory_mb = None
            gpu_utilization = None
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_memory_mb = gpu.memoryUsed
                    gpu_utilization = gpu.load * 100
            except:
                pass
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / (1024 * 1024),
                'disk_read_mb': disk_read_mb,
                'disk_write_mb': disk_write_mb,
                'network_sent_mb': net_sent_mb,
                'network_recv_mb': net_recv_mb,
                'gpu_memory_mb': gpu_memory_mb,
                'gpu_utilization': gpu_utilization,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def start_hardware_monitoring(self, interval: float = 1.0):
        """Start continuous hardware monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._hardware_monitoring_loop,
                args=(interval,),
                daemon=True
            )
            self.monitor_thread.start()
            self.logger.info(f"🔄 Started hardware monitoring (interval: {interval}s)")
    
    def stop_hardware_monitoring(self):
        """Stop continuous hardware monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.logger.info("🛑 Stopped hardware monitoring")
    
    def _hardware_monitoring_loop(self, interval: float):
        """Continuous hardware monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self._collect_system_snapshot()
                hardware_metric = HardwareMetrics(
                    timestamp=time.time(),
                    cpu_percent=metrics['cpu_percent'],
                    cpu_temp=None,  # Would require additional sensors
                    memory_percent=metrics['memory_percent'],
                    memory_used_mb=metrics['memory_used_mb'],
                    disk_io_read_mb=metrics['disk_read_mb'],
                    disk_io_write_mb=metrics['disk_write_mb'],
                    gpu_memory_mb=metrics.get('gpu_memory_mb'),
                    gpu_utilization=metrics.get('gpu_utilization'),
                    network_bytes_sent=metrics['network_sent_mb'] * 1024 * 1024,
                    network_bytes_recv=metrics['network_recv_mb'] * 1024 * 1024
                )
                
                self.hardware_history.append(hardware_metric)
                
                # Keep history within limits
                if len(self.hardware_history) > 3600:  # 1 hour at 1s intervals
                    self.hardware_history.pop(0)
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Hardware monitoring error: {e}")
                time.sleep(interval)
    
    def _export_session(self, session: GenerationSession):
        """Export session data to JSON"""
        try:
            # JSON export
            json_path = self.export_dir / f"session_{session.session_id}.json"
            with open(json_path, 'w') as f:
                json.dump(asdict(session), f, indent=2, default=str)
            
            # CSV export for steps
            csv_path = self.export_dir / f"steps_{session.session_id}.csv"
            with open(csv_path, 'w', newline='') as f:
                if session.steps:
                    writer = csv.DictWriter(f, fieldnames=[
                        'step_name', 'duration', 'memory_start_mb', 'memory_end_mb',
                        'cpu_start_percent', 'cpu_end_percent', 'success'
                    ])
                    writer.writeheader()
                    
                    for step in session.steps:
                        writer.writerow({
                            'step_name': step.step_name,
                            'duration': step.duration,
                            'memory_start_mb': step.memory_usage_start,
                            'memory_end_mb': step.memory_usage_end,
                            'cpu_start_percent': step.cpu_percent_start,
                            'cpu_end_percent': step.cpu_percent_end,
                            'success': step.success
                        })
            
            self.logger.info(f"💾 Exported session {session.session_id} to {json_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export session {session.session_id}: {e}")
    
    def export_hardware_metrics(self, format: str = 'json') -> str:
        """Export collected hardware metrics"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            export_path = self.export_dir / f"hardware_metrics_{timestamp}.json"
            metrics_data = [asdict(metric) for metric in self.hardware_history]
            
            with open(export_path, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
        elif format == 'csv':
            export_path = self.export_dir / f"hardware_metrics_{timestamp}.csv"
            with open(export_path, 'w', newline='') as f:
                if self.hardware_history:
                    writer = csv.DictWriter(f, fieldnames=[
                        'timestamp', 'cpu_percent', 'memory_percent', 'memory_used_mb',
                        'disk_io_read_mb', 'disk_io_write_mb', 'gpu_utilization'
                    ])
                    writer.writeheader()
                    
                    for metric in self.hardware_history:
                        writer.writerow({
                            'timestamp': metric.timestamp,
                            'cpu_percent': metric.cpu_percent,
                            'memory_percent': metric.memory_percent,
                            'memory_used_mb': metric.memory_used_mb,
                            'disk_io_read_mb': metric.disk_io_read_mb,
                            'disk_io_write_mb': metric.disk_io_write_mb,
                            'gpu_utilization': metric.gpu_utilization
                        })
        
        self.logger.info(f"📊 Exported hardware metrics to {export_path}")
        return str(export_path)
    
    def get_performance_trends(self) -> Dict[str, Any]:
        """Generate performance trend analysis"""
        if not self.completed_sessions:
            return {'error': 'No completed sessions for analysis'}
        
        # Analyze step durations
        step_durations = {}
        total_times = []
        
        for session in self.completed_sessions:
            total_times.append(session.total_duration)
            
            for step in session.steps:
                if step.step_name not in step_durations:
                    step_durations[step.step_name] = []
                step_durations[step.step_name].append(step.duration)
        
        # Calculate statistics
        trends = {
            'total_generation_times': {
                'count': len(total_times),
                'average': sum(total_times) / len(total_times),
                'min': min(total_times),
                'max': max(total_times),
                'median': sorted(total_times)[len(total_times)//2]
            },
            'step_performance': {}
        }
        
        # Step performance analysis
        for step_name, durations in step_durations.items():
            trends['step_performance'][step_name] = {
                'count': len(durations),
                'average': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations),
                'median': sorted(durations)[len(durations)//2]
            }
        
        return trends
    
    def get_current_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.active_sessions.keys())
    
    def get_completed_sessions_count(self) -> int:
        """Get number of completed sessions"""
        return len(self.completed_sessions)

# Integration with Secure AI Engine
class EngineWithMonitoring:
    """Wrapper to integrate monitoring with existing engine"""
    
    def __init__(self, engine, monitoring_agent: MonitoringAgent):
        self.engine = engine
        self.monitor = monitoring_agent
    
    def generate_content_with_monitoring(self, request, session_id: str = None):
        """Generate content with full monitoring"""
        import uuid
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Start monitoring session
        self.monitor.start_session(session_id, {
            'content_type': request.content_type,
            'prompt': request.prompt,
            'dimensions': request.dimensions,
            'format': request.format
        })
        
        try:
            # Step 1: Load Model
            step_timer = self.monitor.start_step(session_id, "load_model")
            # ... model loading logic ...
            self.monitor.end_step(session_id, "load_model", step_timer)
            
            # Step 2: Inference
            step_timer = self.monitor.start_step(session_id, "inference")
            result = self.engine.generate_content(request)
            self.monitor.end_step(session_id, "inference", step_timer)
            
            # Step 3: Watermark
            step_timer = self.monitor.start_step(session_id, "watermark")
            # ... watermarking logic ...
            self.monitor.end_step(session_id, "watermark", step_timer)
            
            # Step 4: Save
            step_timer = self.monitor.start_step(session_id, "save_file")
            # ... file saving logic ...
            for path in result.output_paths:
                self.monitor.add_output_file(session_id, path)
            self.monitor.end_step(session_id, "save_file", step_timer)
            
            # End session
            session_record = self.monitor.end_session(session_id, result.success)
            
            # Attach monitoring data to result
            result.monitoring_session = session_record
            
            return result
            
        except Exception as e:
            # End session with error
            self.monitor.end_session(session_id, success=False)
            raise

# Example usage
def main():
    """Demo monitoring agent functionality"""
    print("📊 MONITORING AGENT DEMO")
    print("=" * 30)
    
    # Initialize agent
    agent = MonitoringAgent()
    
    try:
        # Start hardware monitoring
        agent.start_hardware_monitoring(interval=0.5)
        
        # Simulate generation session
        session_id = "demo_session_001"
        
        # Start session
        input_params = {
            'content_type': 'image',
            'prompt': 'Landscape painting',
            'dimensions': (512, 512),
            'format': 'PNG'
        }
        
        agent.start_session(session_id, input_params)
        
        # Simulate pipeline steps
        steps = [
            ("load_model", 0.5),
            ("inference", 2.3),
            ("watermark", 0.8),
            ("save_file", 0.3)
        ]
        
        for step_name, duration in steps:
            start_time = agent.start_step(session_id, step_name)
            time.sleep(duration)  # Simulate work
            agent.end_step(session_id, step_name, start_time)
            agent.add_output_file(session_id, f"output/demo_{step_name}.png")
        
        # End session
        session_record = agent.end_session(session_id)
        
        # Show results
        print(f"✅ Session completed: {session_record.session_id}")
        print(f"Total duration: {session_record.total_duration:.3f}s")
        print(f"Steps completed: {len(session_record.steps)}")
        
        # Show trends
        trends = agent.get_performance_trends()
        print(f"Average generation time: {trends['total_generation_times']['average']:.3f}s")
        
        # Export hardware metrics
        hw_export = agent.export_hardware_metrics('csv')
        print(f"Hardware metrics exported to: {hw_export}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        agent.stop_hardware_monitoring()
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)