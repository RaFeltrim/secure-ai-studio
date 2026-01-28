#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👥 MULTI-USER SUPPORT SYSTEM
Phase 2 - Collaborative Features and Team Workflows

Provides:
- User management and authentication
- Team collaboration features
- Shared workspace capabilities
- Permission and access control
- Activity tracking and audit logs
- Real-time collaboration tools
"""

import json
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

class UserRole(Enum):
    """User role definitions"""
    ADMIN = "admin"
    MANAGER = "manager"
    CREATOR = "creator"
    VIEWER = "viewer"
    GUEST = "guest"

class Permission(Enum):
    """Permission definitions"""
    CREATE_CONTENT = "create_content"
    EDIT_CONTENT = "edit_content"
    DELETE_CONTENT = "delete_content"
    SHARE_CONTENT = "share_content"
    MANAGE_USERS = "manage_users"
    MANAGE_TEAMS = "manage_teams"
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    MANAGE_TEMPLATES = "manage_templates"

@dataclass
class User:
    """User account information"""
    user_id: str
    username: str
    email: str
    role: UserRole
    password_hash: str
    salt: str
    created_date: str
    last_login: Optional[str]
    is_active: bool = True
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    permissions: List[Permission] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []

@dataclass
class Team:
    """Team/workspace information"""
    team_id: str
    name: str
    description: str
    owner_id: str
    members: List[str]  # user IDs
    created_date: str
    is_active: bool = True
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}

@dataclass
class CollaborationSession:
    """Real-time collaboration session"""
    session_id: str
    team_id: str
    content_id: str
    participants: List[str]  # user IDs
    created_at: str
    expires_at: str
    is_active: bool = True

class UserManager:
    """Manages user accounts and authentication"""
    
    def __init__(self, data_path: str = "users"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.users_file = self.data_path / "users.json"
        self.sessions_file = self.data_path / "sessions.json"
        
        self.users: Dict[str, User] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        self._load_data()
        
    def _load_data(self):
        """Load user data from files"""
        # Load users
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                users_data = json.load(f)
                for user_data in users_data:
                    user = User(**user_data)
                    self.users[user.user_id] = user
                    
        # Load sessions
        if self.sessions_file.exists():
            with open(self.sessions_file, 'r') as f:
                self.active_sessions = json.load(f)
                
    def _save_data(self):
        """Save user data to files"""
        # Save users
        users_list = [asdict(user) for user in self.users.values()]
        with open(self.users_file, 'w') as f:
            json.dump(users_list, f, indent=2)
            
        # Save sessions
        with open(self.sessions_file, 'w') as f:
            json.dump(self.active_sessions, f, indent=2)
            
    def create_user(self, username: str, email: str, password: str, 
                   role: UserRole = UserRole.CREATOR) -> User:
        """Create a new user account"""
        
        # Check if user already exists
        if self.get_user_by_username(username) or self.get_user_by_email(email):
            raise ValueError("User already exists")
            
        # Generate user ID
        user_id = str(uuid.uuid4())
        
        # Hash password
        salt = self._generate_salt()
        password_hash = self._hash_password(password, salt)
        
        # Create user
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            password_hash=password_hash,
            salt=salt,
            created_date=datetime.now().isoformat(),
            last_login=None,
            permissions=self._get_role_permissions(role)
        )
        
        self.users[user_id] = user
        self._save_data()
        
        return user
        
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return session token"""
        
        user = self.get_user_by_username(username)
        if not user:
            return None
            
        # Verify password
        password_hash = self._hash_password(password, user.salt)
        if password_hash != user.password_hash:
            return None
            
        # Update last login
        user.last_login = datetime.now().isoformat()
        
        # Create session
        session_token = self._create_session(user.user_id)
        
        self._save_data()
        
        return session_token
        
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
        
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
        
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
        
    def update_user_role(self, user_id: str, new_role: UserRole):
        """Update user role and permissions"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")
            
        user.role = new_role
        user.permissions = self._get_role_permissions(new_role)
        self._save_data()
        
    def _generate_salt(self) -> str:
        """Generate password salt"""
        return hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
    def _create_session(self, user_id: str) -> str:
        """Create authentication session"""
        session_token = str(uuid.uuid4())
        
        self.active_sessions[session_token] = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        return session_token
        
    def _get_role_permissions(self, role: UserRole) -> List[Permission]:
        """Get permissions for user role"""
        permission_map = {
            UserRole.ADMIN: list(Permission),
            UserRole.MANAGER: [
                Permission.CREATE_CONTENT,
                Permission.EDIT_CONTENT,
                Permission.DELETE_CONTENT,
                Permission.SHARE_CONTENT,
                Permission.MANAGE_TEAMS,
                Permission.VIEW_ANALYTICS
            ],
            UserRole.CREATOR: [
                Permission.CREATE_CONTENT,
                Permission.EDIT_CONTENT,
                Permission.SHARE_CONTENT
            ],
            UserRole.VIEWER: [
                Permission.SHARE_CONTENT
            ],
            UserRole.GUEST: []
        }
        
        return permission_map.get(role, [])

class TeamManager:
    """Manages teams and collaborative workspaces"""
    
    def __init__(self, data_path: str = "teams"):
        self.data_path = Path(data_path)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.teams_file = self.data_path / "teams.json"
        
        self.teams: Dict[str, Team] = {}
        self._load_data()
        
    def _load_data(self):
        """Load team data"""
        if self.teams_file.exists():
            with open(self.teams_file, 'r') as f:
                teams_data = json.load(f)
                for team_data in teams_data:
                    team = Team(**team_data)
                    self.teams[team.team_id] = team
                    
    def _save_data(self):
        """Save team data"""
        teams_list = [asdict(team) for team in self.teams.values()]
        with open(self.teams_file, 'w') as f:
            json.dump(teams_list, f, indent=2)
            
    def create_team(self, name: str, description: str, owner_id: str) -> Team:
        """Create a new team"""
        team_id = str(uuid.uuid4())
        
        team = Team(
            team_id=team_id,
            name=name,
            description=description,
            owner_id=owner_id,
            members=[owner_id],
            created_date=datetime.now().isoformat(),
            settings={
                'visibility': 'private',
                'content_sharing': 'team_only',
                'approval_required': False
            }
        )
        
        self.teams[team_id] = team
        self._save_data()
        
        return team
        
    def add_member(self, team_id: str, user_id: str):
        """Add member to team"""
        team = self.teams.get(team_id)
        if not team:
            raise ValueError("Team not found")
            
        if user_id not in team.members:
            team.members.append(user_id)
            self._save_data()
            
    def remove_member(self, team_id: str, user_id: str):
        """Remove member from team"""
        team = self.teams.get(team_id)
        if not team:
            raise ValueError("Team not found")
            
        if user_id in team.members:
            team.members.remove(user_id)
            self._save_data()
            
    def get_user_teams(self, user_id: str) -> List[Team]:
        """Get all teams for a user"""
        user_teams = []
        for team in self.teams.values():
            if user_id in team.members:
                user_teams.append(team)
        return user_teams
        
    def get_team_members(self, team_id: str) -> List[str]:
        """Get member IDs for a team"""
        team = self.teams.get(team_id)
        if not team:
            return []
        return team.members[:]

class CollaborationManager:
    """Manages real-time collaboration features"""
    
    def __init__(self):
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.content_locks: Dict[str, Dict[str, Any]] = {}  # content_id -> {user_id, timestamp}
        
    def start_collaboration_session(self, team_id: str, content_id: str, 
                                  initiator_id: str) -> CollaborationSession:
        """Start a collaboration session"""
        session_id = str(uuid.uuid4())
        
        session = CollaborationSession(
            session_id=session_id,
            team_id=team_id,
            content_id=content_id,
            participants=[initiator_id],
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=4)).isoformat()
        )
        
        self.active_sessions[session_id] = session
        return session
        
    def join_session(self, session_id: str, user_id: str) -> bool:
        """Join an existing collaboration session"""
        session = self.active_sessions.get(session_id)
        if not session or not session.is_active:
            return False
            
        if user_id not in session.participants:
            session.participants.append(user_id)
            
        return True
        
    def leave_session(self, session_id: str, user_id: str):
        """Leave collaboration session"""
        session = self.active_sessions.get(session_id)
        if session and user_id in session.participants:
            session.participants.remove(user_id)
            
    def acquire_content_lock(self, content_id: str, user_id: str) -> bool:
        """Acquire lock on content for editing"""
        current_lock = self.content_locks.get(content_id)
        
        # If no lock exists or lock has expired
        if not current_lock or self._is_lock_expired(current_lock):
            self.content_locks[content_id] = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            return True
            
        # If user already has lock
        if current_lock['user_id'] == user_id:
            return True
            
        # Lock held by another user
        return False
        
    def release_content_lock(self, content_id: str, user_id: str):
        """Release content lock"""
        current_lock = self.content_locks.get(content_id)
        if current_lock and current_lock['user_id'] == user_id:
            del self.content_locks[content_id]
            
    def get_content_lock_owner(self, content_id: str) -> Optional[str]:
        """Get current lock owner for content"""
        lock = self.content_locks.get(content_id)
        if lock and not self._is_lock_expired(lock):
            return lock['user_id']
        return None
        
    def _is_lock_expired(self, lock: Dict[str, Any]) -> bool:
        """Check if content lock has expired (5 minutes)"""
        lock_time = datetime.fromisoformat(lock['timestamp'])
        return datetime.now() - lock_time > timedelta(minutes=5)

class ActivityTracker:
    """Tracks user activities and generates audit logs"""
    
    def __init__(self, log_path: str = "logs/activity"):
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)
        
    def log_activity(self, user_id: str, action: str, 
                    resource_type: str, resource_id: str, 
                    details: Dict[str, Any] = None):
        """Log user activity"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': details or {},
            'ip_address': '127.0.0.1'  # Would be captured from request in real implementation
        }
        
        # Write to daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_path / f"activity_{today}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
            
    def get_user_activities(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent activities for a user"""
        activities = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Search recent log files
        for log_file in self.log_path.glob("activity_*.jsonl"):
            file_date_str = log_file.name.split('_')[1].split('.')[0]
            file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
            
            if file_date >= cutoff_date:
                with open(log_file, 'r') as f:
                    for line in f:
                        entry = json.loads(line)
                        if entry['user_id'] == user_id:
                            activities.append(entry)
                            
        return sorted(activities, key=lambda x: x['timestamp'], reverse=True)

# Main Multi-user Support System
class MultiUserSupport:
    """Main multi-user support system combining all components"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.team_manager = TeamManager()
        self.collaboration_manager = CollaborationManager()
        self.activity_tracker = ActivityTracker()
        
    def register_user(self, username: str, email: str, password: str,
                     role: UserRole = UserRole.CREATOR) -> User:
        """Register new user"""
        user = self.user_manager.create_user(username, email, password, role)
        self.activity_tracker.log_activity(
            user.user_id, 'user_registered', 'user', user.user_id,
            {'username': username, 'role': role.value}
        )
        return user
        
    def login_user(self, username: str, password: str) -> Optional[str]:
        """Login user and return session token"""
        session_token = self.user_manager.authenticate_user(username, password)
        if session_token:
            user = self.user_manager.get_user_by_username(username)
            self.activity_tracker.log_activity(
                user.user_id, 'user_login', 'user', user.user_id,
                {'session_token': session_token[:8] + '...'}
            )
        return session_token
        
    def create_team_workspace(self, name: str, description: str, 
                            owner_username: str) -> Team:
        """Create team workspace"""
        owner = self.user_manager.get_user_by_username(owner_username)
        if not owner:
            raise ValueError("Owner user not found")
            
        team = self.team_manager.create_team(name, description, owner.user_id)
        self.activity_tracker.log_activity(
            owner.user_id, 'team_created', 'team', team.team_id,
            {'team_name': name}
        )
        return team
        
    def start_collaborative_session(self, team_id: str, content_id: str,
                                  username: str) -> CollaborationSession:
        """Start collaborative editing session"""
        user = self.user_manager.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
            
        session = self.collaboration_manager.start_collaboration_session(
            team_id, content_id, user.user_id
        )
        
        self.activity_tracker.log_activity(
            user.user_id, 'collaboration_started', 'content', content_id,
            {'team_id': team_id, 'session_id': session.session_id}
        )
        
        return session

# Example usage
if __name__ == "__main__":
    multi_user_system = MultiUserSupport()
    
    # Register users
    admin_user = multi_user_system.register_user(
        "admin", "admin@company.com", "securepassword123", UserRole.ADMIN
    )
    
    creator_user = multi_user_system.register_user(
        "designer", "designer@company.com", "creativework123", UserRole.CREATOR
    )
    
    print(f"Registered users: {admin_user.username}, {creator_user.username}")
    
    # Create team
    design_team = multi_user_system.create_team_workspace(
        "Design Team", "Creative design and content team", "admin"
    )
    
    # Add member to team
    multi_user_system.team_manager.add_member(design_team.team_id, creator_user.user_id)
    
    print(f"Created team: {design_team.name} with {len(design_team.members)} members")
    
    # Login user
    session_token = multi_user_system.login_user("designer", "creativework123")
    if session_token:
        print(f"User logged in successfully. Session: {session_token[:10]}...")