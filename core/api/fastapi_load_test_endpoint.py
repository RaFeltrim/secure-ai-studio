#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - FastAPI Load Testing Endpoint
API for k6 stress testing with performance metrics

Features:
- RESTful API for content generation
- Performance monitoring endpoints
- Stress testing capabilities
- Real-time metrics exposure
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import time
import uuid
import json
import logging
from datetime import datetime
import psutil
import GPUtil

# Import our existing components
from core.engine.secure_ai_engine import SecureAIEngine, GenerationRequest
from core.engine.input_validator import InputValidator
from core.monitoring.internal_monitoring_agent import MonitoringAgent

app = FastAPI(
    title="Secure AI Studio API",
    description="Enterprise-grade AI content generation API with performance monitoring",
    version="1.0.0"
)

# Global components
engine = None
validator = None
monitor = None

# Request/Response Models
class GenerationRequestModel(BaseModel):
    content_type: str
    prompt: str
    dimensions: tuple[int, int]
    format: str
    quality: str = "HIGH"
    batch_size: int = 1
    style: Optional[str] = None
    priority: str = "normal"  # low, normal, high
    timeout: int = 300

class GenerationResponse(BaseModel):
    success: bool
    job_id: str
    output_paths: List[str]
    processing_time: float
    resource_usage: Optional[Dict[str, Any]]
    error_message: Optional[str]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    system_metrics: Dict[str, Any]
    api_version: str

class PerformanceMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    gpu_utilization: Optional[float]
    active_jobs: int
    queue_size: int
    avg_response_time: float

