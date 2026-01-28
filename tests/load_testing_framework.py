#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Load Testing Framework
k6 integration for performance benchmarking across different resolutions

Features:
- Multi-resolution load testing
- Concurrent user simulation
- Performance metrics collection
- Comparative analysis reports
- Stress testing capabilities
"""

import subprocess
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

@dataclass
class LoadTestConfig:
    """Load test configuration"""
    duration: str = "2m"  # Test duration
    virtual_users: int = 10  # Number of virtual users
    ramp_up_time: str = "30s"  # Ramp-up period
    test_scenarios: List[Dict[str, Any]] = None
    output_format: str = "json"  # json, csv, influxdb

@dataclass
class TestScenario:
    """Individual test scenario"""
    name: str
    resolution: tuple  # (width, height)
    content_type: str  # "image" or "video"
    batch_size: int = 1
    complexity: str = "basic"  # basic, medium, complex

class K6LoadTester:
    """
    k6 load testing integration
    """
    
    def __init__(self, k6_path: str = "k6", results_dir: str = "tests/load_test_results"):
        """Initialize load tester"""
        self.k6_path = k6_path
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logging()
        
        # Default test scenarios
        self.default_scenarios = [
            TestScenario("small_basic", (256, 256), "image", 1, "basic"),
            TestScenario("medium_basic", (512, 512), "image", 1, "basic"),
            TestScenario("large_basic", (1024, 1024), "image", 1, "basic"),
            TestScenario("small_complex", (256, 256), "image", 1, "complex"),
            TestScenario("medium_complex", (512, 512), "image", 1, "complex"),
            TestScenario("large_complex", (1024, 1024), "image", 1, "complex"),
            TestScenario("batch_processing", (512, 512), "image", 5, "basic"),
        ]
        
        self.logger.info("🏋️ K6 Load Tester initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('LoadTester')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def generate_k6_script(self, scenarios: List[TestScenario], 
                          config: LoadTestConfig) -> str:
        """Generate k6 JavaScript test script"""
        
        # Convert scenarios to JS format
        js_scenarios = []
        for scenario in scenarios:
            js_scenarios.append(f"""
    "{scenario.name}": {{
        executor: "constant-vus",
        vus: {config.virtual_users},
        duration: "{config.duration}",
        gracefulStop: "30s",
        exec: "generate{scenario.name.replace('_', '')}"
    }}""")
        
        scenarios_js = ",".join(js_scenarios)
        
        # Generate function definitions for each scenario
        functions_js = []
        for scenario in scenarios:
            func_name = f"generate{scenario.name.replace('_', '')}"
            functions_js.append(f"""
export function {func_name}() {{
    const payload = {{
        content_type: "{scenario.content_type}",
        prompt: "Test image generation {scenario.complexity}",
        dimensions: [{scenario.resolution[0]}, {scenario.resolution[1]}],
        format: "PNG",
        quality: "HIGH",
        batch_size: {scenario.batch_size}
    }};
    
    const res = http.post("http://localhost:8000/generate", JSON.stringify(payload), {{
        headers: {{ "Content-Type": "application/json" }}
    }});
    
    check(res, {{
        "status is 200": (r) => r.status === 200,
        "response time < 30s": (r) => r.timings.duration < 30000
    }});
    
    // Add some delay between requests
    sleep(Math.random() * 2 + 1);
}}""")
        
        functions_js_str = "\n".join(functions_js)
        
        # Complete k6 script
        k6_script = f"""
import http from "k6/http";
import {{ check, sleep }} from "k6";

export const options = {{
    scenarios: {{{scenarios_js}
    }},
    thresholds: {{
        http_req_duration: ["p(95)<30000"],  // 95% of requests should be below 30s
        http_req_failed: ["rate<0.01"],     // Error rate should be less than 1%
    }}
}};

{functions_js_str}

export function setup() {{
    console.log("🚀 Starting load test with {len(scenarios)} scenarios");
    return {{ test_start_time: Date.now() }};
}}

