#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 DORA METRICS IMPLEMENTATION
SDET Phase 4 Week 14 - Deployment Frequency and Lead Time Measurement

Enterprise-grade DORA (DevOps Research and Assessment) metrics implementation
for measuring software delivery performance and continuous improvement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import json
import subprocess
import time
import uuid
import statistics
from collections import defaultdict

# ==================== DORA METRICS FRAMEWORK ====================

@dataclass
class DORAMetricsConfig:
    """Configuration for DORA metrics collection"""
    deployment_frequency_target: str = "weekly"  # daily, weekly, monthly
    lead_time_target_hours: float = 24.0
    change_failure_rate_target: float = 15.0  # percentage
    mttr_target_hours: float = 2.0
    data_collection_interval: str = "1h"
    reporting_granularity: str = "daily"

@dataclass
class DeploymentEvent:
    """Represents a deployment event for metrics tracking"""
    deployment_id: str
    service_name: str
    version: str
    environment: str
    deployed_at: str
    lead_time_seconds: float
    deployment_duration_seconds: float
    success: bool
    rollback_required: bool = False

@dataclass
class IncidentEvent:
    """Represents an incident for MTTR calculation"""
    incident_id: str
    service_name: str
    environment: str
    detected_at: str
    resolved_at: str
    severity: str
    root_cause: str
    mttr_seconds: float