# Initialize components
@app.on_event("startup")
async def startup_event():
    global engine, validator, monitor
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("API")
    
    try:
        # Initialize components
        engine = SecureAIEngine()
        validator = InputValidator()
        monitor = MonitoringAgent()
        
        # Start monitoring
        monitor.start_hardware_monitoring(interval=2.0)
        
        logger.info("✅ API components initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize API components: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    if monitor:
        monitor.stop_hardware_monitoring()

# API Endpoints

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "🛡️ Secure AI Studio API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    try:
        # Collect system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        gpu_utilization = None
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_utilization = gpus[0].load * 100
        except:
            pass
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            system_metrics={
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "gpu_utilization": gpu_utilization
            },
            api_version="1.0.0"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/metrics/performance", response_model=PerformanceMetrics)
async def get_performance_metrics():
    """Get current performance metrics for monitoring"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        gpu_utilization = None
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_utilization = gpus[0].load * 100
        except:
            pass
        
        # Get queue and job information (simulated)
        active_jobs = len(monitor.get_current_sessions()) if monitor else 0
        queue_size = 0  # Would integrate with actual queue system
        
        # Calculate average response time from recent sessions
        avg_response_time = 0.0
        if monitor and monitor.completed_sessions:
            recent_sessions = monitor.completed_sessions[-10:]  # Last 10 sessions
            if recent_sessions:
                avg_response_time = sum(s.total_duration for s in recent_sessions) / len(recent_sessions)
        
        return PerformanceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            gpu_utilization=gpu_utilization,
            active_jobs=active_jobs,
            queue_size=queue_size,
            avg_response_time=avg_response_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect metrics: {str(e)}")

@app.post("/generate", response_model=GenerationResponse)
async def generate_content(request: GenerationRequestModel, background_tasks: BackgroundTasks):
    """Main content generation endpoint"""
    start_time = time.time()
    
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Validate request
        if validator:
            validation_result = validator.validate_generation_request(request.dict())
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid request: {[e[1] for e in validation_result.errors]}"
                )
        
        # Start monitoring session
        if monitor:
            monitor.start_session(job_id, request.dict())
            step_timer = monitor.start_step(job_id, "api_request_processing")
        
        # Convert to engine request format
        engine_request = GenerationRequest(
            content_type=request.content_type,
            prompt=request.prompt,
            dimensions=request.dimensions,
            format=request.format,
            quality=request.quality,
            batch_size=request.batch_size,
            style=request.style
        )
        
        # End preprocessing step
        if monitor:
            monitor.end_step(job_id, "api_request_processing", step_timer)
        
        # Generate content
        if monitor:
            step_timer = monitor.start_step(job_id, "ai_generation")
        
        result = engine.generate_content(engine_request)
        
        if monitor:
            monitor.end_step(job_id, "ai_generation", step_timer)
        
        # Add output files to monitoring
        if monitor and result.success:
            for path in result.output_paths:
                monitor.add_output_file(job_id, path)
        
        # Calculate total processing time
        processing_time = time.time() - start_time
        
        # End monitoring session
        if monitor:
            session_record = monitor.end_session(job_id, result.success)
        
        # Prepare response
        response = GenerationResponse(
            success=result.success,
            job_id=job_id,
            output_paths=result.output_paths,
            processing_time=processing_time,
            resource_usage=result.resource_usage,
            error_message=result.error_message
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        if monitor:
            monitor.end_session(job_id if 'job_id' in locals() else 'unknown', success=False)
        
        raise HTTPException(
            status_code=500, 
            detail=f"Generation failed: {str(e)}"
        )

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific generation job"""
    if not monitor:
        raise HTTPException(status_code=501, detail="Monitoring not available")
    
    # Check active sessions
    active_sessions = monitor.get_current_sessions()
    if job_id in active_sessions:
        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Job is currently being processed"
        }
    
    # Check completed sessions
    completed_session = None
    for session in monitor.completed_sessions:
        if session.session_id == job_id:
            completed_session = session
            break
    
    if completed_session:
        return {
            "job_id": job_id,
            "status": "completed" if completed_session.success else "failed",
            "total_duration": completed_session.total_duration,
            "steps": len(completed_session.steps),
            "output_files": completed_session.output_files,
            "success": completed_session.success
        }
    
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/system/status")
async def get_system_status():
    """Get comprehensive system status"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        status = engine.get_system_status()
        
        # Add performance metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        status.update({
            "performance": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3)
            },
            "monitoring": {
                "active_sessions": len(monitor.get_current_sessions()) if monitor else 0,
                "completed_sessions": monitor.get_completed_sessions_count() if monitor else 0
            }
        })
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@app.get("/metrics/hardware-history")
async def get_hardware_history(format: str = "json"):
    """Get historical hardware metrics"""
    if not monitor:
        raise HTTPException(status_code=501, detail="Monitoring not available")
    
    try:
        export_path = monitor.export_hardware_metrics(format)
        return {
            "export_path": export_path,
            "format": format,
            "message": "Metrics exported successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export metrics: {str(e)}")

@app.get("/stress-test/config")
async def get_stress_test_config():
    """Get configuration for k6 stress testing"""
    return {
        "endpoints": {
            "health": "/health",
            "generate": "/generate",
            "metrics": "/metrics/performance",
            "system_status": "/system/status"
        },
        "test_scenarios": {
            "basic_load": {
                "virtual_users": 10,
                "duration": "2m",
                "target_rps": 5
            },
            "stress_test": {
                "virtual_users": 50,
                "duration": "5m",
                "target_rps": 20
            },
            "spike_test": {
                "virtual_users": 100,
                "duration": "1m",
                "target_rps": 50
            }
        },
        "sample_payload": {
            "content_type": "image",
            "prompt": "Test image for load testing",
            "dimensions": [512, 512],
            "format": "PNG",
            "quality": "HIGH",
            "batch_size": 1
        }
    }

# k6 Test Scripts Generator
@app.get("/k6-script/basic")
async def generate_basic_k6_script():
    """Generate basic k6 load test script"""
    script = '''
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '2m',
  thresholds: {
    http_req_duration: ['p(95)<5000'],  // 95% of requests should be below 5s
    http_req_failed: ['rate<0.01'],    // Error rate should be less than 1%
  },
};

const BASE_URL = 'http://localhost:8000';

export default function () {
  // Health check
  const health_res = http.get(`${BASE_URL}/health`);
  check(health_res, {
    'health status is 200': (r) => r.status === 200,
  });

  // Content generation request
  const payload = JSON.stringify({
    content_type: 'image',
    prompt: 'Test image generation',
    dimensions: [512, 512],
    format: 'PNG',
    quality: 'HIGH',
    batch_size: 1
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const gen_res = http.post(`${BASE_URL}/generate`, payload, params);
  check(gen_res, {
    'generation status is 200': (r) => r.status === 200,
    'response time < 30s': (r) => r.timings.duration < 30000,
  });

  sleep(1);
}
'''
    return {"script": script}

@app.get("/k6-script/stress")
async def generate_stress_k6_script():
    """Generate stress test k6 script"""
    script = '''
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Gauge, Rate, Trend } from 'k6/metrics';

// Custom metrics
const generationTime = new Trend('generation_time');
const activeJobs = new Gauge('active_jobs');
const errorRate = new Rate('error_rate');

export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Ramp up to 10 users
    { duration: '3m', target: 50 },   // Stay at 50 users
    { duration: '1m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<30000'],  // 95% under 30s
    http_req_failed: ['rate<0.05'],      // Less than 5% errors
    generation_time: ['p(90)<25000'],    // 90% under 25s
    error_rate: ['rate<0.05'],           // Error rate under 5%
  },
};

const BASE_URL = 'http://localhost:8000';

export default function () {
  group('Health Check', function () {
    const health_res = http.get(`${BASE_URL}/health`);
    check(health_res, {
      'health check passes': (r) => r.status === 200,
    });
  });

  group('Content Generation', function () {
    const payloads = [
      {
        content_type: 'image',
        prompt: 'Simple landscape',
        dimensions: [256, 256],
        format: 'PNG',
      },
      {
        content_type: 'image',
        prompt: 'Complex scene',
        dimensions: [512, 512],
        format: 'PNG',
      }
    ];

    const payload = payloads[Math.floor(Math.random() * payloads.length)];
    payload.batch_size = Math.floor(Math.random() * 3) + 1; // 1-3 batch size

    const start_time = new Date().getTime();
    
    const res = http.post(
      `${BASE_URL}/generate`,
      JSON.stringify(payload),
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: '60s',
      }
    );

    const duration = new Date().getTime() - start_time;
    generationTime.add(duration);

    const success = check(res, {
      'generation succeeds': (r) => r.status === 200,
      'response time < 60s': () => duration < 60000,
      'has output files': (r) => {
        if (r.status === 200) {
          const body = JSON.parse(r.body);
          return body.output_paths && body.output_paths.length > 0;
        }
        return false;
      },
    });

    errorRate.add(!success);
    
    // Check system metrics
    const metrics_res = http.get(`${BASE_URL}/metrics/performance`);
    if (metrics_res.status === 200) {
      const metrics = JSON.parse(metrics_res.body);
      activeJobs.add(metrics.active_jobs);
    }
  });

  sleep(Math.random() * 2 + 0.5); // Random sleep between 0.5-2.5s
}
'''
    return {"script": script}

# Example usage
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")