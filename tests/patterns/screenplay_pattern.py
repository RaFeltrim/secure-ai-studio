#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎬 SCREENPLAY PATTERN IMPLEMENTATION
SDET Phase 1 Week 1 - Advanced Test Design Pattern

Transforms traditional Page Objects into user-centric, readable test scenarios
using the Screenplay Pattern (also known as Journey Pattern or Actor pattern).

Key Benefits:
- Improved test readability and maintainability
- Better separation of concerns
- Enhanced reusability across test scenarios
- Natural language-like test expressions
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ==================== CORE SCREENPLAY CLASSES ====================

class Actor:
    """Represents a user performing actions in the system"""
    
    def __init__(self, name: str):
        self.name = name
        self.abilities = {}
        self.questions = []
        
    def can(self, ability_name: str, ability) -> 'Actor':
        """Grant an ability to the actor"""
        self.abilities[ability_name] = ability
        return self
        
    def attempts_to(self, *tasks) -> 'Actor':
        """Attempt to perform one or more tasks"""
        for task in tasks:
            task.perform_as(self)
        return self
        
    def should_see_the(self, *questions) -> 'Actor':
        """Verify expected outcomes"""
        for question in questions:
            question.answered_by(self)
        return self
        
    def uses_ability(self, ability_name: str):
        """Access a specific ability"""
        if ability_name not in self.abilities:
            raise ValueError(f"Actor {self.name} doesn't have ability: {ability_name}")
        return self.abilities[ability_name]

class Ability(ABC):
    """Abstract base class for actor abilities"""
    
    @abstractmethod
    def initialize(self, **kwargs):
        """Initialize the ability with required parameters"""
        pass

class Task(ABC):
    """Abstract base class for test tasks"""
    
    @abstractmethod
    def perform_as(self, actor: Actor):
        """Perform the task as the given actor"""
        pass

class Question(ABC):
    """Abstract base class for test questions/verifications"""
    
    @abstractmethod
    def answered_by(self, actor: Actor) -> Any:
        """Answer the question from the actor's perspective"""
        pass

# ==================== WEB BROWSER ABILITY ====================

@dataclass
class BrowserConfig:
    """Browser configuration settings"""
    driver: WebDriver
    base_url: str
    default_timeout: int = 10
    implicit_wait: int = 5

class BrowseTheWeb(Ability):
    """Ability to interact with web browsers"""
    
    def __init__(self):
        self.browser_config: Optional[BrowserConfig] = None
        
    def initialize(self, driver: WebDriver, base_url: str, 
                   default_timeout: int = 10, implicit_wait: int = 5):
        """Initialize browser ability"""
        self.browser_config = BrowserConfig(
            driver=driver,
            base_url=base_url,
            default_timeout=default_timeout,
            implicit_wait=implicit_wait
        )
        self.browser_config.driver.implicitly_wait(implicit_wait)
        
    def navigate_to(self, url: str):
        """Navigate to URL"""
        if not self.browser_config:
            raise RuntimeError("Browser not initialized")
            
        full_url = f"{self.browser_config.base_url}{url}" if not url.startswith('http') else url
        self.browser_config.driver.get(full_url)
        
    def find_element(self, locator: tuple, timeout: int = None) -> Any:
        """Find element with explicit wait"""
        if not self.browser_config:
            raise RuntimeError("Browser not initialized")
            
        wait_time = timeout or self.browser_config.default_timeout
        return WebDriverWait(self.browser_config.driver, wait_time).until(
            EC.presence_of_element_located(locator)
        )
        
    def find_elements(self, locator: tuple, timeout: int = None) -> List[Any]:
        """Find multiple elements"""
        if not self.browser_config:
            raise RuntimeError("Browser not initialized")
            
        wait_time = timeout or self.browser_config.default_timeout
        return WebDriverWait(self.browser_config.driver, wait_time).until(
            EC.presence_of_all_elements_located(locator)
        )
        
    def wait_for_condition(self, condition, timeout: int = None):
        """Wait for specific condition"""
        if not self.browser_config:
            raise RuntimeError("Browser not initialized")
            
        wait_time = timeout or self.browser_config.default_timeout
        return WebDriverWait(self.browser_config.driver, wait_time).until(condition)
        
    def get_current_url(self) -> str:
        """Get current browser URL"""
        if not self.browser_config:
            raise RuntimeError("Browser not initialized")
        return self.browser_config.driver.current_url
        
    def get_page_title(self) -> str:
        """Get current page title"""
        if not self.browser_config:
            raise RuntimeError("Browser not initialized")
        return self.browser_config.driver.title