class DORAMetricsCollector:
    """Collect and calculate DORA metrics from deployment and incident data"""
    
    def __init__(self, config: DORAMetricsConfig):
        self.config = config
        self.deployment_events = []
        self.incident_events = []
        self.metrics_history = []
        
    def record_deployment(self, deployment_event: DeploymentEvent):
        """Record a deployment event"""
        self.deployment_events.append(deployment_event)
        print(f"📊 Deployment recorded: {deployment_event.service_name} v{deployment_event.version}")
        
    def record_incident(self, incident_event: IncidentEvent):
        """Record an incident event"""
        self.incident_events.append(incident_event)
        print(f"⚠️  Incident recorded: {incident_event.incident_id} ({incident_event.severity})")
        
    def calculate_current_metrics(self, time_window_days: int = 30) -> Dict[str, Any]:
        """Calculate current DORA metrics for specified time window"""
        
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        cutoff_str = cutoff_date.isoformat()
        
        # Filter events within time window
        recent_deployments = [
            d for d in self.deployment_events 
            if d.deployed_at >= cutoff_str
        ]
        
        recent_incidents = [
            i for i in self.incident_events 
            if i.detected_at >= cutoff_str
        ]
        
        # Calculate the four key DORA metrics
        deployment_frequency = self._calculate_deployment_frequency(recent_deployments)
        lead_time = self._calculate_lead_time(recent_deployments)
        change_failure_rate = self._calculate_change_failure_rate(recent_deployments)
        mttr = self._calculate_mttr(recent_incidents)
        
        current_metrics = {
            'calculation_period': f"Last {time_window_days} days",
            'calculation_timestamp': datetime.now().isoformat(),
            'deployment_frequency': deployment_frequency,
            'lead_time': lead_time,
            'change_failure_rate': change_failure_rate,
            'mttr': mttr,
            'performance_level': self._assess_performance_level(
                deployment_frequency, lead_time, change_failure_rate, mttr
            ),
            'improvement_opportunities': self._identify_improvement_opportunities(
                deployment_frequency, lead_time, change_failure_rate, mttr
            )
        }
        
        self.metrics_history.append(current_metrics)
        return current_metrics
        
    def _calculate_deployment_frequency(self, deployments: List[DeploymentEvent]) -> Dict[str, Any]:
        """Calculate deployment frequency metrics"""
        
        if not deployments:
            return {
                'frequency': 0,
                'deployments_per_day': 0,
                'deployments_per_week': 0,
                'trend': 'no_data'
            }
            
        # Count deployments by period
        deployment_dates = [datetime.fromisoformat(d.deployed_at).date() for d in deployments]
        unique_days = len(set(deployment_dates))
        unique_weeks = len(set(d.isocalendar()[:2] for d in [datetime.fromisoformat(dep.deployed_at) for dep in deployments]))
        
        total_deployments = len(deployments)
        
        frequency_data = {
            'total_deployments': total_deployments,
            'unique_deployment_days': unique_days,
            'unique_deployment_weeks': unique_weeks,
            'deployments_per_day': round(total_deployments / max(unique_days, 1), 2),
            'deployments_per_week': round(total_deployments / max(unique_weeks, 1), 2),
            'success_rate': round(
                (len([d for d in deployments if d.success]) / total_deployments) * 100, 2
            ) if total_deployments > 0 else 0
        }
        
        # Determine frequency category
        if frequency_data['deployments_per_week'] >= 5:
            frequency_data['category'] = 'Elite'
        elif frequency_data['deployments_per_week'] >= 1:
            frequency_data['category'] = 'High'
        elif frequency_data['deployments_per_week'] >= 0.14:  # Once per week
            frequency_data['category'] = 'Medium'
        else:
            frequency_data['category'] = 'Low'
            
        return frequency_data
        
    def _calculate_lead_time(self, deployments: List[DeploymentEvent]) -> Dict[str, Any]:
        """Calculate lead time for changes"""
        
        if not deployments:
            return {
                'avg_lead_time_hours': 0,
                'median_lead_time_hours': 0,
                'p95_lead_time_hours': 0,
                'trend': 'no_data'
            }
            
        lead_times_hours = [d.lead_time_seconds / 3600 for d in deployments]
        
        lead_time_data = {
            'avg_lead_time_hours': round(statistics.mean(lead_times_hours), 2),
            'median_lead_time_hours': round(statistics.median(lead_times_hours), 2),
            'min_lead_time_hours': round(min(lead_times_hours), 2),
            'max_lead_time_hours': round(max(lead_times_hours), 2),
            'p95_lead_time_hours': round(
                sorted(lead_times_hours)[int(len(lead_times_hours) * 0.95)], 2
            )
        }
        
        # Determine lead time category
        avg_hours = lead_time_data['avg_lead_time_hours']
        if avg_hours <= 1:
            lead_time_data['category'] = 'Elite'
        elif avg_hours <= 24:
            lead_time_data['category'] = 'High'
        elif avg_hours <= 168:  # 1 week
            lead_time_data['category'] = 'Medium'
        else:
            lead_time_data['category'] = 'Low'
            
        return lead_time_data
        
    def _calculate_change_failure_rate(self, deployments: List[DeploymentEvent]) -> Dict[str, Any]:
        """Calculate change failure rate"""
        
        if not deployments:
            return {
                'failure_rate_percent': 0,
                'failed_deployments': 0,
                'total_deployments': 0,
                'trend': 'no_data'
            }
            
        failed_deployments = [d for d in deployments if not d.success]
        total_deployments = len(deployments)
        
        failure_rate = (len(failed_deployments) / total_deployments) * 100 if total_deployments > 0 else 0
        
        failure_data = {
            'failure_rate_percent': round(failure_rate, 2),
            'failed_deployments': len(failed_deployments),
            'total_deployments': total_deployments,
            'rollback_rate_percent': round(
                (len([d for d in failed_deployments if d.rollback_required]) / max(len(failed_deployments), 1)) * 100, 2
            )
        }
        
        # Determine failure rate category
        if failure_rate <= 5:
            failure_data['category'] = 'Elite'
        elif failure_rate <= 15:
            failure_data['category'] = 'High'
        elif failure_rate <= 30:
            failure_data['category'] = 'Medium'
        else:
            failure_data['category'] = 'Low'
            
        return failure_data
        
    def _calculate_mttr(self, incidents: List[IncidentEvent]) -> Dict[str, Any]:
        """Calculate Mean Time to Recovery"""
        
        if not incidents:
            return {
                'avg_mttr_hours': 0,
                'median_mttr_hours': 0,
                'p95_mttr_hours': 0,
                'trend': 'no_data'
            }
            
        mttr_hours = [i.mttr_seconds / 3600 for i in incidents]
        
        mttr_data = {
            'avg_mttr_hours': round(statistics.mean(mttr_hours), 2),
            'median_mttr_hours': round(statistics.median(mttr_hours), 2),
            'min_mttr_hours': round(min(mttr_hours), 2),
            'max_mttr_hours': round(max(mttr_hours), 2),
            'p95_mttr_hours': round(
                sorted(mttr_hours)[int(len(mttr_hours) * 0.95)], 2
            ),
            'total_incidents': len(incidents)
        }
        
        # Determine MTTR category
        avg_hours = mttr_data['avg_mttr_hours']
        if avg_hours <= 1:
            mttr_data['category'] = 'Elite'
        elif avg_hours <= 24:
            mttr_data['category'] = 'High'
        elif avg_hours <= 168:  # 1 week
            mttr_data['category'] = 'Medium'
        else:
            mttr_data['category'] = 'Low'
            
        return mttr_data
        
    def _assess_performance_level(self, deployment_freq: Dict[str, Any],
                                lead_time: Dict[str, Any],
                                failure_rate: Dict[str, Any],
                                mttr: Dict[str, Any]) -> str:
        """Assess overall DORA performance level"""
        
        categories = [
            deployment_freq.get('category', 'Low'),
            lead_time.get('category', 'Low'),
            failure_rate.get('category', 'Low'),
            mttr.get('category', 'Low')
        ]
        
        # Count category levels
        elite_count = categories.count('Elite')
        high_count = categories.count('High')
        medium_count = categories.count('Medium')
        
        if elite_count >= 3:
            return 'Elite'
        elif elite_count + high_count >= 3:
            return 'High'
        elif elite_count + high_count + medium_count >= 3:
            return 'Medium'
        else:
            return 'Low'
            
    def _identify_improvement_opportunities(self, deployment_freq: Dict[str, Any],
                                          lead_time: Dict[str, Any],
                                          failure_rate: Dict[str, Any],
                                          mttr: Dict[str, Any]) -> List[str]:
        """Identify improvement opportunities based on metrics"""
        
        opportunities = []
        
        # Deployment frequency improvements
        if deployment_freq.get('category') in ['Medium', 'Low']:
            opportunities.append("Increase deployment frequency through automated pipelines")
            opportunities.append("Implement feature flags for safer deployments")
            
        # Lead time improvements
        if lead_time.get('category') in ['Medium', 'Low']:
            opportunities.append("Reduce lead time by optimizing build processes")
            opportunities.append("Implement trunk-based development practices")
            
        # Failure rate improvements
        if failure_rate.get('category') in ['Medium', 'Low']:
            opportunities.append("Improve testing coverage and quality gates")
            opportunities.append("Implement canary deployments for risk reduction")
            
        # MTTR improvements
        if mttr.get('category') in ['Medium', 'Low']:
            opportunities.append("Enhance monitoring and alerting capabilities")
            opportunities.append("Implement automated rollback mechanisms")
            
        return opportunities[:5]  # Return top 5 opportunities

