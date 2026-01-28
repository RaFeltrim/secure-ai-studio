#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⬅️➡️ SHIFT-LEFT/SHIFT-RIGHT TESTING STRATEGY
SDET Phase 4 Week 13 - Unit Test Integration and Production Monitoring

Enterprise-grade shift-left/shift-right testing implementation connecting
early-stage testing with production monitoring for continuous quality assurance.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import json
import subprocess
import time
import uuid
import requests
from kubernetes import client, config
import statistics

# ==================== SHIFT-LEFT/SHIFT-RIGHT FRAMEWORK ====================

@dataclass
class TestingStrategyConfig:
    """Configuration for shift-left/right testing strategy"""
    shift_left_enabled: bool = True
    shift_right_enabled: bool = True
    unit_test_coverage_threshold: float = 85.0
    production_monitoring_enabled: bool = True
    feedback_loop_interval: str = "5m"
    alert_thresholds: Dict[str, Any] = None

@dataclass
class TestFeedbackLoop:
    """Feedback loop between testing phases"""
    source_phase: str  # unit, integration, system, production
    target_phase: str
    feedback_type: str  # defect, performance, security, usability
    data_payload: Dict[str, Any]
    timestamp: str
    correlation_id: str

class UnitTestIntegrator:
    """Integrate unit testing early in development lifecycle"""
    
    def __init__(self):
        self.unit_test_results = []
        self.coverage_reports = []
        
    def integrate_unit_tests_early(self, code_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Integrate unit tests at early development stages"""
        
        print("🧪 Integrating Unit Tests Early in Development")
        print("=" * 55)
        
        integration_results = {
            'files_analyzed': len(code_changes),
            'tests_generated': 0,
            'coverage_improvement': 0,
            'defects_prevented': 0,
            'integration_timestamp': datetime.now().isoformat()
        }
        
        for change in code_changes:
            # Analyze code change for test opportunities
            test_opportunities = self._analyze_code_for_testing(change)
            
            # Generate unit tests
            generated_tests = self._generate_unit_tests(change, test_opportunities)
            integration_results['tests_generated'] += len(generated_tests)
            
            # Run tests immediately
            test_results = self._execute_unit_tests(generated_tests)
            self.unit_test_results.extend(test_results)
            
            # Calculate coverage impact
            coverage_impact = self._calculate_coverage_impact(test_results)
            integration_results['coverage_improvement'] += coverage_impact
            
            # Prevent defects through early testing
            prevented_defects = self._identify_prevented_defects(test_results)
            integration_results['defects_prevented'] += len(prevented_defects)
            
        print(f"✅ Unit Test Integration Complete")
        print(f"Tests Generated: {integration_results['tests_generated']}")
        print(f"Coverage Improvement: {integration_results['coverage_improvement']:.1f}%")
        print(f"Defects Prevented: {integration_results['defects_prevented']}")
        
        return integration_results
        
    def _analyze_code_for_testing(self, code_change: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze code changes to identify testing opportunities"""
        
        opportunities = []
        file_content = code_change.get('content', '')
        file_path = code_change.get('file_path', '')
        
        # Identify functions/methods
        function_patterns = ['def ', 'function ', 'public ', 'private ', 'protected ']
        for pattern in function_patterns:
            if pattern in file_content:
                opportunities.append({
                    'type': 'function_testing',
                    'scope': 'unit',
                    'complexity': self._assess_complexity(file_content)
                })
                
        # Identify edge cases
        if 'if ' in file_content or 'else' in file_content:
            opportunities.append({
                'type': 'branch_testing',
                'scope': 'unit',
                'complexity': 'medium'
            })
            
        # Identify error handling
        error_patterns = ['try:', 'except:', 'catch', 'throw', 'raise']
        if any(pattern in file_content for pattern in error_patterns):
            opportunities.append({
                'type': 'exception_testing',
                'scope': 'unit',
                'complexity': 'high'
            })
            
        return opportunities
        
    def _generate_unit_tests(self, code_change: Dict[str, Any], 
                           opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate unit tests based on code analysis"""
        
        generated_tests = []
        file_path = code_change.get('file_path', '')
        
        for opportunity in opportunities:
            if opportunity['type'] == 'function_testing':
                test_case = {
                    'name': f"test_{Path(file_path).stem}_functionality",
                    'type': 'unit',
                    'scope': 'function',
                    'complexity': opportunity['complexity'],
                    'generated_from': file_path,
                    'test_content': self._create_function_test_template(file_path)
                }
                generated_tests.append(test_case)
                
            elif opportunity['type'] == 'branch_testing':
                test_case = {
                    'name': f"test_{Path(file_path).stem}_branch_coverage",
                    'type': 'unit',
                    'scope': 'branch',
                    'complexity': 'medium',
                    'generated_from': file_path,
                    'test_content': self._create_branch_test_template(file_path)
                }
                generated_tests.append(test_case)
                
            elif opportunity['type'] == 'exception_testing':
                test_case = {
                    'name': f"test_{Path(file_path).stem}_exception_handling",
                    'type': 'unit',
                    'scope': 'exception',
                    'complexity': 'high',
                    'generated_from': file_path,
                    'test_content': self._create_exception_test_template(file_path)
                }
                generated_tests.append(test_case)
                
        return generated_tests
        
    def _execute_unit_tests(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute generated unit tests"""
        
        results = []
        
        for test_case in test_cases:
            # Simulate test execution
            execution_result = {
                'test_name': test_case['name'],
                'status': 'passed',  # Assume passing for demo
                'duration_ms': 150 + (len(test_case['test_content']) % 100),
                'assertions': 3,
                'coverage_lines': 12,
                'timestamp': datetime.now().isoformat(),
                'file_path': test_case['generated_from']
            }
            
            # Add some failures for realism
            import random
            if random.random() < 0.1:  # 10% failure rate
                execution_result['status'] = 'failed'
                execution_result['error'] = 'AssertionError: Expected true but got false'
                
            results.append(execution_result)
            
        return results
        
    def _calculate_coverage_impact(self, test_results: List[Dict[str, Any]]) -> float:
        """Calculate coverage improvement from new tests"""
        passed_tests = [r for r in test_results if r['status'] == 'passed']
        return len(passed_tests) * 0.5  # 0.5% coverage per passing test (simulated)
        
    def _identify_prevented_defects(self, test_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify defects prevented through unit testing"""
        failed_tests = [r for r in test_results if r['status'] == 'failed']
        return failed_tests  # Failed tests indicate prevented defects

# ==================== PRODUCTION MONITORING INTEGRATION ====================

class ProductionMonitoringIntegrator:
    """Integrate production monitoring with testing feedback loops"""
    
    def __init__(self):
        self.production_metrics = []
        self.feedback_loops = []
        
    def establish_shift_right_monitoring(self, 
                                       monitoring_targets: List[str]) -> Dict[str, Any]:
        """Establish production monitoring for shift-right testing"""
        
        print("📊 Establishing Production Monitoring")
        print("=" * 45)
        
        monitoring_setup = {
            'targets_configured': len(monitoring_targets),
            'metrics_collected': 0,
            'alerts_configured': 0,
            'feedback_channels': 0,
            'setup_timestamp': datetime.now().isoformat()
        }
        
        # Configure monitoring for each target
        for target in monitoring_targets:
            # Setup production metrics collection
            metrics_config = self._configure_production_metrics(target)
            self.production_metrics.append(metrics_config)
            monitoring_setup['metrics_collected'] += len(metrics_config['metrics'])
            
            # Configure alerts
            alert_config = self._configure_production_alerts(target)
            monitoring_setup['alerts_configured'] += len(alert_config['alerts'])
            
            # Establish feedback channels
            feedback_channel = self._establish_feedback_channel(target)
            self.feedback_loops.append(feedback_channel)
            monitoring_setup['feedback_channels'] += 1
            
        print(f"✅ Production Monitoring Established")
        print(f"Targets: {monitoring_setup['targets_configured']}")
        print(f"Metrics: {monitoring_setup['metrics_collected']}")
        print(f"Alerts: {monitoring_setup['alerts_configured']}")
        print(f"Feedback Channels: {monitoring_setup['feedback_channels']}")
        
        return monitoring_setup
        
    def collect_production_feedback(self, time_window: str = "1h") -> List[TestFeedbackLoop]:
        """Collect feedback from production monitoring"""
        
        feedback_loops = []
        
        # Simulate collecting production data
        production_data = self._simulate_production_data_collection(time_window)
        
        # Analyze for testing insights
        testing_insights = self._analyze_production_for_testing(production_data)
        
        # Create feedback loops
        for insight in testing_insights:
            feedback_loop = TestFeedbackLoop(
                source_phase='production',
                target_phase=insight['target_phase'],
                feedback_type=insight['feedback_type'],
                data_payload=insight['data'],
                timestamp=datetime.now().isoformat(),
                correlation_id=str(uuid.uuid4())
            )
            feedback_loops.append(feedback_loop)
            self.feedback_loops.append(feedback_loop)
            
        return feedback_loops
        
    def _configure_production_metrics(self, target: str) -> Dict[str, Any]:
        """Configure production metrics collection"""
        
        metrics_config = {
            'target': target,
            'metrics': [
                {
                    'name': 'response_time_p95',
                    'type': 'histogram',
                    'threshold': 2000,  # ms
                    'collection_interval': '30s'
                },
                {
                    'name': 'error_rate',
                    'type': 'gauge',
                    'threshold': 0.05,  # 5%
                    'collection_interval': '1m'
                },
                {
                    'name': 'throughput_rps',
                    'type': 'counter',
                    'threshold': 100,
                    'collection_interval': '1m'
                }
            ],
            'configured_at': datetime.now().isoformat()
        }
        
        return metrics_config
        
    def _configure_production_alerts(self, target: str) -> Dict[str, Any]:
        """Configure production alerting"""
        
        alert_config = {
            'target': target,
            'alerts': [
                {
                    'name': 'high_error_rate',
                    'condition': 'error_rate > 0.05',
                    'severity': 'warning',
                    'notification_channels': ['slack', 'email']
                },
                {
                    'name': 'slow_response_time',
                    'condition': 'response_time_p95 > 3000',
                    'severity': 'critical',
                    'notification_channels': ['pagerduty', 'slack']
                }
            ],
            'configured_at': datetime.now().isoformat()
        }
        
        return alert_config
        
    def _establish_feedback_channel(self, target: str) -> Dict[str, Any]:
        """Establish bidirectional feedback channel"""
        
        return {
            'channel_name': f'{target}_feedback_channel',
            'direction': 'bidirectional',
            'protocols': ['http', 'grpc'],
            'established_at': datetime.now().isoformat()
        }
        
    def _simulate_production_data_collection(self, time_window: str) -> Dict[str, Any]:
        """Simulate production data collection"""
        
        # Generate realistic production metrics
        return {
            'time_window': time_window,
            'metrics': {
                'avg_response_time': 1200 + (time.time() % 800),  # 1200-2000ms
                'error_rate': 0.01 + (time.time() % 0.04),       # 1-5%
                'requests_per_second': 50 + (time.time() % 150), # 50-200 RPS
                'cpu_utilization': 60 + (time.time() % 30),      # 60-90%
                'memory_usage': 70 + (time.time() % 20)          # 70-90%
            },
            'collected_at': datetime.now().isoformat()
        }
        
    def _analyze_production_for_testing(self, production_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze production data for testing insights"""
        
        insights = []
        metrics = production_data['metrics']
        
        # Performance degradation insight
        if metrics['avg_response_time'] > 1800:
            insights.append({
                'target_phase': 'performance_testing',
                'feedback_type': 'performance_degradation',
                'data': {
                    'current_response_time': metrics['avg_response_time'],
                    'threshold': 1800,
                    'recommendation': 'Increase performance test load'
                }
            })
            
        # Error rate increase insight
        if metrics['error_rate'] > 0.03:
            insights.append({
                'target_phase': 'integration_testing',
                'feedback_type': 'error_propagation',
                'data': {
                    'current_error_rate': metrics['error_rate'],
                    'threshold': 0.03,
                    'recommendation': 'Review integration test coverage'
                }
            })
            
        # Resource utilization insight
        if metrics['cpu_utilization'] > 85 or metrics['memory_usage'] > 85:
            insights.append({
                'target_phase': 'unit_testing',
                'feedback_type': 'resource_leak',
                'data': {
                    'cpu_usage': metrics['cpu_utilization'],
                    'memory_usage': metrics['memory_usage'],
                    'recommendation': 'Add resource leak detection tests'
                }
            })
            
        return insights

# ==================== FEEDBACK LOOP ORCHESTRATOR ====================

class FeedbackLoopOrchestrator:
    """Orchestrate feedback loops between testing phases"""
    
    def __init__(self, unit_integrator: UnitTestIntegrator,
                 monitoring_integrator: ProductionMonitoringIntegrator):
        self.unit_integrator = unit_integrator
        self.monitoring_integrator = monitoring_integrator
        self.orchestration_results = []
        
    def run_continuous_testing_cycle(self, development_cycle: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete continuous testing cycle with feedback loops"""
        
        print("🔄 Running Continuous Testing Cycle")
        print("=" * 45)
        
        cycle_start = datetime.now()
        
        # Phase 1: Shift-Left Integration
        print("\n⬅️  SHIFT-LEFT: Early Unit Testing")
        unit_integration = self.unit_integrator.integrate_unit_tests_early(
            development_cycle.get('code_changes', [])
        )
        
        # Phase 2: Production Monitoring Setup
        print("\n➡️  SHIFT-RIGHT: Production Monitoring")
        monitoring_setup = self.monitoring_integrator.establish_shift_right_monitoring(
            development_cycle.get('services', [])
        )
        
        # Phase 3: Production Feedback Collection
        print("\n🔄 FEEDBACK: Production Insights")
        feedback_loops = self.monitoring_integrator.collect_production_feedback("1h")
        
        # Phase 4: Feedback Loop Analysis
        print("\n📊 ANALYSIS: Cross-Phase Insights")
        cross_phase_insights = self._analyze_cross_phase_feedback(feedback_loops)
        
        cycle_end = datetime.now()
        
        cycle_result = {
            'cycle_id': str(uuid.uuid4()),
            'start_time': cycle_start.isoformat(),
            'end_time': cycle_end.isoformat(),
            'duration_seconds': (cycle_end - cycle_start).total_seconds(),
            'phases_executed': ['shift_left', 'shift_right', 'feedback_analysis'],
            'unit_integration': unit_integration,
            'monitoring_setup': monitoring_setup,
            'feedback_loops': len(feedback_loops),
            'cross_phase_insights': cross_phase_insights,
            'overall_effectiveness': self._calculate_cycle_effectiveness(
                unit_integration, monitoring_setup, len(feedback_loops)
            )
        }
        
        self.orchestration_results.append(cycle_result)
        
        print(f"\n✅ Continuous Testing Cycle Complete")
        print(f"Duration: {cycle_result['duration_seconds']:.2f}s")
        print(f"Feedback Loops: {cycle_result['feedback_loops']}")
        print(f"Effectiveness Score: {cycle_result['overall_effectiveness']:.1f}/100")
        
        return cycle_result
        
    def _analyze_cross_phase_feedback(self, feedback_loops: List[TestFeedbackLoop]) -> List[Dict[str, Any]]:
        """Analyze feedback across different testing phases"""
        
        insights = []
        
        # Group feedback by type
        feedback_by_type = {}
        for loop in feedback_loops:
            fb_type = loop.feedback_type
            if fb_type not in feedback_by_type:
                feedback_by_type[fb_type] = []
            feedback_by_type[fb_type].append(loop)
            
        # Generate cross-phase insights
        for fb_type, loops in feedback_by_type.items():
            if len(loops) > 1:
                insights.append({
                    'insight_type': 'cross_phase_correlation',
                    'feedback_type': fb_type,
                    'correlated_phases': list(set(loop.source_phase for loop in loops)),
                    'frequency': len(loops),
                    'recommendation': f'Strengthen {fb_type} testing across correlated phases'
                })
                
        # Identify improvement opportunities
        if feedback_by_type.get('performance_degradation'):
            insights.append({
                'insight_type': 'optimization_opportunity',
                'area': 'performance',
                'priority': 'high',
                'recommendation': 'Implement performance regression testing'
            })
            
        if feedback_by_type.get('error_propagation'):
            insights.append({
                'insight_type': 'quality_gap',
                'area': 'integration',
                'priority': 'medium',
                'recommendation': 'Enhance integration test coverage'
            })
            
        return insights
        
    def _calculate_cycle_effectiveness(self, unit_result: Dict[str, Any],
                                     monitoring_result: Dict[str, Any],
                                     feedback_count: int) -> float:
        """Calculate overall effectiveness score for testing cycle"""
        
        # Weighted scoring system
        unit_score = min(unit_result.get('coverage_improvement', 0) * 2, 30)  # Max 30 points
        defect_prevention_score = min(unit_result.get('defects_prevented', 0) * 5, 20)  # Max 20 points
        monitoring_score = min(monitoring_result.get('metrics_collected', 0), 25)  # Max 25 points
        feedback_score = min(feedback_count * 3, 25)  # Max 25 points
        
        total_score = unit_score + defect_prevention_score + monitoring_score + feedback_score
        return round(total_score, 1)

# ==================== CI/CD INTEGRATION ====================

class ShiftLeftRightCIPipeline:
    """Integrate shift-left/right strategy into CI/CD pipeline"""
    
    def __init__(self, orchestrator: FeedbackLoopOrchestrator):
        self.orchestrator = orchestrator
        self.pipeline_results = []
        
    def run_testing_strategy_gate(self, pipeline_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run shift-left/right testing strategy as CI/CD gate"""
        
        print("🔒 Running Shift-Left/Right Testing Strategy Gate")
        print("=" * 60)
        
        gate_start = datetime.now()
        
        # Execute continuous testing cycle
        cycle_result = self.orchestrator.run_continuous_testing_cycle(pipeline_context)
        
        # Evaluate gate criteria
        effectiveness_threshold = pipeline_context.get('effectiveness_threshold', 70.0)
        gate_passed = cycle_result['overall_effectiveness'] >= effectiveness_threshold
        
        gate_result = {
            'status': 'PASSED' if gate_passed else 'FAILED',
            'cycle_result': cycle_result,
            'threshold': effectiveness_threshold,
            'actual_score': cycle_result['overall_effectiveness'],
            'recommendations': self._generate_pipeline_recommendations(cycle_result),
            'start_time': gate_start.isoformat(),
            'end_time': datetime.now().isoformat()
        }
        
        self.pipeline_results.append(gate_result)
        
        status_icon = "✅" if gate_passed else "❌"
        print(f"{status_icon} Strategy Gate: {gate_result['status']}")
        print(f"Effectiveness Score: {gate_result['actual_score']:.1f}/{gate_result['threshold']}")
        
        if not gate_passed:
            print("📋 RECOMMENDATIONS:")
            for rec in gate_result['recommendations']:
                print(f"  • {rec}")
                
        return gate_result
        
    def _generate_pipeline_recommendations(self, cycle_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on cycle results"""
        
        recommendations = []
        effectiveness = cycle_result['overall_effectiveness']
        
        if effectiveness < 50:
            recommendations.append("Critical: Implement basic unit testing coverage")
            recommendations.append("Urgent: Establish production monitoring")
            
        elif effectiveness < 70:
            recommendations.append("Improve: Increase unit test coverage")
            recommendations.append("Enhance: Expand production metric collection")
            
        elif effectiveness < 85:
            recommendations.append("Optimize: Strengthen feedback loop mechanisms")
            recommendations.append("Refine: Improve cross-phase correlation analysis")
            
        else:
            recommendations.append("Maintain current testing strategy")
            recommendations.append("Consider advanced testing techniques")
            
        # Specific recommendations based on insights
        insights = cycle_result.get('cross_phase_insights', [])
        for insight in insights:
            if insight['insight_type'] == 'optimization_opportunity':
                recommendations.append(f"Priority: {insight['recommendation']}")
            elif insight['insight_type'] == 'quality_gap':
                recommendations.append(f"Address: {insight['recommendation']}")
                
        return recommendations

# ==================== DEMONSTRATION ====================

def demonstrate_shift_leftright_capabilities():
    """Demonstrate shift-left/shift-right testing capabilities"""
    
    print("⬅️➡️ SHIFT-LEFT/SHIFT-RIGHT TESTING STRATEGY")
    print("=" * 55)
    
    print("\nBEFORE - Traditional Testing Approach:")
    print("""
# Linear testing process
1. Developers write code
2. QA team tests after development
3. Deploy to production
4. Monitor for issues
5. Fix issues reactively
    """)
    
    print("\nAFTER - Continuous Testing Strategy:")
    print("""
orchestrator = FeedbackLoopOrchestrator(unit_integrator, monitoring_integrator)

# Shift-Left: Early testing integration
unit_results = unit_integrator.integrate_unit_tests_early(code_changes)

# Shift-Right: Production monitoring
monitoring_results = monitoring_integrator.establish_shift_right_monitoring(services)

# Continuous feedback loops
feedback = monitoring_integrator.collect_production_feedback()
insights = orchestrator.analyze_cross_phase_feedback(feedback)
    """)
    
    print("\n🎯 SHIFT-LEFT/SHIFT-RIGHT CAPABILITIES:")
    print("✅ Early Unit Test Integration")
    print("✅ Production Monitoring Setup")
    print("✅ Bidirectional Feedback Loops")
    print("✅ Cross-Phase Correlation Analysis")
    print("✅ Continuous Quality Improvement")
    print("✅ Automated Testing Strategy Gates")

def run_shift_leftright_demo():
    """Run complete shift-left/right demonstration"""
    
    print("\n🧪 SHIFT-LEFT/SHIFT-RIGHT TESTING DEMONSTRATION")
    print("=" * 60)
    
    # Initialize components
    unit_integrator = UnitTestIntegrator()
    monitoring_integrator = ProductionMonitoringIntegrator()
    orchestrator = FeedbackLoopOrchestrator(unit_integrator, monitoring_integrator)
    ci_pipeline = ShiftLeftRightCIPipeline(orchestrator)
    
    # Development cycle context
    development_cycle = {
        'code_changes': [
            {
                'file_path': 'core/api/user_controller.py',
                'content': '''
def get_user(user_id):
    if user_id <= 0:
        raise ValueError("Invalid user ID")
    return fetch_user_from_db(user_id)
                ''',
                'change_type': 'feature'
            },
            {
                'file_path': 'core/engine/content_generator.py',
                'content': '''
def generate_content(prompt, style="realistic"):
    if not prompt:
        raise ValueError("Prompt cannot be empty")
    return process_generation_request(prompt, style)
                ''',
                'change_type': 'enhancement'
            }
        ],
        'services': ['user-service', 'content-service', 'api-gateway'],
        'effectiveness_threshold': 75.0
    }
    
    # Run testing strategy gate
    gate_result = ci_pipeline.run_testing_strategy_gate(development_cycle)
    
    # Display results
    cycle_result = gate_result['cycle_result']
    
    print(f"\n📊 SHIFT-LEFT/SHIFT-RIGHT RESULTS:")
    print(f"Strategy Gate: {gate_result['status']}")
    print(f"Effectiveness Score: {gate_result['actual_score']:.1f}/{gate_result['threshold']}")
    
    print(f"\n📈 CYCLE BREAKDOWN:")
    unit_integration = cycle_result['unit_integration']
    print(f"Unit Tests Generated: {unit_integration['tests_generated']}")
    print(f"Coverage Improvement: {unit_integration['coverage_improvement']:.1f}%")
    print(f"Defects Prevented: {unit_integration['defects_prevented']}")
    
    monitoring_setup = cycle_result['monitoring_setup']
    print(f"Services Monitored: {monitoring_setup['targets_configured']}")
    print(f"Metrics Collected: {monitoring_setup['metrics_collected']}")
    print(f"Feedback Loops: {cycle_result['feedback_loops']}")
    
    if cycle_result['cross_phase_insights']:
        print(f"\n🔍 CROSS-PHASE INSIGHTS:")
        for insight in cycle_result['cross_phase_insights'][:3]:  # Top 3 insights
            print(f"  • {insight['insight_type']}: {insight['recommendation']}")
    
    return {
        'gate_result': gate_result,
        'cycle_result': cycle_result
    }

if __name__ == "__main__":
    demonstrate_shift_leftright_capabilities()
    print("\n" + "=" * 65)
    run_shift_leftright_demo()