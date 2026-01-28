#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📚 TEMPLATE LIBRARY MANAGER
Phase 2 - Comprehensive Content Template System

Provides:
- Pre-built content templates for various industries
- Template categorization and tagging
- Custom template creation and management
- Template version control
- Industry-specific template collections
"""

import json
import os
import yaml
import uuid
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import hashlib
from dataclasses import dataclass, asdict

@dataclass
class TemplateMetadata:
    """Metadata for content templates"""
    template_id: str
    name: str
    description: str
    category: str
    industry: str
    version: str
    author: str
    created_date: str
    last_modified: str
    tags: List[str]
    difficulty: str  # beginner, intermediate, advanced
    estimated_time: int  # minutes
    required_skills: List[str]
    preview_image: Optional[str] = None
    dependencies: List[str] = None

class Template:
    """Represents a content template"""
    
    def __init__(self, metadata: TemplateMetadata, content: Dict[str, Any]):
        self.metadata = metadata
        self.content = content
        self.id = metadata.template_id
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary format"""
        return {
            'metadata': asdict(self.metadata),
            'content': self.content
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """Create template from dictionary"""
        metadata = TemplateMetadata(**data['metadata'])
        return cls(metadata, data['content'])

class TemplateLibrary:
    """Manages comprehensive template library"""
    
    def __init__(self, library_path: str = "templates"):
        self.library_path = Path(library_path)
        self.library_path.mkdir(parents=True, exist_ok=True)
        
        # Template categories
        self.categories = {
            'marketing': 'Marketing and Advertising',
            'corporate': 'Corporate Communications',
            'education': 'Educational Content',
            'entertainment': 'Entertainment and Media',
            'technical': 'Technical Documentation',
            'creative': 'Creative Projects',
            'business': 'Business Presentations',
            'social_media': 'Social Media Content'
        }
        
        # Industry sectors
        self.industries = {
            'technology': 'Technology and Software',
            'finance': 'Financial Services',
            'healthcare': 'Healthcare and Medical',
            'retail': 'Retail and E-commerce',
            'manufacturing': 'Manufacturing',
            'education': 'Education and Training',
            'government': 'Government and Public Sector',
            'media': 'Media and Entertainment',
            'real_estate': 'Real Estate',
            'automotive': 'Automotive'
        }
        
        # Initialize template collections
        self._initialize_template_collections()
        
    def _initialize_template_collections(self):
        """Initialize template collections structure"""
        
        # Create category directories
        for category_key, category_name in self.categories.items():
            category_dir = self.library_path / category_key
            category_dir.mkdir(exist_ok=True)
            
            # Create industry subdirectories
            for industry_key, industry_name in self.industries.items():
                industry_dir = category_dir / industry_key
                industry_dir.mkdir(exist_ok=True)
                
        # Create special directories
        (self.library_path / "favorites").mkdir(exist_ok=True)
        (self.library_path / "recent").mkdir(exist_ok=True)
        (self.library_path / "custom").mkdir(exist_ok=True)
        
    def create_template(self, 
                       name: str,
                       description: str,
                       category: str,
                       industry: str,
                       content: Dict[str, Any],
                       tags: List[str] = None,
                       difficulty: str = "intermediate",
                       estimated_time: int = 30) -> Template:
        """Create a new template"""
        
        if category not in self.categories:
            raise ValueError(f"Invalid category: {category}")
            
        if industry not in self.industries:
            raise ValueError(f"Invalid industry: {industry}")
            
        # Generate template ID
        template_id = str(uuid.uuid4())
        
        # Create metadata
        metadata = TemplateMetadata(
            template_id=template_id,
            name=name,
            description=description,
            category=category,
            industry=industry,
            version="1.0.0",
            author="Secure AI Studio",
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            tags=tags or [],
            difficulty=difficulty,
            estimated_time=estimated_time,
            required_skills=self._determine_required_skills(category, industry),
            dependencies=[]
        )
        
        # Create template
        template = Template(metadata, content)
        
        # Save template
        self.save_template(template)
        
        return template
        
    def save_template(self, template: Template):
        """Save template to library"""
        
        # Determine save path
        category_dir = self.library_path / template.metadata.category
        industry_dir = category_dir / template.metadata.industry
        template_file = industry_dir / f"{template.id}.json"
        
        # Save template data
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)
            
        # Update recent templates
        self._update_recent_templates(template.id)
        
    def load_template(self, template_id: str) -> Optional[Template]:
        """Load template by ID"""
        
        # Search all directories for template
        for root, dirs, files in os.walk(self.library_path):
            for file in files:
                if file == f"{template_id}.json":
                    template_path = Path(root) / file
                    
                    with open(template_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return Template.from_dict(data)
                        
        return None
        
    def get_templates_by_category(self, category: str) -> List[Template]:
        """Get all templates in a category"""
        
        if category not in self.categories:
            raise ValueError(f"Invalid category: {category}")
            
        templates = []
        category_dir = self.library_path / category
        
        for root, dirs, files in os.walk(category_dir):
            for file in files:
                if file.endswith('.json'):
                    template_path = Path(root) / file
                    
                    with open(template_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        templates.append(Template.from_dict(data))
                        
        return templates
        
    def get_templates_by_industry(self, industry: str) -> List[Template]:
        """Get all templates for an industry"""
        
        if industry not in self.industries:
            raise ValueError(f"Invalid industry: {industry}")
            
        templates = []
        
        for category_dir in self.library_path.iterdir():
            if category_dir.is_dir() and category_dir.name != "favorites" and category_dir.name != "recent":
                industry_dir = category_dir / industry
                if industry_dir.exists():
                    for template_file in industry_dir.glob("*.json"):
                        with open(template_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            templates.append(Template.from_dict(data))
                            
        return templates
        
    def search_templates(self, query: str, filters: Dict[str, Any] = None) -> List[Template]:
        """Search templates by query and filters"""
        
        all_templates = self.get_all_templates()
        results = []
        
        query_lower = query.lower()
        
        for template in all_templates:
            # Check name and description
            if (query_lower in template.metadata.name.lower() or
                query_lower in template.metadata.description.lower() or
                any(query_lower in tag.lower() for tag in template.metadata.tags)):
                
                # Apply filters
                if filters and not self._matches_filters(template, filters):
                    continue
                    
                results.append(template)
                
        return results
        
    def get_all_templates(self) -> List[Template]:
        """Get all templates in library"""
        
        templates = []
        
        for root, dirs, files in os.walk(self.library_path):
            # Skip special directories for this operation
            if 'favorites' in root or 'recent' in root:
                continue
                
            for file in files:
                if file.endswith('.json'):
                    template_path = Path(root) / file
                    
                    with open(template_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        templates.append(Template.from_dict(data))
                        
        return templates
        
    def add_to_favorites(self, template_id: str):
        """Add template to favorites"""
        
        favorites_file = self.library_path / "favorites" / "favorites.json"
        
        # Load existing favorites
        if favorites_file.exists():
            with open(favorites_file, 'r') as f:
                favorites = json.load(f)
        else:
            favorites = []
            
        # Add template if not already favorited
        if template_id not in favorites:
            favorites.append(template_id)
            
            # Save updated favorites
            with open(favorites_file, 'w') as f:
                json.dump(favorites, f, indent=2)
                
    def get_favorite_templates(self) -> List[Template]:
        """Get favorite templates"""
        
        favorites_file = self.library_path / "favorites" / "favorites.json"
        
        if not favorites_file.exists():
            return []
            
        with open(favorites_file, 'r') as f:
            favorite_ids = json.load(f)
            
        templates = []
        for template_id in favorite_ids:
            template = self.load_template(template_id)
            if template:
                templates.append(template)
                
        return templates
        
    def create_industry_template_pack(self, industry: str) -> List[Template]:
        """Create comprehensive template pack for an industry"""
        
        if industry not in self.industries:
            raise ValueError(f"Invalid industry: {industry}")
            
        templates = []
        
        # Marketing templates for industry
        marketing_templates = self._create_marketing_templates(industry)
        templates.extend(marketing_templates)
        
        # Corporate templates for industry
        corporate_templates = self._create_corporate_templates(industry)
        templates.extend(corporate_templates)
        
        # Industry-specific templates
        industry_templates = self._create_industry_specific_templates(industry)
        templates.extend(industry_templates)
        
        return templates
        
    def _create_marketing_templates(self, industry: str) -> List[Template]:
        """Create marketing templates for specific industry"""
        
        templates = []
        
        # Social media post template
        social_template = self.create_template(
            name=f"{self.industries[industry]} Social Media Post",
            description=f"Professional social media template for {self.industries[industry]} industry",
            category="social_media",
            industry=industry,
            content={
                "layout": "social_media_standard",
                "dimensions": [1080, 1080],
                "elements": ["logo", "headline", "body_text", "cta_button"],
                "color_scheme": "industry_colors",
                "fonts": ["primary_font", "secondary_font"]
            },
            tags=["social", "marketing", "promotion"],
            difficulty="beginner",
            estimated_time=15
        )
        templates.append(social_template)
        
        # Banner advertisement template
        banner_template = self.create_template(
            name=f"{self.industries[industry]} Banner Ad",
            description=f"Eye-catching banner advertisement for {self.industries[industry]}",
            category="marketing",
            industry=industry,
            content={
                "layout": "banner_16x9",
                "dimensions": [1920, 1080],
                "elements": ["background_image", "logo", "headline", "features", "cta"],
                "animation": "slide_in_effects",
                "brand_guidelines": "company_colors"
            },
            tags=["advertising", "banner", "digital_marketing"],
            difficulty="intermediate",
            estimated_time=45
        )
        templates.append(banner_template)
        
        return templates
        
    def _create_corporate_templates(self, industry: str) -> List[Template]:
        """Create corporate templates for specific industry"""
        
        templates = []
        
        # Business presentation template
        presentation_template = self.create_template(
            name=f"{self.industries[industry]} Business Presentation",
            description=f"Professional presentation template for {self.industries[industry]} sector",
            category="business",
            industry=industry,
            content={
                "layout": "presentation_16x9",
                "slides": ["title", "agenda", "content_sections", "conclusion", "contact"],
                "design_elements": ["company_logo", "consistent_color_scheme", "professional_fonts"],
                "content_structure": "problem_solution_benefits",
                "visual_aids": ["charts", "graphs", "images"]
            },
            tags=["presentation", "corporate", "business"],
            difficulty="intermediate",
            estimated_time=60
        )
        templates.append(presentation_template)
        
        return templates
        
    def _create_industry_specific_templates(self, industry: str) -> List[Template]:
        """Create industry-specific templates"""
        
        templates = []
        
        if industry == "technology":
            # Tech product demo template
            tech_demo = self.create_template(
                name="Software Product Demo",
                description="Interactive software demonstration template",
                category="technical",
                industry=industry,
                content={
                    "layout": "demo_wide_screen",
                    "sections": ["product_overview", "features_walkthrough", "use_cases", "pricing"],
                    "interactive_elements": ["clickable_buttons", "animated_workflows", "screen_recordings"],
                    "technical_specifications": ["system_requirements", "integration_points"]
                },
                tags=["software", "demo", "technical", "product"],
                difficulty="advanced",
                estimated_time=90
            )
            templates.append(tech_demo)
            
        elif industry == "healthcare":
            # Medical presentation template
            medical_pres = self.create_template(
                name="Medical Research Presentation",
                description="Professional medical research presentation template",
                category="education",
                industry=industry,
                content={
                    "layout": "medical_presentation",
                    "sections": ["abstract", "methodology", "results", "conclusions", "references"],
                    "medical_elements": ["anatomical_diagrams", "data_charts", "clinical_photos"],
                    "citation_format": "medical_standards"
                },
                tags=["medical", "research", "healthcare", "scientific"],
                difficulty="advanced",
                estimated_time=120
            )
            templates.append(medical_pres)
            
        return templates
        
    def _determine_required_skills(self, category: str, industry: str) -> List[str]:
        """Determine required skills for template category and industry"""
        
        skills = []
        
        # Category-based skills
        if category == "marketing":
            skills.extend(["graphic_design", "copywriting", "brand_management"])
        elif category == "technical":
            skills.extend(["technical_writing", "data_analysis", "specification_documentation"])
        elif category == "education":
            skills.extend(["instructional_design", "curriculum_development", "assessment_creation"])
            
        # Industry-based skills
        if industry == "technology":
            skills.extend(["software_concepts", "technical_specifications"])
        elif industry == "finance":
            skills.extend(["financial_analysis", "regulatory_compliance"])
        elif industry == "healthcare":
            skills.extend(["medical_terminology", "regulatory_standards"])
            
        return list(set(skills))  # Remove duplicates
        
    def _matches_filters(self, template: Template, filters: Dict[str, Any]) -> bool:
        """Check if template matches given filters"""
        
        for key, value in filters.items():
            if key == "category" and template.metadata.category != value:
                return False
            elif key == "industry" and template.metadata.industry != value:
                return False
            elif key == "difficulty" and template.metadata.difficulty != value:
                return False
            elif key == "tags":
                if not any(tag in template.metadata.tags for tag in value):
                    return False
                    
        return True
        
    def _update_recent_templates(self, template_id: str):
        """Update recent templates list"""
        
        recent_file = self.library_path / "recent" / "recent.json"
        
        # Load existing recent templates
        if recent_file.exists():
            with open(recent_file, 'r') as f:
                recent = json.load(f)
        else:
            recent = []
            
        # Add template to recent (remove if already exists)
        if template_id in recent:
            recent.remove(template_id)
        recent.insert(0, template_id)
        
        # Keep only last 20 recent templates
        recent = recent[:20]
        
        # Save updated recent list
        with open(recent_file, 'w') as f:
            json.dump(recent, f, indent=2)

# Example usage
if __name__ == "__main__":
    library = TemplateLibrary()
    
    # Create some example templates
    tech_template = library.create_template(
        name="Tech Startup Pitch Deck",
        description="Professional pitch deck template for technology startups",
        category="business",
        industry="technology",
        content={
            "slides": ["cover", "problem", "solution", "market", "business_model", "team", "financials", "ask"],
            "design": "modern_minimalist",
            "colors": ["#2563eb", "#1e40af", "#ffffff"],
            "fonts": ["Helvetica Neue", "Roboto"]
        },
        tags=["startup", "pitch", "investors", "venture_capital"],
        difficulty="intermediate",
        estimated_time=45
    )
    
    print(f"Created template: {tech_template.metadata.name}")
    print(f"Template ID: {tech_template.id}")
    
    # Search templates
    results = library.search_templates("technology", {"category": "business"})
    print(f"\nFound {len(results)} technology business templates")
    
    # Get industry templates
    tech_templates = library.get_templates_by_industry("technology")
    print(f"Total technology templates: {len(tech_templates)}")