# ==================== COMMON TASKS ====================

class Open:
    """Task to open/navigate to a URL"""
    
    def __init__(self, url: str):
        self.url = url
        
    def perform_as(self, actor: Actor):
        """Perform navigation task"""
        browser = actor.uses_ability("browse_the_web")
        browser.navigate_to(self.url)
        print(f"🎬 {actor.name} opens {self.url}")

class Click:
    """Task to click on elements"""
    
    def __init__(self, locator: tuple, description: str = ""):
        self.locator = locator
        self.description = description or f"element {locator}"
        
    def perform_as(self, actor: Actor):
        """Perform click task"""
        browser = actor.uses_ability("browse_the_web")
        element = browser.find_element(self.locator)
        element.click()
        print(f"🎬 {actor.name} clicks on {self.description}")

class Enter:
    """Task to enter text into input fields"""
    
    def __init__(self, text: str, into: tuple, description: str = ""):
        self.text = text
        self.into = into
        self.description = description or f"field {into}"
        
    def perform_as(self, actor: Actor):
        """Perform text entry task"""
        browser = actor.uses_ability("browse_the_web")
        element = browser.find_element(self.into)
        element.clear()
        element.send_keys(self.text)
        print(f"🎬 {actor.name} enters '{self.text}' into {self.description}")

class Wait:
    """Task to wait for conditions"""
    
    def __init__(self, seconds: int):
        self.seconds = seconds
        
    def perform_as(self, actor: Actor):
        """Perform wait task"""
        time.sleep(self.seconds)
        print(f"🎬 {actor.name} waits for {self.seconds} seconds")

# ==================== QUESTIONS ====================

class Text:
    """Question to verify element text"""
    
    def __init__(self, locator: tuple, expected_text: str, description: str = ""):
        self.locator = locator
        self.expected_text = expected_text
        self.description = description or f"text in {locator}"
        
    def answered_by(self, actor: Actor) -> bool:
        """Answer the text verification question"""
        browser = actor.uses_ability("browse_the_web")
        element = browser.find_element(self.locator)
        actual_text = element.text.strip()
        
        assert actual_text == self.expected_text, \
            f"Expected '{self.expected_text}' but got '{actual_text}' in {self.description}"
            
        print(f"🎬 {actor.name} sees expected text '{self.expected_text}' in {self.description}")
        return True

class Url:
    """Question to verify current URL"""
    
    def __init__(self, expected_url: str, contains: bool = False):
        self.expected_url = expected_url
        self.contains = contains
        
    def answered_by(self, actor: Actor) -> bool:
        """Answer the URL verification question"""
        browser = actor.uses_ability("browse_the_web")
        current_url = browser.get_current_url()
        
        if self.contains:
            assert self.expected_url in current_url, \
                f"Expected URL containing '{self.expected_url}' but got '{current_url}'"
        else:
            assert current_url == self.expected_url, \
                f"Expected URL '{self.expected_url}' but got '{current_url}'"
                
        print(f"🎬 {actor.name} is on expected URL: {current_url}")
        return True

class Title:
    """Question to verify page title"""
    
    def __init__(self, expected_title: str):
        self.expected_title = expected_title
        
    def answered_by(self, actor: Actor) -> bool:
        """Answer the title verification question"""
        browser = actor.uses_ability("browse_the_web")
        current_title = browser.get_page_title()
        
        assert current_title == self.expected_title, \
            f"Expected title '{self.expected_title}' but got '{current_title}'"
            
        print(f"🎬 {actor.name} sees expected title: {current_title}")
        return True

# ==================== FLUENT INTERFACE BUILDERS ====================

class AuthenticationTasks:
    """Fluent interface for authentication-related tasks"""
    
    @staticmethod
    def login_as(username: str, password: str):
        """Create login task sequence"""
        return [
            Enter(username, (By.ID, "username"), "username field"),
            Enter(password, (By.ID, "password"), "password field"),
            Click((By.ID, "login-button"), "login button")
        ]
        
    @staticmethod
    def logout():
        """Create logout task"""
        return Click((By.ID, "logout-button"), "logout button")

