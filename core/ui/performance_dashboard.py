#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 SECURE AI STUDIO - Simple Performance Dashboard
Visual interface for monitoring system metrics and generation status

This provides a visual representation of the system's performance metrics
that can be referenced in documentation and README files.
"""

import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime
import threading

class PerformanceDashboard:
    """Simple Tkinter dashboard for system monitoring"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛡️ Secure AI Studio - Performance Dashboard")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Dashboard data
        self.metrics = {
            'cpu_usage': 0,
            'memory_usage': 0,
            'active_generations': 0,
            'completed_today': 0,
            'system_status': 'Running'
        }
        
        self.setup_ui()
        self.start_updates()
    
    def setup_ui(self):
        """Setup dashboard user interface"""
        
        # Header
        header_frame = tk.Frame(self.root, bg='#34495e', height=60)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="🛡️ SECURE AI STUDIO DASHBOARD", 
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#34495e'
        )
        title_label.pack(pady=15)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg='#2c3e50')
        status_frame.pack(fill=tk.X, padx=10)
        
        self.status_label = tk.Label(
            status_frame,
            text=f"Status: {self.metrics['system_status']} | Last Update: {datetime.now().strftime('%H:%M:%S')}",
            font=('Arial', 10),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        self.status_label.pack(pady=5)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg='#2c3e50')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Metrics grid
        metrics_frame = tk.Frame(content_frame, bg='#34495e')
        metrics_frame.pack(fill=tk.BOTH, expand=True)
        
        # CPU Usage
        self.create_metric_widget(
            metrics_frame, "CPU Usage", "cpu_usage", 0, 0, '%'
        )
        
        # Memory Usage
        self.create_metric_widget(
            metrics_frame, "Memory Usage", "memory_usage", 0, 1, '%'
        )
        
        # Active Generations
        self.create_metric_widget(
            metrics_frame, "Active Generations", "active_generations", 1, 0, ''
        )
        
        # Completed Today
        self.create_metric_widget(
            metrics_frame, "Completed Today", "completed_today", 1, 1, ''
        )
        
        # Recent Activity Log
        log_frame = tk.Frame(content_frame, bg='#34495e', height=150)
        log_frame.pack(fill=tk.X, pady=(10, 0))
        log_frame.pack_propagate(False)
        
        log_label = tk.Label(
            log_frame,
            text="📋 RECENT ACTIVITY",
            font=('Arial', 12, 'bold'),
            fg='white',
            bg='#34495e'
        )
        log_label.pack(pady=5)
        
        self.log_text = tk.Text(
            log_frame,
            height=6,
            font=('Courier', 9),
            bg='#2c3e50',
            fg='#ecf0f1',
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Add sample log entries
        self.add_log_entry("System initialized successfully")
        self.add_log_entry("Security protocols activated")
        self.add_log_entry("Monitoring agents started")
    
    def create_metric_widget(self, parent, title, key, row, col, unit):
        """Create a metric display widget"""
        frame = tk.Frame(parent, bg='#2c3e50', relief=tk.RAISED, bd=2)
        frame.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        
        # Configure grid weights
        parent.grid_columnconfigure(col, weight=1)
        parent.grid_rowconfigure(row, weight=1)
        
        # Title
        title_label = tk.Label(
            frame,
            text=title,
            font=('Arial', 11, 'bold'),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        title_label.pack(pady=(10, 5))
        
        # Value display
        value_var = tk.StringVar(value=f"{self.metrics[key]}{unit}")
        self.__dict__[f"{key}_var"] = value_var
        
        value_label = tk.Label(
            frame,
            textvariable=value_var,
            font=('Arial', 18, 'bold'),
            fg='#27ae60' if key != 'active_generations' else '#e74c3c',
            bg='#2c3e50'
        )
        value_label.pack(pady=5)
        
        # Progress bar for percentage metrics
        if unit == '%':
            progress = ttk.Progressbar(
                frame,
                length=150,
                mode='determinate',
                maximum=100
            )
            progress.pack(pady=(0, 10))
            self.__dict__[f"{key}_progress"] = progress
    
    def add_log_entry(self, message):
        """Add entry to activity log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def update_metrics(self):
        """Update dashboard metrics with simulated data"""
        # Simulate changing metrics
        import random
        
        self.metrics['cpu_usage'] = random.randint(45, 85)
        self.metrics['memory_usage'] = random.randint(60, 90)
        self.metrics['active_generations'] = random.randint(0, 3)
        self.metrics['completed_today'] = random.randint(12, 45)
        
        # Update UI elements
        self.cpu_usage_var.set(f"{self.metrics['cpu_usage']}%")
        self.memory_usage_var.set(f"{self.metrics['memory_usage']}%")
        self.active_generations_var.set(str(self.metrics['active_generations']))
        self.completed_today_var.set(str(self.metrics['completed_today']))
        
        # Update progress bars
        self.cpu_usage_progress['value'] = self.metrics['cpu_usage']
        self.memory_usage_progress['value'] = self.metrics['memory_usage']
        
        # Update status
        self.status_label.config(
            text=f"Status: {self.metrics['system_status']} | Last Update: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        # Add log entries occasionally
        if random.random() < 0.3:
            activities = [
                "Content generation completed",
                "Security scan performed",
                "Performance metrics updated",
                "Resource cleanup executed"
            ]
            self.add_log_entry(random.choice(activities))
    
    def start_updates(self):
        """Start periodic updates"""
        def update_loop():
            while True:
                self.root.after(0, self.update_metrics)
                time.sleep(2)  # Update every 2 seconds
        
        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()
    
    def run(self):
        """Start the dashboard"""
        self.root.mainloop()

# Example usage for documentation purposes
def create_dashboard_screenshot():
    """Create a simulated dashboard screenshot for documentation"""
    # This would typically save a screenshot, but for documentation
    # we'll just note that the dashboard exists
    print("📊 Dashboard component ready for visualization")
    print("   - Real-time system metrics monitoring")
    print("   - Activity logging and status tracking")
    print("   - Professional UI for system oversight")

if __name__ == "__main__":
    # Run the dashboard
    dashboard = PerformanceDashboard()
    dashboard.run()