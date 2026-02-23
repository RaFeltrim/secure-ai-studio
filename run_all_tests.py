#!/usr/bin/env python3
"""
Comprehensive Test Runner for Secure AI Studio
Executes all tests in the proper sequence and generates reports.
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path


def run_command(cmd, description, cwd=None):
    """Run a command and return the result."""
    print(f"\n🧪 {description}")
    print(f"   Command: {cmd}")
    
    start_time = time.time()
    result = subprocess.run(
        cmd, 
        shell=True, 
        capture_output=True, 
        text=True, 
        cwd=cwd
    )
    end_time = time.time()
    
    duration = round(end_time - start_time, 2)
    print(f"   Duration: {duration}s")
    
    if result.returncode == 0:
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")
        print(f"   STDOUT: {result.stdout[:500]}...")
        print(f"   STDERR: {result.stderr[:500]}...")
        
    return result.returncode == 0, result.stdout, result.stderr, duration


def main():
    """Main test execution function."""
    print("🚀 Starting Comprehensive Test Suite for Secure AI Studio")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Python: {sys.version}")
    print(f"🎯 Working Directory: {os.getcwd()}")
    
    # Set environment for testing
    os.environ['FLASK_TESTING'] = 'true'
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['LUMAAI_API_KEY'] = 'test_key_for_testing'
    os.environ['DATA_RETENTION_POLICY'] = 'ZERO'
    os.environ['FLASK_SECRET_KEY'] = 'test_secret_key'
    
    results = {}
    start_total_time = time.time()
    
    # Test 1: Unit Tests
    unit_test_dir = os.path.join(os.getcwd(), 'tests', 'unit')
    if os.path.exists(unit_test_dir) and any(fname.endswith('.py') for fname in os.listdir(unit_test_dir)):
        success, stdout, stderr, duration = run_command(
            "python -m pytest tests/unit/ -v --tb=short",
            "Running Unit Tests",
            cwd=os.getcwd()
        )
    else:
        print("\n🧪 Running Unit Tests")
        print("   No unit tests found, skipping")
        success, stdout, stderr, duration = True, "No unit tests", "", 0.0
    results['Unit Tests'] = {
        'success': success,
        'stdout': stdout,
        'stderr': stderr,
        'duration': duration
    }
    
    # Test 2: Security Tests
    success, stdout, stderr, duration = run_command(
        "python -m pytest tests/test_security_utils.py tests/test_luma_service.py -v --tb=short",
        "Running Security Tests",
        cwd=os.getcwd()
    )
    results['Security Tests'] = {
        'success': success,
        'stdout': stdout,
        'stderr': stderr,
        'duration': duration
    }
    
    # Test 3: API Endpoint Tests
    success, stdout, stderr, duration = run_command(
        "python -m pytest tests/test_api_endpoints.py -v --tb=short",
        "Running API Endpoint Tests",
        cwd=os.getcwd()
    )
    results['API Endpoint Tests'] = {
        'success': success,
        'stdout': stdout,
        'stderr': stderr,
        'duration': duration
    }
    
    # Test 4: Integration Tests
    success, stdout, stderr, duration = run_command(
        "python -m pytest tests/test_main_app.py -v --tb=short",
        "Running Integration Tests",
        cwd=os.getcwd()
    )
    results['Integration Tests'] = {
        'success': success,
        'stdout': stdout,
        'stderr': stderr,
        'duration': duration
    }
    
    # Test 5: Overall Functionality Tests
    success, stdout, stderr, duration = run_command(
        "python -m pytest tests/test_basic_functionality.py -v --tb=short",
        "Running Basic Functionality Tests",
        cwd=os.getcwd()
    )
    results['Basic Functionality Tests'] = {
        'success': success,
        'stdout': stdout,
        'stderr': stderr,
        'duration': duration
    }
    
    # Calculate total time
    total_time = round(time.time() - start_total_time, 2)
    
    # Generate summary
    print("\n" + "="*60)
    print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, data in results.items():
        status = "✅ PASS" if data['success'] else "❌ FAIL"
        print(f"{test_name:<30} {status:<10} ({data['duration']}s)")
        if not data['success']:
            all_passed = False
    
    print(f"\nTotal Execution Time: {total_time}s")
    print("-"*60)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Secure AI Studio is ready for production")
        print("🔒 Security measures validated")
        print("⚙️  All components functioning properly")
        exit_code = 0
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️  Please address failing tests before production")
        exit_code = 1
    
    # Generate detailed report
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'total_duration': total_time,
        'all_passed': all_passed,
        'results': results
    }
    
    report_path = Path("test_report.json")
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📋 Detailed test report saved to: {report_path.absolute()}")
    
    # Also save a simple summary
    summary_path = Path("test_results_summary.txt")
    with open(summary_path, 'w') as f:
        f.write(f"Secure AI Studio - Test Results Summary\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Python Version: {sys.version.split()[0]}\n\n")
        
        for test_name, data in results.items():
            status = "PASS" if data['success'] else "FAIL"
            f.write(f"{test_name}: {status} ({data['duration']}s)\n")
        
        f.write(f"\nTotal Duration: {total_time}s\n")
        f.write(f"Overall Status: {'SUCCESS' if all_passed else 'FAILURE'}\n")
    
    print(f"📋 Summary report saved to: {summary_path.absolute()}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())