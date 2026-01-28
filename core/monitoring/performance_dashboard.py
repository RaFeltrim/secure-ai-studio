#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Performance Dashboard
Real-time monitoring and performance visualization system

Features:
- System resource monitoring
- AI generation performance tracking
- Real-time metrics visualization
- Historical performance analysis
- Alert system for performance degradation
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib.figure import Figure
import psutil
import GPUtil
import torch
import time
import json
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    gpu_memory_mb: Optional[float]
    gpu_utilization: Optional[float]
    torch_memory_mb: Optional[float]
    active_jobs: int
    pending_jobs: int
    generation_rate: float  # generations per minute

class PerformanceDashboard:
    """
    Real-time performance monitoring dashboard
    """
    
    def __init__(self, title: str = "Secure AI Studio - Performance Dashboard"):
        """Initialize dashboard"""
        self.title = title
        self.logger = self._setup_logging()
        
        # Metrics storage
        self.metrics_history = []
        self.max_history_points = 300  # 5 minutes of data at 1-second intervals
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Alert thresholds
        self.alert_thresholds = {
            'cpu_percent': 85.0,
            'memory_percent': 80.0,
            'gpu_utilization': 90.0,
            'generation_time': 30.0  # seconds
        }
        
        # Create main window
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("1200x800")
        
        # Setup UI components
        self._setup_ui()
        
        self.logger.info("📊 Performance Dashboard initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('PerformanceDashboard')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_ui(self):
        """Setup user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_overview_tab()
        self._create_system_tab()
        self._create_performance_tab()
        self._create_alerts_tab()
        self._create_logs_tab()
        
        # Create control panel
        self._create_control_panel()
    
    def _create_overview_tab(self):
        """Create system overview tab"""
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="Overview")
        
        # System status frame
        status_frame = ttk.LabelFrame(self.overview_frame, text="System Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Status indicators
        self.status_labels = {}
        status_items = [
            ("CPU Usage", "cpu_status"),
            ("Memory Usage", "memory_status"),
            ("GPU Status", "gpu_status"),
            ("AI Engine", "engine_status"),
            ("Queue Status", "queue_status")
        ]
        
        for i, (label, key) in enumerate(status_items):
            ttk.Label(status_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            self.status_labels[key] = ttk.Label(status_frame, text="Unknown")
            self.status_labels[key].grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Quick metrics frame
        metrics_frame = ttk.LabelFrame(self.overview_frame, text="Quick Metrics", padding=10)
        metrics_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.quick_metrics = {}
        metric_items = [
            ("Active Jobs", "active_jobs"),
            ("Pending Jobs", "pending_jobs"),
            ("Avg Generation Time", "avg_time"),
            ("Success Rate", "success_rate")
        ]
        
        for i, (label, key) in enumerate(metric_items):
            ttk.Label(metrics_frame, text=f"{label}:").grid(row=i//2, column=(i%2)*2, sticky=tk.W, padx=5, pady=2)
            self.quick_metrics[key] = ttk.Label(metrics_frame, text="0")
            self.quick_metrics[key].grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=2)
    
    def _create_system_tab(self):
        """Create system resources tab"""
        self.system_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.system_frame, text="System Resources")
        
        # Create matplotlib figure for system metrics
        self.system_fig = Figure(figsize=(10, 6), dpi=100)
        self.system_canvas = FigureCanvasTkAgg(self.system_fig, self.system_frame)
        self.system_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create subplots
        self.cpu_ax = self.system_fig.add_subplot(2, 2, 1)
        self.mem_ax = self.system_fig.add_subplot(2, 2, 2)
        self.gpu_ax = self.system_fig.add_subplot(2, 2, 3)
        self.jobs_ax = self.system_fig.add_subplot(2, 2, 4)
        
        # Initialize plots
        self._initialize_system_plots()
    
    def _create_performance_tab(self):
        """Create AI performance tab"""
        self.performance_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.performance_frame, text="AI Performance")
        
        # Create matplotlib figure for performance metrics
        self.perf_fig = Figure(figsize=(10, 6), dpi=100)
        self.perf_canvas = FigureCanvasTkAgg(self.perf_fig, self.performance_frame)
        self.perf_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Create subplots
        self.generation_ax = self.perf_fig.add_subplot(2, 1, 1)
        self.throughput_ax = self.perf_fig.add_subplot(2, 1, 2)
        
        # Initialize plots
        self._initialize_performance_plots()
    
    def _create_alerts_tab(self):
        """Create alerts and notifications tab"""
        self.alerts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.alerts_frame, text="Alerts")
        
        # Alerts treeview
        columns = ('timestamp', 'level', 'component', 'message')
        self.alerts_tree = ttk.Treeview(self.alerts_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        self.alerts_tree.heading('timestamp', text='Time')
        self.alerts_tree.heading('level', text='Level')
        self.alerts_tree.heading('component', text='Component')
        self.alerts_tree.heading('message', text='Message')
        
        # Define column widths
        self.alerts_tree.column('timestamp', width=150)
        self.alerts_tree.column('level', width=80)
        self.alerts_tree.column('component', width=120)
        self.alerts_tree.column('message', width=400)
        
        self.alerts_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Alert controls
        alert_controls = ttk.Frame(self.alerts_frame)
        alert_controls.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(alert_controls, text="Clear Alerts", 
                  command=self._clear_alerts).pack(side=tk.LEFT, padx=5)
        ttk.Button(alert_controls, text="Export Alerts", 
                  command=self._export_alerts).pack(side=tk.LEFT, padx=5)
    
    def _create_logs_tab(self):
        """Create system logs tab"""
        self.logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="Logs")
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(self.logs_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log controls
        log_controls = ttk.Frame(self.logs_frame)
        log_controls.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_controls, text="Clear Logs", 
                  command=self._clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_controls, text="Save Logs", 
                  command=self._save_logs).pack(side=tk.LEFT, padx=5)
    
    def _create_control_panel(self):
        """Create control panel"""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Monitoring controls
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", 
                                      command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Monitoring", 
                                     command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Refresh interval
        ttk.Label(control_frame, text="Refresh (sec):").pack(side=tk.LEFT, padx=(20, 5))
        self.refresh_var = tk.StringVar(value="1")
        refresh_spinbox = ttk.Spinbox(control_frame, from_=0.1, to=10.0, 
                                     increment=0.1, textvariable=self.refresh_var, width=5)
        refresh_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Status indicator
        self.status_label = ttk.Label(control_frame, text="Stopped", foreground="red")
        self.status_label.pack(side=tk.RIGHT, padx=10)
    
    def _initialize_system_plots(self):
        """Initialize system monitoring plots"""
        # CPU plot
        self.cpu_ax.set_title('CPU Usage (%)')
        self.cpu_ax.set_ylim(0, 100)
        self.cpu_line, = self.cpu_ax.plot([], [], 'b-', label='CPU')
        self.cpu_ax.legend()
        self.cpu_ax.grid(True)
        
        # Memory plot
        self.mem_ax.set_title('Memory Usage (%)')
        self.mem_ax.set_ylim(0, 100)
        self.mem_line, = self.mem_ax.plot([], [], 'r-', label='Memory')
        self.mem_ax.legend()
        self.mem_ax.grid(True)
        
        # GPU plot
        self.gpu_ax.set_title('GPU Utilization (%)')
        self.gpu_ax.set_ylim(0, 100)
        self.gpu_line, = self.gpu_ax.plot([], [], 'g-', label='GPU')
        self.gpu_ax.legend()
        self.gpu_ax.grid(True)
        
        # Jobs plot
        self.jobs_ax.set_title('Queue Status')
        self.jobs_ax.set_ylim(0, 20)
        self.active_jobs_line, = self.jobs_ax.plot([], [], 'b-', label='Active')
        self.pending_jobs_line, = self.jobs_ax.plot([], [], 'r-', label='Pending')
        self.jobs_ax.legend()
        self.jobs_ax.grid(True)
    
    def _initialize_performance_plots(self):
        """Initialize performance plots"""
        # Generation time plot
        self.generation_ax.set_title('Generation Time (seconds)')
        self.generation_ax.set_ylabel('Time (s)')
        self.generation_line, = self.generation_ax.plot([], [], 'purple', marker='o')
        self.generation_ax.grid(True)
        
        # Throughput plot
        self.throughput_ax.set_title('Throughput (generations/minute)')
        self.throughput_ax.set_xlabel('Time')
        self.throughput_ax.set_ylabel('Generations/min')
        self.throughput_line, = self.throughput_ax.plot([], [], 'orange', marker='s')
        self.throughput_ax.grid(True)
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Running", foreground="green")
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            self.logger.info("✅ Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Stopped", foreground="red")
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        self.logger.info("🛑 Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep history within limits
                if len(self.metrics_history) > self.max_history_points:
                    self.metrics_history.pop(0)
                
                # Update UI (must be done on main thread)
                self.root.after(0, self._update_display, metrics)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Wait for next update
                refresh_interval = float(self.refresh_var.get())
                time.sleep(refresh_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(1)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect system and performance metrics"""
        timestamp = datetime.now()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
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
        
        # PyTorch memory
        torch_memory_mb = None
        try:
            if torch.cuda.is_available():
                torch_memory_mb = torch.cuda.memory_allocated() / (1024 * 1024)
        except:
            pass
        
        # Simulated job metrics (would connect to actual queue system)
        active_jobs = len([m for m in self.metrics_history[-10:] if hasattr(m, 'active_jobs')]) % 5
        pending_jobs = len([m for m in self.metrics_history[-10:] if hasattr(m, 'pending_jobs')]) % 3
        generation_rate = 2.5 + np.random.normal(0, 0.5)  # Simulated
        
        return PerformanceMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            gpu_memory_mb=gpu_memory_mb,
            gpu_utilization=gpu_utilization,
            torch_memory_mb=torch_memory_mb,
            active_jobs=active_jobs,
            pending_jobs=pending_jobs,
            generation_rate=max(0, generation_rate)
        )
    
    def _update_display(self, metrics: PerformanceMetrics):
        """Update dashboard display with new metrics"""
        # Update status labels
        self.status_labels['cpu_status'].config(
            text=f"{metrics.cpu_percent:.1f}%", 
            foreground="red" if metrics.cpu_percent > 80 else "green"
        )
        
        self.status_labels['memory_status'].config(
            text=f"{metrics.memory_percent:.1f}%", 
            foreground="red" if metrics.memory_percent > 80 else "green"
        )
        
        gpu_status = f"{metrics.gpu_utilization:.1f}%" if metrics.gpu_utilization else "N/A"
        self.status_labels['gpu_status'].config(text=gpu_status)
        
        self.status_labels['engine_status'].config(text="Running", foreground="green")
        self.status_labels['queue_status'].config(
            text=f"{metrics.active_jobs} active, {metrics.pending_jobs} pending"
        )
        
        # Update quick metrics
        self.quick_metrics['active_jobs'].config(text=str(metrics.active_jobs))
        self.quick_metrics['pending_jobs'].config(text=str(metrics.pending_jobs))
        
        # Update plots
        self._update_system_plots()
        self._update_performance_plots()
        
        # Refresh canvas
        self.system_canvas.draw()
        self.perf_canvas.draw()
    
    def _update_system_plots(self):
        """Update system resource plots"""
        if not self.metrics_history:
            return
        
        # Extract data for plotting
        timestamps = [m.timestamp for m in self.metrics_history]
        cpu_data = [m.cpu_percent for m in self.metrics_history]
        mem_data = [m.memory_percent for m in self.metrics_history]
        gpu_data = [m.gpu_utilization or 0 for m in self.metrics_history]
        active_jobs = [m.active_jobs for m in self.metrics_history]
        pending_jobs = [m.pending_jobs for m in self.metrics_history]
        
        # Update lines
        time_points = range(len(timestamps))
        self.cpu_line.set_data(time_points, cpu_data)
        self.mem_line.set_data(time_points, mem_data)
        self.gpu_line.set_data(time_points, gpu_data)
        self.active_jobs_line.set_data(time_points, active_jobs)
        self.pending_jobs_line.set_data(time_points, pending_jobs)
        
        # Adjust axes
        for ax in [self.cpu_ax, self.mem_ax, self.gpu_ax, self.jobs_ax]:
            ax.relim()
            ax.autoscale_view()
    
    def _update_performance_plots(self):
        """Update performance plots"""
        if not self.metrics_history:
            return
        
        # Extract data
        timestamps = [m.timestamp for m in self.metrics_history]
        generation_times = []  # Would calculate from actual generation data
        throughput = [m.generation_rate for m in self.metrics_history]
        
        # Simulate generation times
        for i, m in enumerate(self.metrics_history):
            if i == 0:
                gen_time = 5.0
            else:
                prev_time = generation_times[-1] if generation_times else 5.0
                gen_time = max(1.0, prev_time + np.random.normal(0, 0.5))
            generation_times.append(gen_time)
        
        # Update lines
        time_points = range(len(timestamps))
        self.generation_line.set_data(time_points, generation_times)
        self.throughput_line.set_data(time_points, throughput)
        
        # Adjust axes
        for ax in [self.generation_ax, self.throughput_ax]:
            ax.relim()
            ax.autoscale_view()
    
    def _check_alerts(self, metrics: PerformanceMetrics):
        """Check for performance alerts"""
        alerts = []
        
        # CPU alert
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'level': 'WARNING',
                'component': 'CPU',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%'
            })
        
        # Memory alert
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append({
                'level': 'WARNING',
                'component': 'Memory',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%'
            })
        
        # GPU alert
        if metrics.gpu_utilization and metrics.gpu_utilization > self.alert_thresholds['gpu_utilization']:
            alerts.append({
                'level': 'WARNING',
                'component': 'GPU',
                'message': f'High GPU utilization: {metrics.gpu_utilization:.1f}%'
            })
        
        # Add alerts to display
        for alert in alerts:
            self._add_alert(alert)
    
    def _add_alert(self, alert: Dict[str, str]):
        """Add alert to alerts display"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.alerts_tree.insert('', 0, values=(
            timestamp,
            alert['level'],
            alert['component'],
            alert['message']
        ))
        
        # Log alert
        self.logger.warning(f"ALERT [{alert['component']}]: {alert['message']}")
    
    def _clear_alerts(self):
        """Clear all alerts"""
        for item in self.alerts_tree.get_children():
            self.alerts_tree.delete(item)
    
    def _export_alerts(self):
        """Export alerts to file"""
        try:
            export_path = Path("alerts_export.json")
            alerts_data = []
            
            for item in self.alerts_tree.get_children():
                values = self.alerts_tree.item(item)['values']
                alerts_data.append({
                    'timestamp': values[0],
                    'level': values[1],
                    'component': values[2],
                    'message': values[3]
                })
            
            with open(export_path, 'w') as f:
                json.dump(alerts_data, f, indent=2)
            
            self.logger.info(f"✅ Alerts exported to {export_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to export alerts: {e}")
    
    def _clear_logs(self):
        """Clear log display"""
        self.log_text.delete(1.0, tk.END)
    
    def _save_logs(self):
        """Save logs to file"""
        try:
            log_content = self.log_text.get(1.0, tk.END)
            export_path = Path("dashboard_logs.txt")
            
            with open(export_path, 'w') as f:
                f.write(log_content)
            
            self.logger.info(f"✅ Logs saved to {export_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save logs: {e}")
    
    def run(self):
        """Start the dashboard application"""
        self.logger.info("🚀 Starting Performance Dashboard...")
        self.root.mainloop()

# Web-based alternative dashboard
class WebDashboard:
    """Web-based performance dashboard using FastAPI"""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.app = None
        self.setup_web_app()
    
    def setup_web_app(self):
        """Setup FastAPI web application"""
        try:
            from fastapi import FastAPI, WebSocket
            from fastapi.responses import HTMLResponse
            import uvicorn
            
            self.app = FastAPI(title="Secure AI Studio Dashboard")
            
            @self.app.get("/", response_class=HTMLResponse)
            async def get_dashboard():
                return self._get_dashboard_html()
            
            @self.app.websocket("/ws/metrics")
            async def websocket_endpoint(websocket: WebSocket):
                await websocket.accept()
                try:
                    while True:
                        # Send metrics periodically
                        metrics = self._collect_web_metrics()
                        await websocket.send_json(metrics)
                        await asyncio.sleep(1)
                except Exception as e:
                    print(f"WebSocket error: {e}")
            
        except ImportError:
            self.logger.warning("FastAPI not available, web dashboard disabled")
    
    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Secure AI Studio - Performance Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <h1>Secure AI Studio Performance Dashboard</h1>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <canvas id="cpuChart"></canvas>
                <canvas id="memoryChart"></canvas>
                <canvas id="gpuChart"></canvas>
                <canvas id="jobsChart"></canvas>
            </div>
            
            <script>
                // Initialize charts and WebSocket connection
                const cpuChart = new Chart(document.getElementById('cpuChart'), {
                    type: 'line',
                    data: {labels: [], datasets: [{label: 'CPU %', data: []}]},
                    options: {responsive: true}
                });
                
                const ws = new WebSocket('ws://' + window.location.host + '/ws/metrics');
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    // Update charts with new data
                };
            </script>
        </body>
        </html>
        """
    
    def _collect_web_metrics(self) -> Dict[str, Any]:
        """Collect metrics for web dashboard"""
        # Similar to _collect_metrics but returns JSON-serializable data
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'gpu_utilization': 0,  # Simplified
            'active_jobs': 0,
            'pending_jobs': 0
        }
    
    def run_web_server(self):
        """Run web server"""
        if self.app:
            import uvicorn
            uvicorn.run(self.app, host=self.host, port=self.port)

# Example usage
def main():
    """Demo dashboard functionality"""
    print("📊 PERFORMANCE DASHBOARD DEMO")
    print("=" * 35)
    
    print("Starting Tkinter dashboard...")
    print("Close the dashboard window to exit.")
    
    try:
        # Create and run dashboard
        dashboard = PerformanceDashboard()
        dashboard.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
    
    return True

if __name__ == "__main__":
    import asyncio
    success = main()
    exit(0 if success else 1)