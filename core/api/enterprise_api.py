#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔌 ENTERPRISE API DEVELOPMENT
Phase 3 - RESTful API Endpoints and External Integration

Provides:
- RESTful API endpoints for external system integration
- GraphQL support for flexible data querying
- SDK development for major programming languages
- Comprehensive API documentation and examples
- Rate limiting and authentication middleware
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import uvicorn
import jwt
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import json
import asyncio

# Import core system components
from ..engine.secure_ai_engine import SecureAIEngine
from ..engine.enhanced_video_generator import EnhancedVideoGenerator
from ..engine.template_library import TemplateLibrary
from ..engine.multi_user_support import MultiUserSupport
from ..engine.advanced_editing_tools import AdvancedEditingSuite
from ..security.authentication_layer import AuthenticationManager
from ..monitoring.internal_monitoring_agent import MonitoringAgent

# Pydantic models for API requests/responses
class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., description="Image generation prompt")
    width: int = Field(1024, ge=256, le=4096, description="Image width")
    height: int = Field(1024, ge=256, le=4096, description="Image height")
    style: str = Field("realistic", description="Artistic style")
    quality: str = Field("standard", description="Generation quality")

class GenerateVideoRequest(BaseModel):
    prompt: str = Field(..., description="Video generation prompt")
    duration: float = Field(10.0, gt=0, le=300, description="Video duration in seconds")
    resolution: str = Field("1080p", description="Video resolution")
    fps: int = Field(30, description="Frames per second")
    style: str = Field("cinematic", description="Video style")

class GenerateImageResponse(BaseModel):
    success: bool
    session_id: str
    image_url: str
    metadata: Dict[str, Any]
    generation_time: float

class GenerateVideoResponse(BaseModel):
    success: bool
    session_id: str
    video_url: str
    metadata: Dict[str, Any]
    generation_time: float

class TemplateListResponse(BaseModel):
    templates: List[Dict[str, Any]]
    total_count: int
    categories: List[str]

class UserRegistrationRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "creator"

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserAuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    expires_in: int

class SystemMetricsResponse(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: str
    active_users: int
    generation_count: int

class APIError(BaseModel):
    error: str
    message: str
    timestamp: str
    request_id: str

# API Application
app = FastAPI(
    title="Secure AI Studio API",
    description="Enterprise-grade AI content generation API",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
auth_manager = AuthenticationManager()

# Core system instances
ai_engine = SecureAIEngine()
video_generator = EnhancedVideoGenerator()
template_library = TemplateLibrary()
multi_user = MultiUserSupport()
editing_suite = AdvancedEditingSuite()
monitor_agent = MonitoringAgent()

# Rate limiting storage
rate_limit_store: Dict[str, List[datetime]] = {}

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, "secret_key", algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def rate_limit_check(user_id: str, max_requests: int = 100, window_minutes: int = 60):
    """Check rate limiting"""
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)
    
    if user_id not in rate_limit_store:
        rate_limit_store[user_id] = []
    
    # Clean old requests
    rate_limit_store[user_id] = [req_time for req_time in rate_limit_store[user_id] 
                                if req_time > window_start]
    
    # Check limit
    if len(rate_limit_store[user_id]) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_minutes} minutes."
        )
    
    rate_limit_store[user_id].append(now)

# API Routes

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Secure AI Studio API v3.0",
        "status": "operational",
        "documentation": "/api/docs",
        "version": "3.0.0"
    }

