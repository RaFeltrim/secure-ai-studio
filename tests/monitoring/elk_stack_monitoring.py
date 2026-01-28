#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 ELK STACK MONITORING & OBSERVABILITY FRAMEWORK
SDET Phase 2 Week 7 - ELK Stack Implementation for Test Result Analysis

Enterprise-grade monitoring and observability solution using ELK stack
(Elasticsearch, Logstash, Kibana) with Grafana dashboards for comprehensive
test result analysis and system metrics visualization.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import json
import yaml
import subprocess
import time
import uuid
from elasticsearch import Elasticsearch
import requests

# ==================== ELK STACK COMPONENTS ====================

@dataclass
class ELKComponent:
    """ELK stack component configuration"""
    name: str
    type: str  # elasticsearch, logstash, kibana
    version: str
    port: int
    config: Dict[str, Any]

@dataclass
class LogPipeline:
    """Log processing pipeline configuration"""
    name: str
    input_plugin: str
    filter_plugins: List[str]
    output_plugin: str
    pattern: str

class ELKStackManager:
    """Manage ELK stack deployment and configuration"""
    
    def __init__(self):
        self.components = []
        self.pipelines = []
        self.es_client = None
        
    def configure_elasticsearch(self, config: Dict[str, Any] = None) -> ELKComponent:
        """Configure Elasticsearch component"""
        
        if config is None:
            config = {
                "cluster.name": "test-monitoring-cluster",
                "node.name": "test-node-1",
                "network.host": "0.0.0.0",
                "http.port": 9200,
                "discovery.type": "single-node",
                "xpack.security.enabled": False,
                "indices.query.bool.max_clause_count": 8192
            }
            
        es_component = ELKComponent(
            name="elasticsearch",
            type="elasticsearch",
            version="8.5.0",
            port=9200,
            config=config
        )
        
        self.components.append(es_component)
        return es_component
        
    def configure_logstash(self, pipelines: List[LogPipeline] = None) -> ELKComponent:
        """Configure Logstash component"""
        
        if pipelines is None:
            pipelines = [
                LogPipeline(
                    name="test-results-pipeline",
                    input_plugin="beats",
                    filter_plugins=["json", "mutate", "date"],
                    output_plugin="elasticsearch",
                    pattern="/test-results/*.log"
                ),
                LogPipeline(
                    name="application-logs-pipeline",
                    input_plugin="file",
                    filter_plugins=["grok", "mutate"],
                    output_plugin="elasticsearch",
                    pattern="/app/logs/*.log"
                )
            ]
            
        self.pipelines.extend(pipelines)
        
        logstash_config = {
            "pipelines": [asdict(pipe) for pipe in pipelines],
            "http.port": 9600,
            "http.host": "0.0.0.0"
        }
        
        logstash_component = ELKComponent(
            name="logstash",
            type="logstash",
            version="8.5.0",
            port=9600,
            config=logstash_config
        )
        
        self.components.append(logstash_component)
        return logstash_component
        
    def configure_kibana(self, config: Dict[str, Any] = None) -> ELKComponent:
        """Configure Kibana component"""
        
        if config is None:
            config = {
                "server.host": "0.0.0.0",
                "server.port": 5601,
                "elasticsearch.hosts": ["http://elasticsearch:9200"],
                "monitoring.ui.container.elasticsearch.enabled": True
            }
            
        kibana_component = ELKComponent(
            name="kibana",
            type="kibana",
            version="8.5.0",
            port=5601,
            config=config
        )
        
        self.components.append(kibana_component)
        return kibana_component
        
    def generate_docker_compose(self) -> Dict[str, Any]:
        """Generate Docker Compose configuration for ELK stack"""
        
        services = {}
        
        # Elasticsearch service
        services["elasticsearch"] = {
            "image": f"docker.elastic.co/elasticsearch/elasticsearch:{self.components[0].version}",
            "container_name": "elasticsearch",
            "environment": [
                f"{key}={value}" for key, value in self.components[0].config.items()
            ],
            "ports": [f"{self.components[0].port}:9200"],
            "volumes": [
                "esdata:/usr/share/elasticsearch/data"
            ],
            "ulimits": {
                "memlock": {
                    "soft": -1,
                    "hard": -1
                }
            }
        }
        
        # Logstash service
        services["logstash"] = {
            "image": f"docker.elastic.co/logstash/logstash:{self.components[1].version}",
            "container_name": "logstash",
            "environment": [
                f"{key}={value}" for key, value in self.components[1].config.items()
            ],
            "ports": [f"{self.components[1].port}:9600"],
            "volumes": [
                "./logstash/pipeline:/usr/share/logstash/pipeline",
                "./test-results:/test-results:ro",
                "./app/logs:/app/logs:ro"
            ],
            "depends_on": ["elasticsearch"]
        }
        
        # Kibana service
        services["kibana"] = {
            "image": f"docker.elastic.co/kibana/kibana:{self.components[2].version}",
            "container_name": "kibana",
            "environment": [
                f"{key}={value}" for key, value in self.components[2].config.items()
            ],
            "ports": [f"{self.components[2].port}:5601"],
            "depends_on": ["elasticsearch"]
        }
        
        compose_config = {
            "version": "3.8",
            "services": services,
            "volumes": {
                "esdata": None
            }
        }
        
        return compose_config

