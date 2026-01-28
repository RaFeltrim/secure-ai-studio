#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 CLEAN CODE & SOLID PRINCIPLES REFACTORING
SDET Phase 1 Week 2 - Refactoring 1000+ Line Test Framework

Applies Clean Code principles and SOLID design patterns to improve
maintainability, readability, and extensibility of existing test framework.

SOLID Principles Addressed:
- Single Responsibility Principle (SRP)
- Open/Closed Principle (OCP)  
- Liskov Substitution Principle (LSP)
- Interface Segregation Principle (ISP)
- Dependency Inversion Principle (DIP)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import json
import logging
from enum import Enum

# ==================== SINGLE RESPONSIBILITY PRINCIPLE ====================
# Each class has one reason to change

class TestLogger:
    """Single responsibility: Handle all test logging operations"""
    
    def __init__(self, log_level: int = logging.INFO):
        self.logger = self._configure_logger(log_level)
        
    def _configure_logger(self, log_level: int) -> logging.Logger:
        """Configure logger with proper formatting"""
        logger = logging.getLogger('SDET_Framework')
        logger.setLevel(log_level)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def info(self, message: str):
        self.logger.info(message)
        
    def error(self, message: str):
        self.logger.error(message)
        
    def debug(self, message: str):
        self.logger.debug(message)
        
    def warning(self, message: str):
        self.logger.warning(message)