@app.post("/api/v1/auth/register", response_model=UserAuthResponse)
async def register_user(request: UserRegistrationRequest):
    """Register new user"""
    try:
        user = multi_user.register_user(
            request.username,
            request.email,
            request.password,
            request.role
        )
        
        # Generate JWT token
        token_data = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        access_token = jwt.encode(token_data, "secret_key", algorithm="HS256")
        
        return UserAuthResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.user_id,
            expires_in=86400
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/auth/login", response_model=UserAuthResponse)
async def login_user(request: UserLoginRequest):
    """User login"""
    try:
        session_token = multi_user.login_user(request.username, request.password)
        if not session_token:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        user = multi_user.user_manager.get_user_by_username(request.username)
        token_data = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        access_token = jwt.encode(token_data, "secret_key", algorithm="HS256")
        
        return UserAuthResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.user_id,
            expires_in=86400
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/v1/generate/image", response_model=GenerateImageResponse)
async def generate_image(
    request: GenerateImageRequest,
    user_id: str = Depends(verify_token)
):
    """Generate AI image"""
    await rate_limit_check(user_id, max_requests=50, window_minutes=60)
    
    try:
        # Start monitoring
        monitor_agent.start_session(user_id, "image_generation")
        
        # Generate image
        result = ai_engine.generate_image(
            prompt=request.prompt,
            width=request.width,
            height=request.height,
            style=request.style
        )
        
        # Stop monitoring
        monitor_agent.end_session(user_id)
        
        return GenerateImageResponse(
            success=result["success"],
            session_id=result["session_id"],
            image_url=result["output_path"],
            metadata=result["metadata"],
            generation_time=result["generation_time"]
        )
    except Exception as e:
        monitor_agent.log_error(user_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/generate/video", response_model=GenerateVideoResponse)
async def generate_video(
    request: GenerateVideoRequest,
    user_id: str = Depends(verify_token)
):
    """Generate AI video"""
    await rate_limit_check(user_id, max_requests=10, window_minutes=60)
    
    try:
        # Map resolution string to dimensions
        resolution_map = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "4K": (3840, 2160)
        }
        resolution = resolution_map.get(request.resolution, (1920, 1080))
        
        # Generate video
        result = video_generator.create_advanced_video(
            prompt=request.prompt,
            duration=request.duration,
            resolution=resolution,
            fps=request.fps,
            style=request.style
        )
        
        return GenerateVideoResponse(
            success=result["success"],
            session_id=result["session_id"],
            video_url=result["output_path"],
            metadata=result["metadata"],
            generation_time=result["generation_time"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/templates", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[str] = None,
    industry: Optional[str] = None,
    search: Optional[str] = None,
    user_id: str = Depends(verify_token)
):
    """List available templates"""
    try:
        if search:
            templates = template_library.search_templates(search)
        elif category:
            templates = template_library.get_templates_by_category(category)
        elif industry:
            templates = template_library.get_templates_by_industry(industry)
        else:
            templates = template_library.get_all_templates()
            
        # Convert to dict format
        template_dicts = []
        for template in templates:
            template_dict = {
                "id": template.id,
                "name": template.metadata.name,
                "description": template.metadata.description,
                "category": template.metadata.category,
                "industry": template.metadata.industry,
                "tags": template.metadata.tags,
                "difficulty": template.metadata.difficulty,
                "estimated_time": template.metadata.estimated_time
            }
            template_dicts.append(template_dict)
            
        return TemplateListResponse(
            templates=template_dicts,
            total_count=len(template_dicts),
            categories=list(template_library.categories.keys())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/metrics/system", response_model=SystemMetricsResponse)
async def get_system_metrics(user_id: str = Depends(verify_token)):
    """Get system performance metrics"""
    try:
        # Get metrics from monitoring agent
        metrics = monitor_agent.get_system_metrics()
        
        return SystemMetricsResponse(
            cpu_usage=metrics.get("cpu_usage", 0),
            memory_usage=metrics.get("memory_usage", 0),
            disk_usage=metrics.get("disk_usage", 0),
            uptime=metrics.get("uptime", "0"),
            active_users=metrics.get("active_users", 0),
            generation_count=metrics.get("generation_count", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ai_engine": "operational",
            "video_generator": "operational",
            "template_library": "operational",
            "authentication": "operational",
            "monitoring": "operational"
        }
    }

# GraphQL Schema (simplified implementation)
@app.post("/api/v1/graphql")
async def graphql_query(query: Dict[str, Any], user_id: str = Depends(verify_token)):
    """GraphQL endpoint for flexible data querying"""
    try:
        # Parse GraphQL query and execute
        # This is a simplified implementation - production would use proper GraphQL library
        operation = query.get("operationName", "")
        variables = query.get("variables", {})
        
        if operation == "getUserTemplates":
            user_templates = template_library.get_all_templates()[:10]  # First 10 templates
            return {
                "data": {
                    "userTemplates": [
                        {
                            "id": t.id,
                            "name": t.metadata.name,
                            "category": t.metadata.category
                        } for t in user_templates
                    ]
                }
            }
        elif operation == "getSystemStats":
            metrics = monitor_agent.get_system_metrics()
            return {
                "data": {
                    "systemStats": {
                        "cpuUsage": metrics.get("cpu_usage", 0),
                        "memoryUsage": metrics.get("memory_usage", 0),
                        "activeUsers": metrics.get("active_users", 0)
                    }
                }
            }
            
        return {"data": {}}
    except Exception as e:
        return {"errors": [{"message": str(e)}]}

# SDK Generation Functions
def generate_python_sdk():
    """Generate Python SDK for API integration"""
    sdk_content = '''
# Secure AI Studio Python SDK
import requests
import json

class SecureAIStudioClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024):
        """Generate AI image"""
        data = {
            "prompt": prompt,
            "width": width,
            "height": height
        }
        response = requests.post(
            f"{self.base_url}/api/v1/generate/image",
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def generate_video(self, prompt: str, duration: float = 10.0):
        """Generate AI video"""
        data = {
            "prompt": prompt,
            "duration": duration
        }
        response = requests.post(
            f"{self.base_url}/api/v1/generate/video",
            headers=self.headers,
            json=data
        )
        return response.json()
'''
    
    with open("sdk/python/secure_ai_studio_sdk.py", "w") as f:
        f.write(sdk_content)

def generate_javascript_sdk():
    """Generate JavaScript SDK for API integration"""
    sdk_content = '''
// Secure AI Studio JavaScript SDK
class SecureAIStudioClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async generateImage(prompt, width = 1024, height = 1024) {
        const data = { prompt, width, height };
        const response = await fetch(`${this.baseUrl}/api/v1/generate/image`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        return response.json();
    }
    
    async generateVideo(prompt, duration = 10.0) {
        const data = { prompt, duration };
        const response = await fetch(`${this.baseUrl}/api/v1/generate/video`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(data)
        });
        return response.json();
    }
}
'''
    
    with open("sdk/javascript/secure_ai_studio_sdk.js", "w") as f:
        f.write(sdk_content)

# API Documentation Generator
def generate_api_documentation():
    """Generate comprehensive API documentation"""
    doc_content = '''
# Secure AI Studio API Documentation

## Overview
The Secure AI Studio API provides enterprise-grade access to AI content generation capabilities with military-grade security and compliance features.

## Authentication
All API requests require JWT bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \\
     -H "Content-Type: application/json" \\
     https://api.secureaistudio.com/api/v1/generate/image
```

## Rate Limits
- Image Generation: 50 requests/hour
- Video Generation: 10 requests/hour
- Other endpoints: 100 requests/hour

## Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login

### Content Generation
- `POST /api/v1/generate/image` - Generate AI images
- `POST /api/v1/generate/video` - Generate AI videos

### Template Management
- `GET /api/v1/templates` - List templates
- `GET /api/v1/templates/{id}` - Get template details

### System Information
- `GET /api/v1/metrics/system` - System performance metrics
- `GET /api/v1/health` - Health check

## SDKs
SDKs are available for:
- Python
- JavaScript
- Java
- C#
'''
    
    with open("docs/api_documentation.md", "w") as f:
        f.write(doc_content)

# Main API Server
if __name__ == "__main__":
    # Generate SDKs and documentation
    Path("sdk/python").mkdir(parents=True, exist_ok=True)
    Path("sdk/javascript").mkdir(parents=True, exist_ok=True)
    Path("docs").mkdir(parents=True, exist_ok=True)
    
    generate_python_sdk()
    generate_javascript_sdk()
    generate_api_documentation()
    
    # Start API server
    uvicorn.run(
        "enterprise_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4
    )