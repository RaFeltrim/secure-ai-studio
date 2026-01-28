#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Message Queue System
Internal queue for managing batch processing and throughput control

Features:
- Priority-based job queuing
- Resource-aware scheduling
- Throughput management
- Batch processing optimization
"""

import queue
import threading
import time
import uuid
import json
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from collections import defaultdict

class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class JobStatus(Enum):
    """Job status states"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class QueueJob:
    """Queue job data structure"""
    job_id: str
    priority: JobPriority
    request_data: Dict[str, Any]
    callback: Optional[Callable] = None
    timeout: int = 300
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.QUEUED
    result: Optional[Dict] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if isinstance(self.priority, str):
            self.priority = JobPriority[self.priority.upper()]

class MessageQueue:
    """
    Advanced message queue system for AI generation jobs
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize message queue system"""
        self.config = config or self._default_config()
        self.logger = self._setup_logging()
        
        # Queue management
        self.queues = {
            JobPriority.LOW: queue.PriorityQueue(),
            JobPriority.NORMAL: queue.PriorityQueue(),
            JobPriority.HIGH: queue.PriorityQueue(),
            JobPriority.CRITICAL: queue.PriorityQueue()
        }
        
        # Job tracking
        self.active_jobs = {}
        self.completed_jobs = {}
        self.job_lock = threading.RLock()
        
        # Worker management
        self.workers = []
        self.worker_count = self.config['worker_threads']
        self.max_batch_size = self.config['max_batch_size']
        
        # Statistics
        self.stats = {
            'jobs_queued': 0,
            'jobs_processed': 0,
            'jobs_failed': 0,
            'total_processing_time': 0.0
        }
        
        # Callbacks
        self.job_completion_callbacks = []
        
        self.logger.info("📨 Message Queue system initialized")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'worker_threads': 4,
            'max_batch_size': 10,
            'queue_timeout': 30,
            'retry_attempts': 3,
            'retry_delay': 5
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('MessageQueue')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def add_job(self, request_data: Dict[str, Any], priority: JobPriority = JobPriority.NORMAL, 
                callback: Optional[Callable] = None, timeout: int = 300) -> str:
        """Add job to queue"""
        job_id = str(uuid.uuid4())
        
        job = QueueJob(
            job_id=job_id,
            priority=priority,
            request_data=request_data,
            callback=callback,
            timeout=timeout
        )
        
        # Add to appropriate priority queue
        # Use negative priority for PriorityQueue (higher priority = lower number)
        self.queues[priority].put((-priority.value, job))
        
        with self.job_lock:
            self.active_jobs[job_id] = job
            self.stats['jobs_queued'] += 1
        
        self.logger.info(f"📥 Job {job_id[:8]} added to {priority.name} queue")
        return job_id
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job"""
        with self.job_lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                if job.status == JobStatus.QUEUED:
                    job.status = JobStatus.CANCELLED
                    job.completed_at = datetime.now()
                    self.logger.info(f"🚫 Job {job_id[:8]} cancelled")
                    return True
        return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status"""
        with self.job_lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                return {
                    'job_id': job.job_id,
                    'status': job.status.value,
                    'priority': job.priority.name,
                    'created_at': job.created_at.isoformat(),
                    'started_at': job.started_at.isoformat() if job.started_at else None,
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                    'result': job.result,
                    'error': job.error
                }
        return None
    
    def start_workers(self):
        """Start worker threads"""
        for i in range(self.worker_count):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"QueueWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        self.logger.info(f"👷 Started {self.worker_count} worker threads")
    
    def stop_workers(self, timeout: float = 5.0):
        """Stop worker threads gracefully"""
        self.logger.info("🛑 Stopping worker threads...")
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=timeout)
        
        self.workers.clear()
        self.logger.info("✅ All workers stopped")
    
    def _worker_loop(self):
        """Main worker processing loop"""
        while True:
            try:
                job = self._get_next_job()
                if job is None:
                    time.sleep(0.1)  # Brief pause before retry
                    continue
                
                self._process_job(job)
                
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
                time.sleep(1)
    
    def _get_next_job(self) -> Optional[QueueJob]:
        """Get next job from highest priority queue"""
        # Check queues in priority order (Critical -> High -> Normal -> Low)
        priority_order = [
            JobPriority.CRITICAL,
            JobPriority.HIGH,
            JobPriority.NORMAL,
            JobPriority.LOW
        ]
        
        for priority in priority_order:
            try:
                _, job = self.queues[priority].get(timeout=self.config['queue_timeout'])
                if job.status == JobStatus.QUEUED:
                    return job
                # Skip cancelled jobs
            except queue.Empty:
                continue
        
        return None
    
    def _process_job(self, job: QueueJob):
        """Process a single job"""
        with self.job_lock:
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now()
        
        self.logger.info(f"⚡ Processing job {job.job_id[:8]} with priority {job.priority.name}")
        
        try:
            # Simulate job processing
            # In real implementation, this would call the AI engine
            processing_result = self._execute_job(job.request_data)
            
            # Record completion
            with self.job_lock:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.result = processing_result
                self.stats['jobs_processed'] += 1
                self.stats['total_processing_time'] += (
                    job.completed_at - job.started_at
                ).total_seconds()
            
            # Execute callback if provided
            if job.callback:
                try:
                    job.callback(job.job_id, processing_result)
                except Exception as e:
                    self.logger.error(f"Callback error for job {job.job_id[:8]}: {e}")
            
            # Trigger completion callbacks
            self._trigger_completion_callbacks(job)
            
            self.logger.info(f"✅ Job {job.job_id[:8]} completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Job {job.job_id[:8]} failed: {e}")
            
            with self.job_lock:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
                job.error = str(e)
                self.stats['jobs_failed'] += 1
    
    def _execute_job(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute job (placeholder for actual AI processing)"""
        # Simulate processing time based on complexity
        content_type = request_data.get('content_type', 'image')
        batch_size = request_data.get('batch_size', 1)
        
        # Simulate processing delay
        if content_type == 'image':
            base_time = 2.0
        else:  # video
            base_time = 10.0
        
        processing_time = base_time * batch_size * (0.8 + 0.4 * (batch_size / 10))
        time.sleep(min(processing_time, 30))  # Cap at 30 seconds for demo
        
        # Return simulated result
        return {
            'success': True,
            'output_count': batch_size,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat()
        }
    
    def _trigger_completion_callbacks(self, job: QueueJob):
        """Trigger registered completion callbacks"""
        for callback in self.job_completion_callbacks:
            try:
                callback({
                    'job_id': job.job_id,
                    'status': job.status.value,
                    'result': job.result,
                    'error': job.error,
                    'processing_time': (
                        job.completed_at - job.started_at
                    ).total_seconds() if job.completed_at and job.started_at else 0
                })
            except Exception as e:
                self.logger.error(f"Completion callback error: {e}")
    
    def add_completion_callback(self, callback: Callable[[Dict], None]):
        """Add callback for job completion"""
        self.job_completion_callbacks.append(callback)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        queue_sizes = {}
        total_queued = 0
        
        for priority, q in self.queues.items():
            # Approximate queue size (PriorityQueue doesn't have qsize())
            queue_sizes[priority.name] = q.qsize() if hasattr(q, 'qsize') else 'unknown'
            if isinstance(queue_sizes[priority.name], int):
                total_queued += queue_sizes[priority.name]
        
        with self.job_lock:
            active_count = len([j for j in self.active_jobs.values() 
                              if j.status in [JobStatus.QUEUED, JobStatus.PROCESSING]])
            completed_count = len(self.completed_jobs)
        
        return {
            'queue_sizes': queue_sizes,
            'total_queued': total_queued,
            'active_jobs': active_count,
            'completed_jobs': completed_count,
            'worker_count': self.worker_count,
            'statistics': self.stats.copy()
        }
    
    def process_batch(self, requests: List[Dict[str, Any]], 
                     priority: JobPriority = JobPriority.NORMAL) -> List[str]:
        """Process batch of requests"""
        job_ids = []
        
        # Add all requests to queue
        for request in requests:
            job_id = self.add_job(request, priority)
            job_ids.append(job_id)
        
        self.logger.info(f"📦 Added batch of {len(requests)} jobs with priority {priority.name}")
        return job_ids
    
    def wait_for_completion(self, job_ids: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Wait for specified jobs to complete"""
        start_time = time.time()
        remaining_jobs = set(job_ids)
        
        while remaining_jobs and (time.time() - start_time) < timeout:
            completed_jobs = set()
            
            for job_id in remaining_jobs:
                status = self.get_job_status(job_id)
                if status and status['status'] in ['completed', 'failed', 'cancelled']:
                    completed_jobs.add(job_id)
            
            remaining_jobs -= completed_jobs
            
            if remaining_jobs:
                time.sleep(1)  # Check every second
        
        # Return results for all jobs
        results = {}
        for job_id in job_ids:
            status = self.get_job_status(job_id)
            results[job_id] = status
        
        return results

class BatchProcessor:
    """Batch processing coordinator"""
    
    def __init__(self, message_queue: MessageQueue):
        self.queue = message_queue
        self.logger = logging.getLogger('BatchProcessor')
    
    def process_batch_with_feedback(self, requests: List[Dict[str, Any]], 
                                  priority: JobPriority = JobPriority.NORMAL,
                                  progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process batch with progress feedback"""
        total_jobs = len(requests)
        completed_jobs = 0
        
        def job_completion_handler(result):
            nonlocal completed_jobs
            completed_jobs += 1
            if progress_callback:
                progress_callback(completed_jobs, total_jobs, result)
        
        # Add completion callback
        self.queue.add_completion_callback(job_completion_handler)
        
        # Process batch
        job_ids = self.queue.process_batch(requests, priority)
        
        # Wait for completion
        results = self.queue.wait_for_completion(job_ids)
        
        return {
            'job_ids': job_ids,
            'results': results,
            'completion_rate': completed_jobs / total_jobs if total_jobs > 0 else 0
        }

# Example usage and testing
def main():
    """Demo usage of the message queue system"""
    print("📨 MESSAGE QUEUE DEMO")
    print("=" * 30)
    
    # Initialize queue
    mq = MessageQueue({
        'worker_threads': 2,
        'max_batch_size': 5
    })
    
    # Add completion callback
    def on_job_complete(job_info):
        print(f"✅ Job {job_info['job_id'][:8]} completed: {job_info['status']}")
    
    mq.add_completion_callback(on_job_complete)
    
    # Start workers
    mq.start_workers()
    
    try:
        # Add some test jobs
        jobs = []
        for i in range(8):
            priority = JobPriority.HIGH if i < 2 else JobPriority.NORMAL
            job_data = {
                'content_type': 'image',
                'prompt': f'Test image {i}',
                'dimensions': (512, 512),
                'batch_size': 1
            }
            job_id = mq.add_job(job_data, priority)
            jobs.append(job_id)
            print(f"Added job {job_id[:8]} with {priority.name} priority")
        
        # Wait a bit and show stats
        time.sleep(2)
        stats = mq.get_queue_stats()
        print(f"\n📊 Queue Stats: {stats}")
        
        # Wait for completion
        print("\n⏳ Waiting for jobs to complete...")
        results = mq.wait_for_completion(jobs, timeout=60)
        
        # Show final results
        completed = sum(1 for r in results.values() if r and r['status'] == 'completed')
        print(f"\n🏁 Final Results: {completed}/{len(jobs)} jobs completed")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        mq.stop_workers()
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)