class TestConfiguration:
    """Single responsibility: Manage test configuration and settings"""
    
    def __init__(self, config_file: str = "test_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_configuration()
        
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "test_directories": ["tests/unit", "tests/integration", "tests/e2e"],
            "output_directory": "test_results",
            "parallel_execution": True,
            "retry_attempts": 3,
            "timeout_seconds": 30,
            "report_formats": ["html", "json", "junit"]
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    default_config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                
        return default_config
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        
    def save(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

# ==================== OPEN/CLOSED PRINCIPLE ====================
# Open for extension, closed for modification

class TestReporter(ABC):
    """Abstract base class for test reporters - OCP compliant"""
    
    @abstractmethod
    def generate_report(self, test_results: List[Dict[str, Any]]) -> str:
        """Generate test report in specific format"""
        pass
        
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for this report format"""
        pass

class HTMLTestReporter(TestReporter):
    """HTML report generation - extends base reporter"""
    
    def generate_report(self, test_results: List[Dict[str, Any]]) -> str:
        """Generate HTML test report"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Results Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; }
                .test-result { margin: 10px 0; padding: 10px; border-left: 4px solid; }
                .passed { border-color: #4CAF50; background: #f1f8e9; }
                .failed { border-color: #f44336; background: #ffebee; }
                .skipped { border-color: #ff9800; background: #fff3e0; }
            </style>
        </head>
        <body>
            <h1>Test Results Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Tests: {total}</p>
                <p>Passed: {passed}</p>
                <p>Failed: {failed}</p>
                <p>Skipped: {skipped}</p>
                <p>Success Rate: {success_rate:.1f}%</p>
            </div>
            <h2>Detailed Results</h2>
            {test_details}
        </body>
        </html>
        """
        
        # Calculate summary statistics
        total = len(test_results)
        passed = sum(1 for result in test_results if result.get('status') == 'passed')
        failed = sum(1 for result in test_results if result.get('status') == 'failed')
        skipped = sum(1 for result in test_results if result.get('status') == 'skipped')
        success_rate = (passed / total * 100) if total > 0 else 0
        
        # Generate test details
        test_details = ""
        for result in test_results:
            css_class = result.get('status', 'skipped')
            test_details += f"""
            <div class="test-result {css_class}">
                <strong>{result.get('test_name', 'Unknown')}</strong><br>
                Status: {result.get('status', 'unknown')}<br>
                Duration: {result.get('duration', 0):.2f}s<br>
                {f"Error: {result.get('error', '')}" if result.get('error') else ""}
            </div>
            """
            
        return html_template.format(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            success_rate=success_rate,
            test_details=test_details
        )
        
    def get_file_extension(self) -> str:
        return ".html"

class JSONTestReporter(TestReporter):
    """JSON report generation - extends base reporter"""
    
    def generate_report(self, test_results: List[Dict[str, Any]]) -> str:
        """Generate JSON test report"""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(test_results),
                "passed": sum(1 for r in test_results if r.get('status') == 'passed'),
                "failed": sum(1 for r in test_results if r.get('status') == 'failed'),
                "skipped": sum(1 for r in test_results if r.get('status') == 'skipped')
            },
            "results": test_results
        }
        return json.dumps(report_data, indent=2)
        
    def get_file_extension(self) -> str:
        return ".json"

class JUnitTestReporter(TestReporter):
    """JUnit XML report generation - extends base reporter"""
    
    def generate_report(self, test_results: List[Dict[str, Any]]) -> str:
        """Generate JUnit XML test report"""
        xml_template = """<?xml version="1.0" encoding="UTF-8"?>
        <testsuites>
            <testsuite name="SDET Test Suite" 
                      tests="{total}" 
                      failures="{failed}" 
                      errors="0" 
                      skipped="{skipped}" 
                      time="{total_time}">
                {test_cases}
            </testsuite>
        </testsuites>
        """
        
        total = len(test_results)
        failed = sum(1 for r in test_results if r.get('status') == 'failed')
        skipped = sum(1 for r in test_results if r.get('status') == 'skipped')
        total_time = sum(r.get('duration', 0) for r in test_results)
        
        test_cases = ""
        for result in test_results:
            status = result.get('status', 'unknown')
            time_taken = result.get('duration', 0)
            
            if status == 'passed':
                test_cases += f'<testcase name="{result.get("test_name", "unknown")}" time="{time_taken}"/>\n'
            elif status == 'failed':
                test_cases += f'''<testcase name="{result.get("test_name", "unknown")}" time="{time_taken}">
                    <failure message="{result.get("error", "Test failed")}"/>
                </testcase>\n'''
            elif status == 'skipped':
                test_cases += f'<testcase name="{result.get("test_name", "unknown")}" time="{time_taken}">\n'
                test_cases += '    <skipped/>\n'
                test_cases += '</testcase>\n'
                
        return xml_template.format(
            total=total,
            failed=failed,
            skipped=skipped,
            total_time=round(total_time, 3),
            test_cases=test_cases
        )
        
    def get_file_extension(self) -> str:
        return ".xml"

# ==================== LISKOV SUBSTITUTION PRINCIPLE ====================
# Subtypes must be substitutable for their base types

class TestExecutor(ABC):
    """Abstract base class ensuring LSP compliance"""
    
    @abstractmethod
    def execute_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test case"""
        pass
        
    @abstractmethod
    def supports_parallel_execution(self) -> bool:
        """Indicate if executor supports parallel execution"""
        pass

class SequentialTestExecutor(TestExecutor):
    """Sequential test execution - LSP compliant implementation"""
    
    def __init__(self, logger: TestLogger):
        self.logger = logger
        
    def execute_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test sequentially"""
        start_time = datetime.now()
        
        try:
            # Simulate test execution
            self.logger.info(f"Executing test: {test_case.get('name')}")
            
            # In real implementation, this would call the actual test function
            # For demo, we'll simulate different outcomes
            import time
            import random
            
            execution_time = random.uniform(0.1, 2.0)
            time.sleep(min(execution_time, 0.1))  # Cap for faster demo
            
            # Simulate different test outcomes
            outcome = random.choices(
                ['passed', 'failed', 'skipped'], 
                weights=[0.8, 0.15, 0.05]
            )[0]
            
            result = {
                "test_name": test_case.get('name'),
                "status": outcome,
                "duration": round(execution_time, 3),
                "timestamp": datetime.now().isoformat()
            }
            
            if outcome == 'failed':
                result["error"] = "Assertion failed: Expected true but got false"
            elif outcome == 'skipped':
                result["reason"] = "Test prerequisites not met"
                
            self.logger.info(f"Test {test_case.get('name')} {outcome}")
            return result
            
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            return {
                "test_name": test_case.get('name'),
                "status": "failed",
                "duration": round((datetime.now() - start_time).total_seconds(), 3),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    def supports_parallel_execution(self) -> bool:
        return False

class ParallelTestExecutor(TestExecutor):
    """Parallel test execution - LSP compliant implementation"""
    
    def __init__(self, logger: TestLogger, max_workers: int = 4):
        self.logger = logger
        self.max_workers = max_workers
        
    def execute_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test (same interface as sequential)"""
        # Same implementation as sequential for LSP compliance
        # In practice, this would be coordinated by a thread pool
        executor = SequentialTestExecutor(self.logger)
        return executor.execute_test(test_case)
        
    def supports_parallel_execution(self) -> bool:
        return True
        
    def execute_batch(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple tests in parallel"""
        import concurrent.futures
        import threading
        
        self.logger.info(f"Starting parallel execution of {len(test_cases)} tests")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tests
            future_to_test = {
                executor.submit(self.execute_test, test_case): test_case 
                for test_case in test_cases
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_test):
                test_case = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Parallel execution error for {test_case.get('name')}: {e}")
                    results.append({
                        "test_name": test_case.get('name'),
                        "status": "failed",
                        "duration": 0,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                    
        self.logger.info(f"Parallel execution completed: {len(results)} results")
        return results

# ==================== INTERFACE SEGREGATION PRINCIPLE ====================
# Many client-specific interfaces are better than one general-purpose interface

class TestLifecycleListener(ABC):
    """Specific interface for test lifecycle events"""
    
    @abstractmethod
    def on_test_start(self, test_name: str):
        pass
        
    @abstractmethod
    def on_test_complete(self, test_result: Dict[str, Any]):
        pass

class TestFailureListener(ABC):
    """Specific interface for test failure events"""
    
    @abstractmethod
    def on_test_failure(self, test_name: str, error: str):
        pass

class TestPerformanceListener(ABC):
    """Specific interface for performance monitoring"""
    
    @abstractmethod
    def on_test_performance(self, test_name: str, duration: float):
        pass

class ComprehensiveTestListener(TestLifecycleListener, 
                               TestFailureListener, 
                               TestPerformanceListener):
    """Concrete implementation that handles all listener types"""
    
    def __init__(self, logger: TestLogger):
        self.logger = logger
        self.performance_data = []
        
    def on_test_start(self, test_name: str):
        self.logger.info(f"🚀 Starting test: {test_name}")
        
    def on_test_complete(self, test_result: Dict[str, Any]):
        status = test_result.get('status', 'unknown')
        self.logger.info(f"🏁 Test {test_result.get('test_name')} completed with status: {status}")
        
    def on_test_failure(self, test_name: str, error: str):
        self.logger.error(f"💥 Test {test_name} failed: {error}")
        
    def on_test_performance(self, test_name: str, duration: float):
        self.performance_data.append({"test": test_name, "duration": duration})
        if duration > 5.0:
            self.logger.warning(f"🐢 Slow test detected: {test_name} took {duration:.2f}s")

# ==================== DEPENDENCY INVERSION PRINCIPLE ====================
# Depend on abstractions, not concretions

T = TypeVar('T')

class TestResultStorage(ABC, Generic[T]):
    """Abstract storage interface - DIP compliant"""
    
    @abstractmethod
    def save_results(self, results: List[T]) -> bool:
        """Save test results"""
        pass
        
    @abstractmethod
    def load_results(self) -> List[T]:
        """Load test results"""
        pass

class FileSystemTestStorage(TestResultStorage[Dict[str, Any]]):
    """Concrete implementation using file system - depends on abstraction"""
    
    def __init__(self, storage_path: str = "test_results"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def save_results(self, results: List[Dict[str, Any]]) -> bool:
        """Save results to file system"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.storage_path / f"test_results_{timestamp}.json"
            
            with open(file_path, 'w') as f:
                json.dump(results, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Failed to save results: {e}")
            return False
            
    def load_results(self) -> List[Dict[str, Any]]:
        """Load results from file system"""
        results = []
        try:
            # Load most recent results file
            result_files = list(self.storage_path.glob("test_results_*.json"))
            if result_files:
                latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
                with open(latest_file, 'r') as f:
                    results = json.load(f)
        except Exception as e:
            print(f"Failed to load results: {e}")
            
        return results

class DatabaseTestStorage(TestResultStorage[Dict[str, Any]]):
    """Alternative implementation using database - same interface"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # Database initialization would go here
        
    def save_results(self, results: List[Dict[str, Any]]) -> bool:
        """Save results to database"""
        # Database save implementation
        return True  # Placeholder
        
    def load_results(self) -> List[Dict[str, Any]]:
        """Load results from database"""
        # Database load implementation
        return []  # Placeholder

# ==================== REFACTORED TEST FRAMEWORK ====================

class CleanCodeTestFramework:
    """Refactored test framework applying all SOLID principles"""
    
    def __init__(self, config: TestConfiguration = None):
        self.config = config or TestConfiguration()
        self.logger = TestLogger()
        self.reporters: Dict[str, TestReporter] = {}
        self.executor: Optional[TestExecutor] = None
        self.listeners: List[TestLifecycleListener] = []
        self.storage: TestResultStorage[Dict[str, Any]] = FileSystemTestStorage()
        
        # Register default reporters
        self._register_default_reporters()
        
        # Initialize executor based on configuration
        self._initialize_executor()
        
    def _register_default_reporters(self):
        """Register built-in report generators"""
        self.reporters['html'] = HTMLTestReporter()
        self.reporters['json'] = JSONTestReporter()
        self.reporters['junit'] = JUnitTestReporter()
        
    def _initialize_executor(self):
        """Initialize appropriate test executor"""
        if self.config.get('parallel_execution', False):
            self.executor = ParallelTestExecutor(self.logger)
        else:
            self.executor = SequentialTestExecutor(self.logger)
            
    def add_listener(self, listener: TestLifecycleListener):
        """Add test lifecycle listener"""
        self.listeners.append(listener)
        
    def set_storage(self, storage: TestResultStorage[Dict[str, Any]]):
        """Set result storage implementation"""
        self.storage = storage
        
    def register_reporter(self, format_name: str, reporter: TestReporter):
        """Register custom report generator"""
        self.reporters[format_name] = reporter
        
    def run_tests(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run test suite with all SOLID principles applied"""
        
        self.logger.info(f"Starting test execution: {len(test_cases)} tests")
        
        # Notify listeners of test start
        for listener in self.listeners:
            if hasattr(listener, 'on_test_start'):
                for test_case in test_cases:
                    listener.on_test_start(test_case.get('name'))
        
        # Execute tests
        if self.executor.supports_parallel_execution() and len(test_cases) > 1:
            executor = self.executor
            if isinstance(executor, ParallelTestExecutor):
                results = executor.execute_batch(test_cases)
            else:
                results = [executor.execute_test(tc) for tc in test_cases]
        else:
            results = [self.executor.execute_test(tc) for tc in test_cases]
            
        # Notify listeners of completion and performance
        for listener in self.listeners:
            for result in results:
                if hasattr(listener, 'on_test_complete'):
                    listener.on_test_complete(result)
                if hasattr(listener, 'on_test_performance'):
                    listener.on_test_performance(
                        result.get('test_name'), 
                        result.get('duration', 0)
                    )
                if result.get('status') == 'failed' and hasattr(listener, 'on_test_failure'):
                    listener.on_test_failure(
                        result.get('test_name'), 
                        result.get('error', 'Unknown error')
                    )
        
        # Store results
        self.storage.save_results(results)
        
        # Generate reports
        self._generate_reports(results)
        
        self.logger.info(f"Test execution completed: {len(results)} results")
        return results
        
    def _generate_reports(self, results: List[Dict[str, Any]]):
        """Generate configured report formats"""
        output_dir = Path(self.config.get('output_directory', 'test_results'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for format_name in self.config.get('report_formats', ['html']):
            if format_name in self.reporters:
                reporter = self.reporters[format_name]
                report_content = reporter.generate_report(results)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_file = output_dir / f"report_{timestamp}{reporter.get_file_extension()}"
                
                with open(report_file, 'w') as f:
                    f.write(report_content)
                    
                self.logger.info(f"Generated {format_name.upper()} report: {report_file}")

# ==================== DEMONSTRATION AND MIGRATION EXAMPLE ====================

def demonstrate_refactored_vs_traditional():
    """Demonstrate the improvement from traditional to refactored approach"""
    
    print("🧹 CLEAN CODE & SOLID PRINCIPLES REFACTORING")
    print("=" * 60)
    
    print("\nBEFORE - Traditional Monolithic Approach:")
    print("""
class TestRunner:
    def __init__(self):
        self.results = []
        self.log_file = open('test.log', 'w')
        
    def run_test(self, test_func):
        # Everything mixed together
        start_time = time.time()
        try:
            result = test_func()
            status = 'PASS' if result else 'FAIL'
            self.log_file.write(f"Test passed: {test_func.__name__}\\n")
        except Exception as e:
            status = 'ERROR'
            self.log_file.write(f"Test failed: {test_func.__name__} - {e}\\n")
            
        duration = time.time() - start_time
        self.results.append({
            'name': test_func.__name__,
            'status': status,
            'duration': duration
        })
        
    def generate_html_report(self):
        # Mixed reporting logic
        with open('report.html', 'w') as f:
            f.write('<html>...hardcoded HTML...</html>')
    """)
    
    print("\nAFTER - SOLID Refactored Approach:")
    print("""
# Separate responsibilities
logger = TestLogger()
storage = FileSystemTestStorage()
executor = ParallelTestExecutor(logger)
reporter = HTMLTestReporter()

# Compose functionality
framework = CleanCodeTestFramework()
framework.set_storage(storage)
framework.register_reporter('html', reporter)

# Clean execution
results = framework.run_tests(test_cases)
    """)
    
    print("\n🎯 SOLID PRINCIPLES APPLIED:")
    print("✅ Single Responsibility: Each class has one reason to change")
    print("✅ Open/Closed: Extend functionality without modifying existing code")
    print("✅ Liskov Substitution: Subtypes are fully substitutable")
    print("✅ Interface Segregation: Specific interfaces for specific clients")
    print("✅ Dependency Inversion: Depend on abstractions, not concretions")

def run_clean_code_demo():
    """Run demonstration of refactored framework"""
    
    print("\n🧪 CLEAN CODE FRAMEWORK DEMONSTRATION")
    print("=" * 50)
    
    # Create framework instance
    framework = CleanCodeTestFramework()
    
    # Add comprehensive listener
    listener = ComprehensiveTestListener(framework.logger)
    framework.add_listener(listener)
    
    # Define test cases
    test_cases = [
        {"name": "test_user_authentication", "type": "unit"},
        {"name": "test_content_generation", "type": "integration"},
        {"name": "test_api_endpoints", "type": "api"},
        {"name": "test_security_protocols", "type": "security"},
        {"name": "test_performance_benchmarks", "type": "performance"}
    ]
    
    # Run tests
    results = framework.run_tests(test_cases)
    
    # Show results summary
    passed = sum(1 for r in results if r['status'] == 'passed')
    failed = sum(1 for r in results if r['status'] == 'failed')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    
    return results

if __name__ == "__main__":
    demonstrate_refactored_vs_traditional()
    print("\n" + "=" * 60)
    run_clean_code_demo()