# ==================== CI/CD INTEGRATION ====================

class DORACIPipelineIntegrator:
    """Integrate DORA metrics collection into CI/CD pipeline"""
    
    def __init__(self, metrics_collector: DORAMetricsCollector):
        self.metrics_collector = metrics_collector
        self.pipeline_integrations = []
        
    def integrate_with_deployment_pipeline(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate DORA metrics collection with deployment pipeline"""
        
        print("🔄 Integrating DORA Metrics with Deployment Pipeline")
        print("=" * 55)
        
        integration_config = {
            'pipeline_name': pipeline_config.get('name', 'default'),
            'environments_tracked': pipeline_config.get('environments', []),
            'metrics_collection_points': [],
            'automated_reporting_enabled': True,
            'integration_timestamp': datetime.now().isoformat()
        }
        
        # Setup deployment tracking
        deployment_tracking = self._setup_deployment_tracking(pipeline_config)
        integration_config['metrics_collection_points'].append(deployment_tracking)
        
        # Setup incident tracking
        incident_tracking = self._setup_incident_tracking(pipeline_config)
        integration_config['metrics_collection_points'].append(incident_tracking)
        
        # Configure automated reporting
        reporting_config = self._configure_automated_reporting(pipeline_config)
        integration_config['reporting_config'] = reporting_config
        
        self.pipeline_integrations.append(integration_config)
        
        print(f"✅ DORA Integration Complete")
        print(f"Pipeline: {integration_config['pipeline_name']}")
        print(f"Environments: {len(integration_config['environments_tracked'])}")
        print(f"Collection Points: {len(integration_config['metrics_collection_points'])}")
        
        return integration_config
        
    def _setup_deployment_tracking(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup automated deployment tracking"""
        
        return {
            'type': 'deployment_tracking',
            'trigger_events': ['deployment_success', 'deployment_failure'],
            'data_collected': [
                'deployment_timestamp',
                'service_name',
                'version',
                'environment',
                'deployment_duration',
                'success_status'
            ],
            'configured_at': datetime.now().isoformat()
        }
        
    def _setup_incident_tracking(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup automated incident tracking"""
        
        return {
            'type': 'incident_tracking',
            'trigger_events': ['incident_detected', 'incident_resolved'],
            'data_collected': [
                'incident_timestamp',
                'resolution_timestamp',
                'service_name',
                'environment',
                'severity',
                'root_cause'
            ],
            'configured_at': datetime.now().isoformat()
        }
        
    def _configure_automated_reporting(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure automated DORA metrics reporting"""
        
        return {
            'report_schedule': pipeline_config.get('reporting_schedule', 'daily'),
            'report_formats': ['dashboard', 'email', 'slack'],
            'stakeholders': pipeline_config.get('report_recipients', []),
            'configured_at': datetime.now().isoformat()
        }

# ==================== REPORTING AND VISUALIZATION ====================

class DORAMetricsReporter:
    """Generate DORA metrics reports and visualizations"""
    
    def __init__(self, metrics_collector: DORAMetricsCollector):
        self.metrics_collector = metrics_collector
        self.reports_generated = []
        
    def generate_comprehensive_report(self, time_window_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive DORA metrics report"""
        
        print("📊 Generating DORA Metrics Report")
        print("=" * 40)
        
        # Calculate current metrics
        current_metrics = self.metrics_collector.calculate_current_metrics(time_window_days)
        
        # Generate historical trend analysis
        trend_analysis = self._analyze_historical_trends()
        
        # Create performance benchmarking
        benchmark_comparison = self._compare_against_industry_benchmarks(current_metrics)
        
        report = {
            'report_id': str(uuid.uuid4()),
            'generated_at': datetime.now().isoformat(),
            'time_window_days': time_window_days,
            'current_metrics': current_metrics,
            'trend_analysis': trend_analysis,
            'benchmark_comparison': benchmark_comparison,
            'recommendations': self._generate_strategic_recommendations(current_metrics),
            'action_items': self._generate_action_items(current_metrics)
        }
        
        self.reports_generated.append(report)
        
        print(f"✅ Report Generated: {report['report_id']}")
        print(f"Performance Level: {current_metrics['performance_level']}")
        print(f"Improvement Opportunities: {len(current_metrics['improvement_opportunities'])}")
        
        return report
        
    def _analyze_historical_trends(self) -> Dict[str, Any]:
        """Analyze trends in historical metrics data"""
        
        if len(self.metrics_collector.metrics_history) < 2:
            return {'trend_analysis_available': False}
            
        recent_history = self.metrics_collector.metrics_history[-6:]  # Last 6 periods
        
        trends = {
            'deployment_frequency_trend': self._calculate_metric_trend(
                [h['deployment_frequency']['deployments_per_week'] for h in recent_history]
            ),
            'lead_time_trend': self._calculate_metric_trend(
                [h['lead_time']['avg_lead_time_hours'] for h in recent_history]
            ),
            'failure_rate_trend': self._calculate_metric_trend(
                [h['change_failure_rate']['failure_rate_percent'] for h in recent_history]
            ),
            'mttr_trend': self._calculate_metric_trend(
                [h['mttr']['avg_mttr_hours'] for h in recent_history]
            ),
            'periods_analyzed': len(recent_history)
        }
        
        return trends
        
    def _calculate_metric_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a metric"""
        
        if len(values) < 2:
            return 'insufficient_data'
            
        # Simple linear trend analysis
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg < first_avg * 0.9:  # 10% improvement
            return 'improving'
        elif second_avg > first_avg * 1.1:  # 10% degradation
            return 'degrading'
        else:
            return 'stable'
            
    def _compare_against_industry_benchmarks(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare metrics against industry benchmarks"""
        
        # Industry benchmarks (DORA research findings)
        benchmarks = {
            'Elite': {
                'deployment_frequency': '> 5/day',
                'lead_time': '< 1 hour',
                'failure_rate': '< 5%',
                'mttr': '< 1 hour'
            },
            'High': {
                'deployment_frequency': '1/day - 5/day',
                'lead_time': '1 hour - 1 day',
                'failure_rate': '5-15%',
                'mttr': '1 hour - 1 day'
            },
            'Medium': {
                'deployment_frequency': '1/week - 1/month',
                'lead_time': '1 day - 1 week',
                'failure_rate': '15-30%',
                'mttr': '1 day - 1 week'
            },
            'Low': {
                'deployment_frequency': '< 1/month',
                'lead_time': '> 1 week',
                'failure_rate': '> 30%',
                'mttr': '> 1 week'
            }
        }
        
        current_level = current_metrics['performance_level']
        
        return {
            'current_performance_level': current_level,
            'industry_benchmark': benchmarks.get(current_level, {}),
            'gap_analysis': self._perform_gap_analysis(current_metrics, benchmarks[current_level])
        }
        
    def _perform_gap_analysis(self, current_metrics: Dict[str, Any], 
                            benchmark: Dict[str, str]) -> List[Dict[str, Any]]:
        """Perform gap analysis against benchmarks"""
        
        gaps = []
        
        # Deployment frequency gap
        current_freq = current_metrics['deployment_frequency']['deployments_per_week']
        if current_freq < 1:  # Below high performer threshold
            gaps.append({
                'metric': 'deployment_frequency',
                'current_value': f"{current_freq:.2f}/week",
                'benchmark': benchmark['deployment_frequency'],
                'gap_size': 'significant',
                'improvement_needed': max(1 - current_freq, 0)
            })
            
        # Lead time gap
        current_lead_time = current_metrics['lead_time']['avg_lead_time_hours']
        if current_lead_time > 24:  # Above high performer threshold
            gaps.append({
                'metric': 'lead_time',
                'current_value': f"{current_lead_time:.2f} hours",
                'benchmark': benchmark['lead_time'],
                'gap_size': 'significant' if current_lead_time > 168 else 'moderate',
                'improvement_needed': max(current_lead_time - 24, 0)
            })
            
        return gaps
        
    def _generate_strategic_recommendations(self, current_metrics: Dict[str, Any]) -> List[str]:
        """Generate strategic recommendations based on metrics"""
        
        recommendations = []
        performance_level = current_metrics['performance_level']
        
        if performance_level == 'Elite':
            recommendations.append("Maintain current excellence while exploring innovation opportunities")
            recommendations.append("Share best practices across organization")
            
        elif performance_level == 'High':
            recommendations.append("Target Elite performance through continuous optimization")
            recommendations.append("Invest in advanced automation and monitoring")
            
        elif performance_level == 'Medium':
            recommendations.append("Prioritize deployment automation and pipeline improvements")
            recommendations.append("Strengthen testing and quality assurance processes")
            
        else:  # Low
            recommendations.append("Implement fundamental CI/CD practices immediately")
            recommendations.append("Focus on reducing lead time and failure rates")
            
        # Add specific recommendations from metrics analysis
        recommendations.extend(current_metrics['improvement_opportunities'])
        
        return recommendations[:6]  # Limit to 6 recommendations
        
    def _generate_action_items(self, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific action items with owners and timelines"""
        
        action_items = []
        opportunities = current_metrics['improvement_opportunities']
        
        for i, opportunity in enumerate(opportunities[:3]):  # Top 3 opportunities
            action_items.append({
                'action_item': opportunity,
                'priority': 'High' if i == 0 else 'Medium',
                'owner': 'Engineering Team',
                'timeline_weeks': 4,
                'success_criteria': 'Measurable improvement in relevant DORA metric',
                'dependencies': []
            })
            
        return action_items

# ==================== DEMONSTRATION ====================

def demonstrate_dora_metrics_capabilities():
    """Demonstrate DORA metrics implementation capabilities"""
    
    print("📊 DORA METRICS IMPLEMENTATION")
    print("=" * 40)
    
    print("\nBEFORE - Manual Metrics Tracking:")
    print("""
# Manual process
1. Manually count deployments
2. Guess lead times
3. Track incidents in spreadsheets
4. Generate quarterly reports
5. No real-time insights
    """)
    
    print("\nAFTER - Automated DORA Metrics:")
    print("""
collector = DORAMetricsCollector(config)

# Automatic deployment tracking
collector.record_deployment(DeploymentEvent(...))

# Automatic incident tracking  
collector.record_incident(IncidentEvent(...))

# Real-time metrics calculation
metrics = collector.calculate_current_metrics(30)
report = reporter.generate_comprehensive_report(30)
    """)
    
    print("\n🎯 DORA METRICS CAPABILITIES:")
    print("✅ Automated Deployment Tracking")
    print("✅ Real-time Metric Calculation")
    print("✅ Industry Benchmark Comparison")
    print("✅ Trend Analysis and Forecasting")
    print("✅ Strategic Recommendations")
    print("✅ Actionable Improvement Plans")

def run_dora_metrics_demo():
    """Run complete DORA metrics demonstration"""
    
    print("\n🧪 DORA METRICS DEMONSTRATION")
    print("=" * 45)
    
    # Initialize DORA metrics system
    config = DORAMetricsConfig()
    metrics_collector = DORAMetricsCollector(config)
    pipeline_integrator = DORACIPipelineIntegrator(metrics_collector)
    reporter = DORAMetricsReporter(metrics_collector)
    
    # Simulate deployment events
    print("\n🚀 Recording Deployment Events")
    
    sample_deployments = [
        DeploymentEvent(
            deployment_id=f"dep_{i}",
            service_name="user-service" if i % 2 == 0 else "content-service",
            version=f"v1.{i}.0",
            environment="production" if i % 3 != 0 else "staging",
            deployed_at=(datetime.now() - timedelta(days=i*2)).isoformat(),
            lead_time_seconds=3600 + (i * 1800),  # 1-4 hours
            deployment_duration_seconds=300 + (i * 60),  # 5-11 minutes
            success=i != 3 and i != 7  # Some failures for realism
        )
        for i in range(15)
    ]
    
    for deployment in sample_deployments:
        metrics_collector.record_deployment(deployment)
        
    # Simulate incident events
    print("\n⚠️  Recording Incident Events")
    
    sample_incidents = [
        IncidentEvent(
            incident_id=f"inc_{i}",
            service_name="user-service" if i % 2 == 0 else "content-service",
            environment="production",
            detected_at=(datetime.now() - timedelta(days=i*3, hours=2)).isoformat(),
            resolved_at=(datetime.now() - timedelta(days=i*3)).isoformat(),
            severity="high" if i % 3 == 0 else "medium",
            root_cause="database_connection" if i % 2 == 0 else "memory_leak",
            mttr_seconds=7200 + (i * 3600)  # 2-8 hours
        )
        for i in range(8)
    ]
    
    for incident in sample_incidents:
        metrics_collector.record_incident(incident)
        
    # Integrate with CI/CD pipeline
    print("\n🔄 CI/CD Pipeline Integration")
    
    pipeline_config = {
        'name': 'secure-ai-studio-pipeline',
        'environments': ['development', 'staging', 'production'],
        'reporting_schedule': 'weekly',
        'report_recipients': ['engineering-team', 'product-management']
    }
    
    integration = pipeline_integrator.integrate_with_deployment_pipeline(pipeline_config)
    
    # Generate comprehensive report
    print("\n📊 Generating DORA Metrics Report")
    
    report = reporter.generate_comprehensive_report(30)
    current_metrics = report['current_metrics']
    
    print(f"\n📈 DORA METRICS RESULTS:")
    print(f"Performance Level: {current_metrics['performance_level']}")
    
    deployment_freq = current_metrics['deployment_frequency']
    print(f"Deployment Frequency: {deployment_freq['deployments_per_week']}/week ({deployment_freq['category']})")
    
    lead_time = current_metrics['lead_time']
    print(f"Lead Time: {lead_time['avg_lead_time_hours']} hours ({lead_time['category']})")
    
    failure_rate = current_metrics['change_failure_rate']
    print(f"Change Failure Rate: {failure_rate['failure_rate_percent']}% ({failure_rate['category']})")
    
    mttr = current_metrics['mttr']
    print(f"MTTR: {mttr['avg_mttr_hours']} hours ({mttr['category']})")
    
    print(f"\n📋 IMPROVEMENT OPPORTUNITIES:")
    for opportunity in current_metrics['improvement_opportunities'][:3]:
        print(f"  • {opportunity}")
        
    return {
        'metrics_collector': metrics_collector,
        'report': report,
        'integration': integration
    }

if __name__ == "__main__":
    demonstrate_dora_metrics_capabilities()
    print("\n" + "=" * 50)
    run_dora_metrics_demo()