# ==================== LOG PROCESSING PIPELINES ====================

class LogPipelineProcessor:
    """Process and transform log data for ELK ingestion"""
    
    def __init__(self):
        self.processed_logs = []
        
    def process_test_results(self, test_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process test results for ELK indexing"""
        
        processed_results = []
        
        for result in test_results:
            # Enrich test result data
            enriched_result = {
                "@timestamp": datetime.now().isoformat(),
                "test_name": result.get("test_name", "unknown"),
                "status": result.get("status", "unknown"),
                "duration": result.get("duration", 0),
                "environment": result.get("environment", "test"),
                "suite": result.get("suite", "default"),
                "metadata": result.get("metadata", {}),
                "log_level": self._determine_log_level(result.get("status")),
                "tags": ["test-result", result.get("suite", "default")]
            }
            
            # Add performance metrics
            if "performance" in result:
                enriched_result["performance"] = result["performance"]
                
            # Add error details if failed
            if result.get("status") == "failed" and "error" in result:
                enriched_result["error_details"] = {
                    "message": result["error"],
                    "stack_trace": result.get("stack_trace", ""),
                    "failure_type": self._classify_failure(result["error"])
                }
                enriched_result["tags"].append("failure")
                
            processed_results.append(enriched_result)
            self.processed_logs.append(enriched_result)
            
        return processed_results
        
    def process_application_logs(self, app_logs: List[str]) -> List[Dict[str, Any]]:
        """Process application logs for structured format"""
        
        processed_logs = []
        
        for log_entry in app_logs:
            try:
                # Parse log entry (assuming structured logging)
                if log_entry.startswith("{"):
                    log_data = json.loads(log_entry)
                else:
                    # Parse unstructured logs
                    log_data = self._parse_unstructured_log(log_entry)
                    
                # Enrich with metadata
                enriched_log = {
                    "@timestamp": log_data.get("timestamp", datetime.now().isoformat()),
                    "log_level": log_data.get("level", "INFO"),
                    "message": log_data.get("message", log_entry),
                    "component": log_data.get("component", "unknown"),
                    "thread": log_data.get("thread", "main"),
                    "tags": ["application-log"]
                }
                
                # Add structured fields if present
                if "fields" in log_data:
                    enriched_log.update(log_data["fields"])
                    
                processed_logs.append(enriched_log)
                self.processed_logs.append(enriched_log)
                
            except Exception as e:
                # Handle parsing errors
                error_log = {
                    "@timestamp": datetime.now().isoformat(),
                    "log_level": "ERROR",
                    "message": f"Log parsing failed: {e}",
                    "original_log": log_entry[:200],  # First 200 chars
                    "tags": ["parsing-error"]
                }
                processed_logs.append(error_log)
                
        return processed_logs
        
    def _determine_log_level(self, status: str) -> str:
        """Determine appropriate log level based on test status"""
        level_mapping = {
            "passed": "INFO",
            "failed": "ERROR",
            "skipped": "WARN",
            "pending": "DEBUG"
        }
        return level_mapping.get(status.lower(), "INFO")
        
    def _classify_failure(self, error_message: str) -> str:
        """Classify failure type based on error message"""
        error_lower = error_message.lower()
        
        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        elif "connection" in error_lower or "network" in error_lower:
            return "connectivity"
        elif "assertion" in error_lower or "expected" in error_lower:
            return "assertion"
        elif "memory" in error_lower or "oom" in error_lower:
            return "memory"
        else:
            return "other"
            
    def _parse_unstructured_log(self, log_entry: str) -> Dict[str, Any]:
        """Parse unstructured log entry into structured format"""
        # Simple regex-based parsing (would be enhanced with proper log parsing library)
        import re
        
        # Extract timestamp (ISO format)
        timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', log_entry)
        timestamp = timestamp_match.group() if timestamp_match else datetime.now().isoformat()
        
        # Extract log level
        level_match = re.search(r'(INFO|ERROR|WARN|DEBUG)', log_entry)
        level = level_match.group() if level_match else "INFO"
        
        return {
            "timestamp": timestamp,
            "level": level,
            "message": log_entry
        }

# ==================== GRAFANA DASHBOARD CREATION ====================

class GrafanaDashboardManager:
    """Manage Grafana dashboard creation and configuration"""
    
    def __init__(self, grafana_url: str = "http://localhost:3000"):
        self.grafana_url = grafana_url
        self.dashboards = []
        
    def create_test_metrics_dashboard(self) -> Dict[str, Any]:
        """Create comprehensive test metrics dashboard"""
        
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "Test Results & Performance Dashboard",
                "timezone": "browser",
                "panels": [
                    self._create_summary_panel(),
                    self._create_trend_panel(),
                    self._create_failure_analysis_panel(),
                    self._create_performance_panel(),
                    self._create_environment_panel()
                ],
                "templating": {
                    "list": [
                        {
                            "name": "Environment",
                            "type": "query",
                            "datasource": "Elasticsearch",
                            "refresh": 1,
                            "query": "{\"find\": \"terms\", \"field\": \"environment.keyword\"}"
                        }
                    ]
                }
            },
            "overwrite": True
        }
        
        self.dashboards.append(dashboard)
        return dashboard
        
    def create_system_metrics_dashboard(self) -> Dict[str, Any]:
        """Create system metrics monitoring dashboard"""
        
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "System Metrics & Resource Usage",
                "timezone": "browser",
                "panels": [
                    self._create_cpu_panel(),
                    self._create_memory_panel(),
                    self._create_disk_panel(),
                    self._create_network_panel()
                ]
            },
            "overwrite": True
        }
        
        self.dashboards.append(dashboard)
        return dashboard
        
    def _create_summary_panel(self) -> Dict[str, Any]:
        """Create test summary panel"""
        return {
            "type": "stat",
            "title": "Test Summary",
            "gridPos": {"x": 0, "y": 0, "w": 12, "h": 6},
            "targets": [
                {
                    "refId": "A",
                    "query": "SELECT count(*) FROM test-results WHERE status = 'passed'",
                    "alias": "Passed Tests"
                },
                {
                    "refId": "B", 
                    "query": "SELECT count(*) FROM test-results WHERE status = 'failed'",
                    "alias": "Failed Tests"
                }
            ],
            "options": {
                "orientation": "auto",
                "textMode": "value_and_name",
                "colorMode": "background"
            }
        }
        
    def _create_trend_panel(self) -> Dict[str, Any]:
        """Create test trend visualization panel"""
        return {
            "type": "timeseries",
            "title": "Test Execution Trends",
            "gridPos": {"x": 0, "y": 6, "w": 24, "h": 8},
            "targets": [
                {
                    "refId": "A",
                    "query": "SELECT count(*) FROM test-results GROUP BY date_histogram(@timestamp, '1d')",
                    "alias": "Daily Test Count"
                }
            ]
        }
        
    def _create_failure_analysis_panel(self) -> Dict[str, Any]:
        """Create failure analysis panel"""
        return {
            "type": "piechart",
            "title": "Failure Types Distribution",
            "gridPos": {"x": 12, "y": 0, "w": 12, "h": 6},
            "targets": [
                {
                    "refId": "A",
                    "query": "SELECT failure_type, count(*) FROM test-results WHERE status = 'failed' GROUP BY failure_type",
                    "alias": "$tag_failure_type"
                }
            ]
        }
        
    def _create_performance_panel(self) -> Dict[str, Any]:
        """Create performance metrics panel"""
        return {
            "type": "gauge",
            "title": "Average Test Duration",
            "gridPos": {"x": 0, "y": 14, "w": 8, "h": 6},
            "targets": [
                {
                    "refId": "A",
                    "query": "SELECT avg(duration) FROM test-results",
                    "alias": "Avg Duration (ms)"
                }
            ]
        }
        
    def _create_environment_panel(self) -> Dict[str, Any]:
        """Create environment comparison panel"""
        return {
            "type": "barchart",
            "title": "Test Results by Environment",
            "gridPos": {"x": 8, "y": 14, "w": 16, "h": 6},
            "targets": [
                {
                    "refId": "A",
                    "query": "SELECT environment, count(*) FROM test-results GROUP BY environment",
                    "alias": "$tag_environment"
                }
            ]
        }
        
    def _create_cpu_panel(self) -> Dict[str, Any]:
        """Create CPU usage panel"""
        return {
            "type": "timeseries",
            "title": "CPU Usage %",
            "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
            "targets": [
                {
                    "refId": "A",
                    "query": "SELECT avg(cpu_usage) FROM system-metrics GROUP BY date_histogram(@timestamp, '1m')",
                    "alias": "CPU Usage"
                }
            ]
        }
        
    def _create_memory_panel(self) -> Dict[str, Any]:
        """Create memory usage panel"""
        return {
            "type": "timeseries", 
            "title": "Memory Usage MB",
            "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
            "targets": [
                {
                    "refId": "A",
                    "query": "SELECT avg(memory_used) FROM system-metrics GROUP BY date_histogram(@timestamp, '1m')",
                    "alias": "Memory Used"
                }
            ]
        }

# ==================== DATA INDEXING & QUERYING ====================

class ELKDataIndexer:
    """Index data into Elasticsearch and perform queries"""
    
    def __init__(self, es_host: str = "localhost", es_port: int = 9200):
        self.es_client = Elasticsearch([f"http://{es_host}:{es_port}"])
        self.indices = {
            "test-results": "test_results_index",
            "application-logs": "app_logs_index",
            "system-metrics": "system_metrics_index"
        }
        
    def index_test_results(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index test results into Elasticsearch"""
        
        indexed_count = 0
        errors = []
        
        for result in test_results:
            try:
                # Index document
                response = self.es_client.index(
                    index=self.indices["test-results"],
                    document=result
                )
                
                if response.get("result") == "created":
                    indexed_count += 1
                    
            except Exception as e:
                errors.append(f"Failed to index result {result.get('test_name')}: {e}")
                
        return {
            "indexed_count": indexed_count,
            "total_count": len(test_results),
            "errors": errors,
            "success_rate": (indexed_count / len(test_results)) * 100 if test_results else 0
        }
        
    def index_application_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Index application logs into Elasticsearch"""
        
        indexed_count = 0
        errors = []
        
        for log in logs:
            try:
                response = self.es_client.index(
                    index=self.indices["application-logs"],
                    document=log
                )
                
                if response.get("result") == "created":
                    indexed_count += 1
                    
            except Exception as e:
                errors.append(f"Failed to index log: {e}")
                
        return {
            "indexed_count": indexed_count,
            "total_count": len(logs),
            "errors": errors,
            "success_rate": (indexed_count / len(logs)) * 100 if logs else 0
        }
        
    def query_test_metrics(self, timeframe: str = "24h") -> Dict[str, Any]:
        """Query test metrics from Elasticsearch"""
        
        try:
            # Query for test summary
            test_summary_query = {
                "size": 0,
                "aggs": {
                    "total_tests": {"value_count": {"field": "test_name.keyword"}},
                    "passed_tests": {"filter": {"term": {"status": "passed"}}},
                    "failed_tests": {"filter": {"term": {"status": "failed"}}},
                    "avg_duration": {"avg": {"field": "duration"}}
                }
            }
            
            response = self.es_client.search(
                index=self.indices["test-results"],
                body=test_summary_query
            )
            
            aggregations = response.get("aggregations", {})
            
            return {
                "total_tests": aggregations.get("total_tests", {}).get("value", 0),
                "passed_tests": aggregations.get("passed_tests", {}).get("doc_count", 0),
                "failed_tests": aggregations.get("failed_tests", {}).get("doc_count", 0),
                "avg_duration": aggregations.get("avg_duration", {}).get("value", 0),
                "success_rate": 0 if aggregations.get("total_tests", {}).get("value", 0) == 0 else
                              (aggregations.get("passed_tests", {}).get("doc_count", 0) / 
                               aggregations.get("total_tests", {}).get("value", 1)) * 100
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    def query_failure_patterns(self) -> Dict[str, Any]:
        """Query common failure patterns"""
        
        try:
            failure_query = {
                "size": 0,
                "query": {"term": {"status": "failed"}},
                "aggs": {
                    "by_failure_type": {
                        "terms": {"field": "error_details.failure_type.keyword"}
                    },
                    "recent_failures": {
                        "top_hits": {
                            "size": 10,
                            "_source": ["test_name", "error_details.message", "@timestamp"]
                        }
                    }
                }
            }
            
            response = self.es_client.search(
                index=self.indices["test-results"],
                body=failure_query
            )
            
            return {
                "failure_types": response.get("aggregations", {}).get("by_failure_type", {}).get("buckets", []),
                "recent_failures": response.get("aggregations", {}).get("recent_failures", {}).get("hits", {}).get("hits", [])
            }
            
        except Exception as e:
            return {"error": str(e)}

# ==================== MONITORING ORCHESTRATOR ====================

class MonitoringOrchestrator:
    """Orchestrate complete monitoring and observability solution"""
    
    def __init__(self):
        self.elk_manager = ELKStackManager()
        self.pipeline_processor = LogPipelineProcessor()
        self.dashboard_manager = GrafanaDashboardManager()
        self.data_indexer = ELKDataIndexer()
        self.monitoring_results = []
        
    def setup_complete_monitoring_stack(self) -> Dict[str, Any]:
        """Setup complete ELK + Grafana monitoring stack"""
        
        print("📊 Setting up Complete Monitoring Stack")
        print("=" * 45)
        
        setup_start = datetime.now()
        
        # Configure ELK components
        self.elk_manager.configure_elasticsearch()
        self.elk_manager.configure_logstash()
        self.elk_manager.configure_kibana()
        
        # Generate Docker Compose
        docker_compose = self.elk_manager.generate_docker_compose()
        
        # Create Grafana dashboards
        test_dashboard = self.dashboard_manager.create_test_metrics_dashboard()
        system_dashboard = self.dashboard_manager.create_system_metrics_dashboard()
        
        setup_end = datetime.now()
        
        result = {
            "components_configured": len(self.elk_manager.components),
            "pipelines_created": len(self.elk_manager.pipelines),
            "dashboards_created": len(self.dashboard_manager.dashboards),
            "docker_compose_generated": True,
            "setup_start": setup_start.isoformat(),
            "setup_end": setup_end.isoformat(),
            "setup_duration": (setup_end - setup_start).total_seconds()
        }
        
        self.monitoring_results.append(result)
        
        print(f"✅ Monitoring stack setup completed")
        print(f"   Components: {result['components_configured']}")
        print(f"   Dashboards: {result['dashboards_created']}")
        print(f"   Setup Time: {result['setup_duration']:.2f}s")
        
        return result
        
    def process_and_index_test_data(self, test_results: List[Dict[str, Any]], 
                                  app_logs: List[str] = None) -> Dict[str, Any]:
        """Process test data and index into monitoring system"""
        
        print("🔄 Processing and Indexing Test Data")
        print("=" * 40)
        
        processing_start = datetime.now()
        
        # Process test results
        processed_results = self.pipeline_processor.process_test_results(test_results)
        indexing_result = self.data_indexer.index_test_results(processed_results)
        
        # Process application logs if provided
        log_indexing_result = None
        if app_logs:
            processed_logs = self.pipeline_processor.process_application_logs(app_logs)
            log_indexing_result = self.data_indexer.index_application_logs(processed_logs)
            
        # Query metrics
        test_metrics = self.data_indexer.query_test_metrics()
        failure_patterns = self.data_indexer.query_failure_patterns()
        
        processing_end = datetime.now()
        
        result = {
            "processed_test_results": len(processed_results),
            "test_indexing_result": indexing_result,
            "log_processing_result": log_indexing_result,
            "test_metrics": test_metrics,
            "failure_patterns": failure_patterns,
            "processing_start": processing_start.isoformat(),
            "processing_end": processing_end.isoformat(),
            "processing_duration": (processing_end - processing_start).total_seconds()
        }
        
        self.monitoring_results.append(result)
        
        print(f"✅ Data processing completed")
        print(f"   Test Results Processed: {len(processed_results)}")
        print(f"   Indexing Success Rate: {indexing_result['success_rate']:.1f}%")
        print(f"   Processing Time: {result['processing_duration']:.2f}s")
        
        return result

# ==================== DEMONSTRATION ====================

def demonstrate_monitoring_capabilities():
    """Demonstrate monitoring and observability capabilities"""
    
    print("📊 MONITORING & OBSERVABILITY FRAMEWORK")
    print("=" * 45)
    
    print("\nBEFORE - Manual Log Analysis:")
    print("""
# Manual process
1. SSH to servers
2. Tail log files manually
3. Count test results by hand
4. Create charts in spreadsheets
5. Share reports via email
    """)
    
    print("\nAFTER - Automated Monitoring Stack:")
    print("""
orchestrator = MonitoringOrchestrator()
stack = orchestrator.setup_complete_monitoring_stack()
data_result = orchestrator.process_and_index_test_data(test_results)

# Real-time dashboards
# Automated alerting
# Trend analysis
# Failure pattern detection
    """)
    
    print("\n🎯 MONITORING CAPABILITIES:")
    print("✅ ELK Stack Deployment")
    print("✅ Log Processing Pipelines")
    print("✅ Grafana Dashboard Creation")
    print("✅ Real-time Metrics Visualization")
    print("✅ Failure Pattern Analysis")
    print("✅ Performance Trend Monitoring")

def run_monitoring_demo():
    """Run complete monitoring demonstration"""
    
    print("\n🧪 MONITORING FRAMEWORK DEMONSTRATION")
    print("=" * 45)
    
    # Initialize orchestrator
    orchestrator = MonitoringOrchestrator()
    
    # Setup monitoring stack
    stack_result = orchestrator.setup_complete_monitoring_stack()
    
    # Sample test results
    sample_test_results = [
        {
            "test_name": "test_user_authentication",
            "status": "passed",
            "duration": 125,
            "environment": "staging",
            "suite": "auth-tests"
        },
        {
            "test_name": "test_content_generation",
            "status": "failed",
            "duration": 2500,
            "environment": "staging", 
            "suite": "generation-tests",
            "error": "Timeout occurred while generating content"
        },
        {
            "test_name": "test_api_endpoints",
            "status": "passed",
            "duration": 89,
            "environment": "production",
            "suite": "api-tests"
        }
    ]
    
    # Sample application logs
    sample_logs = [
        '{"timestamp": "2023-01-15T10:30:00", "level": "INFO", "message": "User login successful", "component": "auth-service"}',
        '{"timestamp": "2023-01-15T10:31:00", "level": "ERROR", "message": "Database connection failed", "component": "db-service"}',
        '{"timestamp": "2023-01-15T10:32:00", "level": "WARN", "message": "High memory usage detected", "component": "memory-manager"}'
    ]
    
    # Process and index data
    data_result = orchestrator.process_and_index_test_data(sample_test_results, sample_logs)
    
    print(f"\n📊 MONITORING IMPLEMENTATION RESULTS:")
    print(f"Stack Components: {stack_result['components_configured']}")
    print(f"Dashboards Created: {stack_result['dashboards_created']}")
    print(f"Test Results Processed: {data_result['processed_test_results']}")
    print(f"Data Indexing Success: {data_result['test_indexing_result']['success_rate']:.1f}%")
    
    # Display sample metrics
    metrics = data_result['test_metrics']
    if 'error' not in metrics:
        print(f"\n📈 SAMPLE METRICS:")
        print(f"Total Tests: {metrics['total_tests']}")
        print(f"Pass Rate: {metrics['success_rate']:.1f}%")
        print(f"Avg Duration: {metrics['avg_duration']:.1f}ms")
        
    return {
        "stack_setup": stack_result,
        "data_processing": data_result
    }

if __name__ == "__main__":
    demonstrate_monitoring_capabilities()
    print("\n" + "=" * 50)
    run_monitoring_demo()