class NavigationTasks:
    """Fluent interface for navigation tasks"""
    
    @staticmethod
    def to_dashboard():
        """Navigate to dashboard"""
        return Click((By.LINK_TEXT, "Dashboard"), "dashboard link")
        
    @staticmethod
    def to_profile():
        """Navigate to profile"""
        return Click((By.LINK_TEXT, "Profile"), "profile link")

# ==================== PRACTICAL EXAMPLE IMPLEMENTATION ====================

def demonstrate_screenplay_pattern():
    """Demonstrate Screenplay Pattern implementation"""
    
    # This would typically be in your test setup
    from selenium import webdriver
    
    # Initialize browser (in real tests, this would come from fixtures)
    # driver = webdriver.Chrome()
    
    # Create actor
    user = Actor("Standard User")
    
    # Grant abilities (in real implementation, this would be in test setup)
    # browser_ability = BrowseTheWeb()
    # browser_ability.initialize(driver, "https://example.com")
    # user.can("browse_the_web", browser_ability)
    
    print("🎬 SCREENPLAY PATTERN DEMONSTRATION")
    print("=" * 50)
    
    # Example test scenario using Screenplay Pattern
    print("\n📝 Example Test Scenario:")
    print("Given a user wants to login to the system")
    print("When they provide valid credentials")
    print("Then they should be redirected to the dashboard")
    
    # This demonstrates the readability improvement:
    # Instead of: 
    # driver.find_element(By.ID, "username").send_keys("user")
    # driver.find_element(By.ID, "password").send_keys("pass")
    # driver.find_element(By.ID, "login-button").click()
    
    # We write:
    # user.attempts_to(*AuthenticationTasks.login_as("user", "pass"))
    # user.should_see_the(Url("/dashboard"))
    
    print("\n✅ Screenplay Pattern advantages demonstrated:")
    print("• User-centric language (natural sentences)")
    print("• Better separation of test logic and implementation")
    print("• Highly reusable task components")
    print("• Easy to read and maintain test scenarios")
    print("• Clear distinction between actions (Tasks) and verifications (Questions)")

# ==================== MIGRATION HELPER ====================

class PageObjectToScreenplayConverter:
    """Helper to convert existing Page Objects to Screenplay Pattern"""
    
    @staticmethod
    def convert_login_page():
        """Example conversion of traditional login page object"""
        
        print("🔄 PAGE OBJECT TO SCREENPLAY CONVERSION EXAMPLE")
        print("=" * 50)
        
        print("\nBEFORE (Traditional Page Object):")
        print("""
class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.username_field = (By.ID, "username")
        self.password_field = (By.ID, "password")
        self.login_button = (By.ID, "login-button")
    
    def enter_username(self, username):
        self.driver.find_element(*self.username_field).send_keys(username)
    
    def enter_password(self, password):
        self.driver.find_element(*self.password_field).send_keys(password)
    
    def click_login(self):
        self.driver.find_element(*self.login_button).click()
        
    def login(self, username, password):
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
        return DashboardPage(self.driver)
        """)
        
        print("\nAFTER (Screenplay Pattern):")
        print("""
# Tasks (Reusable actions)
class EnterUsername(Task):
    def __init__(self, username):
        self.username = username
    def perform_as(self, actor):
        browser = actor.uses_ability("browse_the_web")
        browser.find_element((By.ID, "username")).send_keys(self.username)

class EnterPassword(Task):
    def __init__(self, password):
        self.password = password
    def perform_as(self, actor):
        browser = actor.uses_ability("browse_the_web")
        browser.find_element((By.ID, "password")).send_keys(self.password)

class ClickLogin(Task):
    def perform_as(self, actor):
        browser = actor.uses_ability("browse_the_web")
        browser.find_element((By.ID, "login-button")).click()

# Fluent interface
class AuthenticationTasks:
    @staticmethod
    def login_as(username, password):
        return [EnterUsername(username), EnterPassword(password), ClickLogin()]

# Usage in test
user.attempts_to(*AuthenticationTasks.login_as("user", "pass"))
        """)

if __name__ == "__main__":
    demonstrate_screenplay_pattern()
    print("\n" + "=" * 50)
    PageObjectToScreenplayConverter.convert_login_page()