#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏛️ ENTERPRISE GOVERNANCE SYSTEM
Post-Phase 3 Enhancement - Advanced Governance and Policy Management

Provides:
- Advanced role-based access control (RBAC)
- Policy management and enforcement engine
- Approval workflows and governance tools
- Enterprise license management
- Audit and compliance policy automation
"""

from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
import hashlib
from functools import wraps

class UserRole(Enum):
    """Enterprise user roles"""
    SYSTEM_ADMIN = "system_admin"
    SECURITY_ADMIN = "security_admin"
    COMPLIANCE_OFFICER = "compliance_officer"
    DATA_PROTECTION_OFFICER = "dpo"
    BUSINESS_OWNER = "business_owner"
    DEPARTMENT_HEAD = "department_head"
    TEAM_LEADER = "team_leader"
    CONTENT_CREATOR = "content_creator"
    REVIEWER = "reviewer"
    AUDITOR = "auditor"
    EXTERNAL_PARTNER = "external_partner"

class Permission(Enum):
    """Granular permissions"""
    # System Permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    SYSTEM_CONFIGURATION = "system_configuration"
    VIEW_SYSTEM_LOGS = "view_system_logs"
    
    # Content Permissions
    CREATE_CONTENT = "create_content"
    EDIT_CONTENT = "edit_content"
    DELETE_CONTENT = "delete_content"
    PUBLISH_CONTENT = "publish_content"
    EXPORT_CONTENT = "export_content"
    
    # Model Permissions
    ACCESS_MODELS = "access_models"
    TRAIN_MODELS = "train_models"
    DEPLOY_MODELS = "deploy_models"
    MANAGE_MODEL_REGISTRY = "manage_model_registry"
    
    # Data Permissions
    ACCESS_SENSITIVE_DATA = "access_sensitive_data"
    MODIFY_DATA_CLASSIFICATION = "modify_data_classification"
    DATA_EXPORT = "data_export"
    
    # Compliance Permissions
    VIEW_COMPLIANCE_REPORTS = "view_compliance_reports"
    MANAGE_COMPLIANCE_SETTINGS = "manage_compliance_settings"
    CONDUCT_AUDITS = "conduct_audits"
    
    # Financial Permissions
    VIEW_BILLING = "view_billing"
    MANAGE_SUBSCRIPTIONS = "manage_subscriptions"
    APPROVE_EXPENSES = "approve_expenses"

class PolicyType(Enum):
    """Types of governance policies"""
    ACCESS_CONTROL = "access_control"
    DATA_CLASSIFICATION = "data_classification"
    CONTENT_MODERATION = "content_moderation"
    USAGE_LIMITS = "usage_limits"
    COMPLIANCE = "compliance"
    AUDIT = "audit"

@dataclass
class PolicyRule:
    """Individual policy rule"""
    rule_id: str
    policy_type: PolicyType
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[str]
    enabled: bool
    created_by: str
    created_date: str
    last_modified: str

@dataclass
class ApprovalWorkflow:
    """Approval workflow definition"""
    workflow_id: str
    name: str
    description: str
    trigger_conditions: Dict[str, Any]
    approvers: List[str]  # role names or user IDs
    approval_levels: int
    timeout_hours: int
    escalation_policy: str
    created_by: str
    created_date: str

class AdvancedRBAC:
    """Advanced Role-Based Access Control System"""
    
    def __init__(self):
        self.roles: Dict[str, Set[Permission]] = {}
        self.user_roles: Dict[str, List[str]] = {}  # user_id -> role_names
        self.role_hierarchy: Dict[str, List[str]] = {}  # role -> inherited_roles
        self._initialize_enterprise_roles()
        
    def _initialize_enterprise_roles(self):
        """Initialize enterprise role hierarchy"""
        # Define role permissions
        role_permissions = {
            UserRole.SYSTEM_ADMIN: set(Permission),
            UserRole.SECURITY_ADMIN: {
                Permission.MANAGE_USERS, Permission.VIEW_SYSTEM_LOGS,
                Permission.ACCESS_SENSITIVE_DATA, Permission.CONDUCT_AUDITS
            },
            UserRole.COMPLIANCE_OFFICER: {
                Permission.VIEW_COMPLIANCE_REPORTS, Permission.MANAGE_COMPLIANCE_SETTINGS,
                Permission.CONDUCT_AUDITS, Permission.VIEW_SYSTEM_LOGS
            },
            UserRole.DATA_PROTECTION_OFFICER: {
                Permission.ACCESS_SENSITIVE_DATA, Permission.MODIFY_DATA_CLASSIFICATION,
                Permission.VIEW_COMPLIANCE_REPORTS, Permission.CONDUCT_AUDITS
            },
            UserRole.BUSINESS_OWNER: {
                Permission.CREATE_CONTENT, Permission.EDIT_CONTENT,
                Permission.PUBLISH_CONTENT, Permission.VIEW_BILLING,
                Permission.APPROVE_EXPENSES
            },
            UserRole.DEPARTMENT_HEAD: {
                Permission.CREATE_CONTENT, Permission.EDIT_CONTENT,
                Permission.PUBLISH_CONTENT, Permission.MANAGE_USERS
            },
            UserRole.TEAM_LEADER: {
                Permission.CREATE_CONTENT, Permission.EDIT_CONTENT,
                Permission.PUBLISH_CONTENT
            },
            UserRole.CONTENT_CREATOR: {
                Permission.CREATE_CONTENT, Permission.EDIT_CONTENT
            },
            UserRole.REVIEWER: {
                Permission.EDIT_CONTENT, Permission.PUBLISH_CONTENT
            },
            UserRole.AUDITOR: {
                Permission.VIEW_SYSTEM_LOGS, Permission.CONDUCT_AUDITS,
                Permission.VIEW_COMPLIANCE_REPORTS
            },
            UserRole.EXTERNAL_PARTNER: {
                Permission.CREATE_CONTENT
            }
        }
        
        # Set up role hierarchy
        self.role_hierarchy = {
            UserRole.SYSTEM_ADMIN.value: [UserRole.SECURITY_ADMIN.value, UserRole.COMPLIANCE_OFFICER.value],
            UserRole.SECURITY_ADMIN.value: [UserRole.CONTENT_CREATOR.value],
            UserRole.DEPARTMENT_HEAD.value: [UserRole.TEAM_LEADER.value],
            UserRole.TEAM_LEADER.value: [UserRole.CONTENT_CREATOR.value]
        }
        
        # Initialize roles
        for role, permissions in role_permissions.items():
            self.roles[role.value] = permissions
            
    def assign_role(self, user_id: str, role: UserRole):
        """Assign role to user"""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
            
        if role.value not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role.value)
            
    def remove_role(self, user_id: str, role: UserRole):
        """Remove role from user"""
        if user_id in self.user_roles and role.value in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role.value)
            
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for user including inherited roles"""
        permissions = set()
        
        if user_id in self.user_roles:
            for role_name in self.user_roles[user_id]:
                # Add direct permissions
                if role_name in self.roles:
                    permissions.update(self.roles[role_name])
                    
                # Add inherited permissions
                if role_name in self.role_hierarchy:
                    for inherited_role in self.role_hierarchy[role_name]:
                        if inherited_role in self.roles:
                            permissions.update(self.roles[inherited_role])
                            
        return permissions
        
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions
        
    def create_custom_role(self, role_name: str, permissions: Set[Permission], 
                          inherits_from: Optional[List[str]] = None) -> str:
        """Create custom role"""
        custom_role_id = f"custom_{role_name.lower().replace(' ', '_')}_{str(uuid.uuid4())[:8]}"
        self.roles[custom_role_id] = permissions
        
        if inherits_from:
            self.role_hierarchy[custom_role_id] = inherits_from
            
        return custom_role_id