export function teardown(data) {{
    console.log("🏁 Load test completed");
}}
"""
        return k6_script
    
    def run_load_test(self, scenarios: List[TestScenario] = None, 
                     config: LoadTestConfig = None) -> Dict[str, Any]:
        """Run load test using k6"""
        scenarios = scenarios or self.default_scenarios
        config = config or LoadTestConfig()
        
        # Generate test script
        test_script = self.generate_k6_script(scenarios, config)
        script_path = self.results_dir / f"load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.js"
        
        with open(script_path, 'w') as f:
            f.write(test_script)
        
        self.logger.info(f"📝 Generated k6 script: {script_path}")
        
        # Prepare k6 command
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_path = self.results_dir / f"results_{timestamp}.json"
        
        cmd = [
            self.k6_path,
            "run",
            str(script_path),
            "--out", f"json={results_path}",
            "--summary-export", str(self.results_dir / f"summary_{timestamp}.json")
        ]
        
        self.logger.info("🏃 Running load test...")
        self.logger.info(f"Command: {' '.join(cmd)}")
        
        try:
            # Run k6 test
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                self.logger.info("✅ Load test completed successfully")
                return self._process_test_results(results_path, execution_time, scenarios)
            else:
                self.logger.error(f"❌ Load test failed: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr,
                    'execution_time': execution_time
                }
                
        except subprocess.TimeoutExpired:
            self.logger.error("⏰ Load test timed out")
            return {
                'success': False,
                'error': 'Test timed out after 1 hour',
                'execution_time': 3600
            }
        except Exception as e:
            self.logger.error(f"❌ Load test error: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def _process_test_results(self, results_path: Path, 
                            execution_time: float, 
                            scenarios: List[TestScenario]) -> Dict[str, Any]:
        """Process and analyze test results"""
        try:
            # Read raw results
            with open(results_path, 'r') as f:
                raw_results = [json.loads(line) for line in f if line.strip()]
            
            # Extract metrics
            metrics = self._extract_metrics(raw_results)
            
            # Generate comparative analysis
            analysis = self._analyze_performance(metrics, scenarios)
            
            # Create visualization
            self._create_performance_charts(metrics, scenarios)
            
            return {
                'success': True,
                'execution_time': execution_time,
                'raw_results_path': str(results_path),
                'metrics': metrics,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to process results: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': execution_time
            }
    
    def _extract_metrics(self, raw_results: List[Dict]) -> Dict[str, Any]:
        """Extract performance metrics from raw results"""
        http_metrics = [r for r in raw_results if r.get('type') == 'HTTP']
        
        if not http_metrics:
            return {'error': 'No HTTP metrics found'}
        
        # Calculate response times
        response_times = [m['value'] for m in http_metrics if m.get('metric') == 'http_req_duration']
        status_codes = [m['value'] for m in http_metrics if m.get('metric') == 'http_req_status']
        
        return {
            'total_requests': len(http_metrics),
            'successful_requests': len([s for s in status_codes if str(s).startswith('2')]),
            'error_rate': 1 - (len([s for s in status_codes if str(s).startswith('2')]) / len(status_codes)) if status_codes else 1,
            'avg_response_time': np.mean(response_times) if response_times else 0,
            'median_response_time': np.median(response_times) if response_times else 0,
            'p95_response_time': np.percentile(response_times, 95) if response_times else 0,
            'p99_response_time': np.percentile(response_times, 99) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'requests_per_second': len(http_metrics) / (max(response_times) / 1000) if response_times else 0
        }
    
    def _analyze_performance(self, metrics: Dict[str, Any], 
                           scenarios: List[TestScenario]) -> Dict[str, Any]:
        """Analyze performance and create comparative report"""
        analysis = {
            'overall_performance': 'GOOD' if metrics.get('error_rate', 1) < 0.05 else 'POOR',
            'bottlenecks_identified': [],
            'recommendations': []
        }
        
        # Check response time thresholds
        p95_time = metrics.get('p95_response_time', 0)
        if p95_time > 30000:  # 30 seconds
            analysis['bottlenecks_identified'].append('High response times detected')
            analysis['recommendations'].append('Consider optimizing generation algorithms')
        
        # Check error rates
        error_rate = metrics.get('error_rate', 1)
        if error_rate > 0.05:  # 5%
            analysis['bottlenecks_identified'].append('High error rate detected')
            analysis['recommendations'].append('Investigate system stability issues')
        
        # Resolution-based analysis
        resolution_analysis = {}
        for scenario in scenarios:
            resolution_key = f"{scenario.resolution[0]}x{scenario.resolution[1]}"
            if resolution_key not in resolution_analysis:
                resolution_analysis[resolution_key] = {
                    'scenarios': [],
                    'avg_time': 0
                }
            resolution_analysis[resolution_key]['scenarios'].append(scenario.name)
        
        analysis['resolution_performance'] = resolution_analysis
        
        return analysis
    
    def _create_performance_charts(self, metrics: Dict[str, Any], 
                                 scenarios: List[TestScenario]):
        """Create performance visualization charts"""
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Load Test Performance Analysis', fontsize=16)
            
            # Response time distribution
            response_times = [
                metrics.get('min_response_time', 0),
                metrics.get('avg_response_time', 0),
                metrics.get('median_response_time', 0),
                metrics.get('p95_response_time', 0),
                metrics.get('max_response_time', 0)
            ]
            
            percentiles = ['Min', 'Avg', 'Median', '95th', 'Max']
            bars = ax1.bar(range(len(percentiles)), response_times, color=['blue', 'green', 'orange', 'red', 'purple'])
            ax1.set_title('Response Time Percentiles (ms)')
            ax1.set_xlabel('Percentile')
            ax1.set_ylabel('Response Time (ms)')
            ax1.set_xticks(range(len(percentiles)))
            ax1.set_xticklabels(percentiles)
            
            # Add value labels on bars
            for bar, value in zip(bars, response_times):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                        f'{value:.0f}', ha='center', va='bottom')
            
            # Error rate
            error_rate = metrics.get('error_rate', 0)
            success_rate = 1 - error_rate
            
            ax2.pie([success_rate, error_rate], labels=['Success', 'Error'], 
                   autopct='%1.1f%%', colors=['green', 'red'])
            ax2.set_title('Request Success Rate')
            
            # Throughput
            rps = metrics.get('requests_per_second', 0)
            ax3.bar(['Requests/sec'], [rps], color='blue')
            ax3.set_title('Throughput')
            ax3.set_ylabel('Requests per Second')
            ax3.text(0, rps + 0.1, f'{rps:.2f}', ha='center', va='bottom')
            
            # Scenario distribution (simplified)
            scenario_counts = {}
            for scenario in scenarios:
                res_key = f"{scenario.resolution[0]}x{scenario.resolution[1]}"
                scenario_counts[res_key] = scenario_counts.get(res_key, 0) + 1
            
            ax4.bar(scenario_counts.keys(), scenario_counts.values(), color='orange')
            ax4.set_title('Test Scenarios by Resolution')
            ax4.set_ylabel('Number of Scenarios')
            ax4.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Save chart
            chart_path = self.results_dir / f"performance_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"📊 Performance chart saved: {chart_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create charts: {e}")
    
    def run_comparative_test(self, resolution_sets: List[List[tuple]]) -> Dict[str, Any]:
        """Run comparative tests across different resolution sets"""
        comparative_results = {}
        
        for i, resolutions in enumerate(resolution_sets):
            self.logger.info(f"🔄 Running test set {i+1}/{len(resolution_sets)}")
            
            # Create scenarios for this resolution set
            scenarios = []
            for j, resolution in enumerate(resolutions):
                scenarios.append(TestScenario(
                    f"set{i}_res{j}", resolution, "image", 1, "basic"
                ))
            
            # Run test
            config = LoadTestConfig(duration="1m", virtual_users=5)
            result = self.run_load_test(scenarios, config)
            
            comparative_results[f"set_{i}"] = {
                'resolutions': resolutions,
                'result': result
            }
            
            # Brief pause between tests
            time.sleep(10)
        
        # Generate comparative report
        report = self._generate_comparative_report(comparative_results)
        return report
    
    def _generate_comparative_report(self, comparative_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparative performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_sets': {},
            'comparison_summary': {}
        }
        
        # Process each test set
        performance_data = []
        for set_name, set_data in comparative_results.items():
            result = set_data['result']
            if result.get('success'):
                metrics = result.get('metrics', {})
                avg_time = metrics.get('avg_response_time', 0)
                error_rate = metrics.get('error_rate', 1)
                
                report['test_sets'][set_name] = {
                    'resolutions': set_data['resolutions'],
                    'avg_response_time': avg_time,
                    'error_rate': error_rate,
                    'throughput': metrics.get('requests_per_second', 0)
                }
                
                performance_data.append({
                    'set': set_name,
                    'avg_time': avg_time,
                    'error_rate': error_rate
                })
        
        # Identify best/worst performing sets
        if performance_data:
            best_time_set = min(performance_data, key=lambda x: x['avg_time'])
            worst_time_set = max(performance_data, key=lambda x: x['avg_time'])
            best_error_set = min(performance_data, key=lambda x: x['error_rate'])
            
            report['comparison_summary'] = {
                'best_performance_by_time': best_time_set['set'],
                'worst_performance_by_time': worst_time_set['set'],
                'best_performance_by_errors': best_error_set['set'],
                'performance_trend': 'improving' if best_time_set['avg_time'] < worst_time_set['avg_time'] else 'degrading'
            }
        
        return report

# Example usage and test runner
def main():
    """Demo load testing functionality"""
    print("🏋️ LOAD TESTING FRAMEWORK DEMO")
    print("=" * 35)
    
    # Initialize tester
    tester = K6LoadTester()
    
    try:
        # Check if k6 is available
        try:
            subprocess.run(["k6", "version"], capture_output=True, check=True)
            print("✅ k6 found, proceeding with load test")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  k6 not found. Please install k6 from https://k6.io/")
            print("Running in simulation mode...")
            return simulate_load_test()
        
        # Run basic load test
        print("🏃 Running basic load test...")
        basic_scenarios = [
            TestScenario("small_image", (256, 256), "image", 1, "basic"),
            TestScenario("medium_image", (512, 512), "image", 1, "basic")
        ]
        
        config = LoadTestConfig(duration="30s", virtual_users=3)
        result = tester.run_load_test(basic_scenarios, config)
        
        if result['success']:
            print("✅ Load test completed successfully!")
            print(f"📊 Results:")
            metrics = result['metrics']
            print(f"   Total Requests: {metrics.get('total_requests', 0)}")
            print(f"   Success Rate: {(1-result.get('error_rate', 1))*100:.1f}%")
            print(f"   Avg Response Time: {metrics.get('avg_response_time', 0):.0f}ms")
            print(f"   95th Percentile: {metrics.get('p95_response_time', 0):.0f}ms")
            
            # Run comparative test
            print("\n🔄 Running comparative test...")
            resolution_sets = [
                [(256, 256), (512, 512)],  # Basic resolutions
                [(1024, 1024), (512, 512)]  # Higher resolutions
            ]
            
            comparative_result = tester.run_comparative_test(resolution_sets)
            print("📊 Comparative Analysis:")
            for set_name, set_data in comparative_result['test_sets'].items():
                print(f"   {set_name}: {set_data['avg_response_time']:.0f}ms avg")
            
        else:
            print(f"❌ Load test failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def simulate_load_test():
    """Simulate load test when k6 is not available"""
    print("🎭 Simulating load test results...")
    
    # Simulated results
    simulated_metrics = {
        'total_requests': 150,
        'successful_requests': 142,
        'error_rate': 0.053,
        'avg_response_time': 8500,
        'median_response_time': 7200,
        'p95_response_time': 18500,
        'p99_response_time': 25000,
        'min_response_time': 2100,
        'max_response_time': 32000,
        'requests_per_second': 2.5
    }
    
    print("📊 Simulated Results:")
    print(f"   Total Requests: {simulated_metrics['total_requests']}")
    print(f"   Success Rate: {(1-simulated_metrics['error_rate'])*100:.1f}%")
    print(f"   Avg Response Time: {simulated_metrics['avg_response_time']:.0f}ms")
    print(f"   95th Percentile: {simulated_metrics['p95_response_time']:.0f}ms")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)