class PolicyEngine:
    """Enterprise policy management and enforcement"""
    
    def __init__(self):
        self.policies: Dict[str, PolicyRule] = {}
        self.workflows: Dict[str, ApprovalWorkflow] = {}
        self.policy_evaluators: Dict[PolicyType, Callable] = {}
        self._register_policy_evaluators()
        
    def _register_policy_evaluators(self):
        """Register policy evaluation functions"""
        self.policy_evaluators[PolicyType.ACCESS_CONTROL] = self._evaluate_access_policy
        self.policy_evaluators[PolicyType.DATA_CLASSIFICATION] = self._evaluate_data_policy
        self.policy_evaluators[PolicyType.CONTENT_MODERATION] = self._evaluate_content_policy
        self.policy_evaluators[PolicyType.USAGE_LIMITS] = self._evaluate_usage_policy
        self.policy_evaluators[PolicyType.COMPLIANCE] = self._evaluate_compliance_policy
        
    def create_policy(self, policy_type: PolicyType, name: str, description: str,
                     conditions: Dict[str, Any], actions: List[str], 
                     created_by: str) -> PolicyRule:
        """Create new policy rule"""
        policy_id = str(uuid.uuid4())
        
        policy = PolicyRule(
            rule_id=policy_id,
            policy_type=policy_type,
            name=name,
            description=description,
            conditions=conditions,
            actions=actions,
            enabled=True,
            created_by=created_by,
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat()
        )
        
        self.policies[policy_id] = policy
        return policy
        
    def evaluate_policies(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all applicable policies for given context"""
        violations = []
        
        for policy in self.policies.values():
            if not policy.enabled:
                continue
                
            evaluator = self.policy_evaluators.get(policy.policy_type)
            if evaluator and evaluator(context, policy):
                violation = {
                    "policy_id": policy.rule_id,
                    "policy_name": policy.name,
                    "violation_details": self._get_violation_details(context, policy),
                    "recommended_actions": policy.actions,
                    "timestamp": datetime.now().isoformat()
                }
                violations.append(violation)
                
        return violations
        
    def _evaluate_access_policy(self, context: Dict[str, Any], policy: PolicyRule) -> bool:
        """Evaluate access control policy"""
        user_role = context.get("user_role")
        resource_type = context.get("resource_type")
        action = context.get("action")
        
        # Check if user role is restricted for this resource/action
        restricted_roles = policy.conditions.get("restricted_roles", [])
        if user_role in restricted_roles:
            return True
            
        # Check time-based restrictions
        current_time = datetime.now()
        restricted_times = policy.conditions.get("restricted_times", [])
        for time_range in restricted_times:
            start_time = datetime.strptime(time_range["start"], "%H:%M").time()
            end_time = datetime.strptime(time_range["end"], "%H:%M").time()
            if start_time <= current_time.time() <= end_time:
                return True
                
        return False
        
    def _evaluate_data_policy(self, context: Dict[str, Any], policy: PolicyRule) -> bool:
        """Evaluate data classification policy"""
        data_classification = context.get("data_classification")
        user_clearance = context.get("user_clearance")
        
        # Check classification hierarchy
        classification_levels = ["public", "internal", "confidential", "restricted", "top_secret"]
        
        if data_classification and user_clearance:
            data_level = classification_levels.index(data_classification.lower())
            user_level = classification_levels.index(user_clearance.lower())
            
            if data_level > user_level:
                return True  # Violation: insufficient clearance
                
        return False
        
    def _evaluate_content_policy(self, context: Dict[str, Any], policy: PolicyRule) -> bool:
        """Evaluate content moderation policy"""
        content_type = context.get("content_type")
        content_tags = context.get("content_tags", [])
        
        # Check restricted content types
        restricted_types = policy.conditions.get("restricted_types", [])
        if content_type in restricted_types:
            return True
            
        # Check prohibited tags
        prohibited_tags = policy.conditions.get("prohibited_tags", [])
        if any(tag in prohibited_tags for tag in content_tags):
            return True
            
        return False
        
    def _evaluate_usage_policy(self, context: Dict[str, Any], policy: PolicyRule) -> bool:
        """Evaluate usage limit policy"""
        user_id = context.get("user_id")
        resource = context.get("resource")
        usage_amount = context.get("usage_amount", 0)
        
        # Check usage limits
        limits = policy.conditions.get("limits", {})
        user_limit = limits.get(user_id, limits.get("default", float('inf')))
        
        if usage_amount > user_limit:
            return True  # Violation: usage limit exceeded
            
        return False
        
    def _evaluate_compliance_policy(self, context: Dict[str, Any], policy: PolicyRule) -> bool:
        """Evaluate compliance policy"""
        compliance_framework = context.get("compliance_framework")
        required_controls = policy.conditions.get("required_controls", [])
        
        # Check if required controls are satisfied
        satisfied_controls = context.get("satisfied_controls", [])
        missing_controls = set(required_controls) - set(satisfied_controls)
        
        return len(missing_controls) > 0
        
    def _get_violation_details(self, context: Dict[str, Any], policy: PolicyRule) -> str:
        """Generate violation details message"""
        return f"Policy '{policy.name}' violated. Context: {json.dumps(context, indent=2)}"

class ApprovalWorkflowEngine:
    """Enterprise approval workflow management"""
    
    def __init__(self):
        self.workflows: Dict[str, ApprovalWorkflow] = {}
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}  # approval_id -> approval_data
        
    def create_workflow(self, name: str, description: str, trigger_conditions: Dict[str, Any],
                       approvers: List[str], approval_levels: int, timeout_hours: int,
                       escalation_policy: str, created_by: str) -> ApprovalWorkflow:
        """Create new approval workflow"""
        workflow_id = str(uuid.uuid4())
        
        workflow = ApprovalWorkflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            trigger_conditions=trigger_conditions,
            approvers=approvers,
            approval_levels=approval_levels,
            timeout_hours=timeout_hours,
            escalation_policy=escalation_policy,
            created_by=created_by,
            created_date=datetime.now().isoformat()
        )
        
        self.workflows[workflow_id] = workflow
        return workflow
        
    def submit_for_approval(self, workflow_id: str, request_data: Dict[str, Any],
                           submitter_id: str) -> str:
        """Submit request for approval"""
        approval_id = str(uuid.uuid4())
        
        approval_request = {
            "approval_id": approval_id,
            "workflow_id": workflow_id,
            "request_data": request_data,
            "submitter_id": submitter_id,
            "status": "pending",
            "current_level": 1,
            "approvers_completed": [],
            "submitted_at": datetime.now().isoformat(),
            "deadline": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        self.pending_approvals[approval_id] = approval_request
        return approval_id
        
    def approve_request(self, approval_id: str, approver_id: str, comments: str = "") -> bool:
        """Approve pending request"""
        if approval_id not in self.pending_approvals:
            return False
            
        approval = self.pending_approvals[approval_id]
        workflow = self.workflows[approval["workflow_id"]]
        
        # Check if approver is authorized
        if approver_id not in workflow.approvers:
            return False
            
        # Record approval
        approval["approvers_completed"].append({
            "approver_id": approver_id,
            "approved_at": datetime.now().isoformat(),
            "comments": comments
        })
        
        # Check if all levels approved
        if len(approval["approvers_completed"]) >= workflow.approval_levels:
            approval["status"] = "approved"
            approval["completed_at"] = datetime.now().isoformat()
            
        return True
        
    def reject_request(self, approval_id: str, rejector_id: str, reason: str) -> bool:
        """Reject pending request"""
        if approval_id not in self.pending_approvals:
            return False
            
        approval = self.pending_approvals[approval_id]
        approval["status"] = "rejected"
        approval["rejected_by"] = rejector_id
        approval["rejection_reason"] = reason
        approval["completed_at"] = datetime.now().isoformat()
        
        return True

class LicenseManager:
    """Enterprise license and subscription management"""
    
    def __init__(self):
        self.licenses: Dict[str, Dict[str, Any]] = {}
        self.usage_tracking: Dict[str, Dict[str, int]] = {}
        
    def create_license(self, customer_id: str, license_type: str, features: List[str],
                      user_limit: int, expiration_date: str, metadata: Dict[str, Any]) -> str:
        """Create new enterprise license"""
        license_id = str(uuid.uuid4())
        
        license_data = {
            "license_id": license_id,
            "customer_id": customer_id,
            "license_type": license_type,
            "features": features,
            "user_limit": user_limit,
            "expiration_date": expiration_date,
            "status": "active",
            "created_date": datetime.now().isoformat(),
            "metadata": metadata,
            "usage_counts": {feature: 0 for feature in features}
        }
        
        self.licenses[license_id] = license_data
        return license_id
        
    def check_license_validity(self, license_id: str, feature: str = None) -> bool:
        """Check if license is valid and feature is permitted"""
        if license_id not in self.licenses:
            return False
            
        license_data = self.licenses[license_id]
        
        # Check expiration
        if datetime.fromisoformat(license_data["expiration_date"]) < datetime.now():
            license_data["status"] = "expired"
            return False
            
        # Check feature access
        if feature and feature not in license_data["features"]:
            return False
            
        # Check user limit (would integrate with user management)
        # if license_data["current_users"] > license_data["user_limit"]:
        #     return False
            
        return True
        
    def track_feature_usage(self, license_id: str, feature: str) -> bool:
        """Track feature usage against license limits"""
        if not self.check_license_validity(license_id, feature):
            return False
            
        self.licenses[license_id]["usage_counts"][feature] += 1
        return True

# Main Enterprise Governance System
class EnterpriseGovernanceSystem:
    """Complete enterprise governance solution"""
    
    def __init__(self):
        self.rbac = AdvancedRBAC()
        self.policy_engine = PolicyEngine()
        self.workflow_engine = ApprovalWorkflowEngine()
        self.license_manager = LicenseManager()
        
    def enforce_governance(self, user_id: str, action: str, 
                          resource: str, context: Dict[str, Any] = None) -> bool:
        """Enforce governance policies for user action"""
        if context is None:
            context = {}
            
        context.update({
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "timestamp": datetime.now().isoformat()
        })
        
        # Check RBAC permissions
        required_permission = self._map_action_to_permission(action)
        if not self.rbac.check_permission(user_id, required_permission):
            return False
            
        # Evaluate applicable policies
        violations = self.policy_engine.evaluate_policies(context)
        if violations:
            # Log violations and potentially block action
            self._log_policy_violations(violations)
            return False  # or implement violation handling logic
            
        return True
        
    def _map_action_to_permission(self, action: str) -> Permission:
        """Map action to required permission"""
        action_permission_map = {
            "create_content": Permission.CREATE_CONTENT,
            "edit_content": Permission.EDIT_CONTENT,
            "delete_content": Permission.DELETE_CONTENT,
            "publish_content": Permission.PUBLISH_CONTENT,
            "export_content": Permission.EXPORT_CONTENT,
            "access_models": Permission.ACCESS_MODELS,
            "train_models": Permission.TRAIN_MODELS,
            "deploy_models": Permission.DEPLOY_MODELS,
            "manage_users": Permission.MANAGE_USERS,
            "view_logs": Permission.VIEW_SYSTEM_LOGS
        }
        
        return action_permission_map.get(action, Permission.CREATE_CONTENT)
        
    def _log_policy_violations(self, violations: List[Dict[str, Any]]):
        """Log policy violations for audit purposes"""
        for violation in violations:
            log_entry = {
                "event_type": "policy_violation",
                "timestamp": violation["timestamp"],
                "policy_id": violation["policy_id"],
                "details": violation["violation_details"],
                "actions_taken": violation["recommended_actions"]
            }
            # Would integrate with audit logging system
            print(f"Policy violation logged: {log_entry}")

# Decorator for governance enforcement
def governed_action(required_permission: Permission = None):
    """Decorator to enforce governance on function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Extract governance context
            user_id = kwargs.get('user_id') or getattr(self, 'current_user_id', 'system')
            action = func.__name__
            
            # Enforce governance
            governance_system = getattr(self, 'governance_system', None)
            if governance_system:
                context = kwargs.get('governance_context', {})
                if not governance_system.enforce_governance(user_id, action, "system_resource", context):
                    raise PermissionError(f"Governance policy violation for action: {action}")
                    
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

# Example usage
if __name__ == "__main__":
    governance = EnterpriseGovernanceSystem()
    
    # Assign roles
    governance.rbac.assign_role("user_001", UserRole.CONTENT_CREATOR)
    governance.rbac.assign_role("user_002", UserRole.DEPARTMENT_HEAD)
    
    # Create policy
    content_policy = governance.policy_engine.create_policy(
        policy_type=PolicyType.CONTENT_MODERATION,
        name="Restricted Content Policy",
        description="Prevent creation of sensitive content",
        conditions={
            "restricted_types": ["medical_advice", "legal_advice"],
            "prohibited_tags": ["confidential", "proprietary"]
        },
        actions=["block_content", "notify_supervisor"],
        created_by="admin"
    )
    
    # Test governance enforcement
    context = {
        "content_type": "medical_advice",
        "content_tags": ["general"]
    }
    
    violations = governance.policy_engine.evaluate_policies(context)
    print(f"Policy violations found: {len(violations)}")
    
    # Create license
    license_id = governance.license_manager.create_license(
        customer_id="enterprise_001",
        license_type="premium",
        features=["content_generation", "model_training", "api_access"],
        user_limit=100,
        expiration_date="2027-01-28T00:00:00",
        metadata={"contract_id": "CONTRACT-2026-001"}
    )
    
    print(f"License created: {license_id}")
    print(f"License valid: {governance.license_manager.check_license_validity(license_id, 'content_generation')}")