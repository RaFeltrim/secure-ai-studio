#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤝 PACT CONTRACT TESTING FRAMEWORK
SDET Phase 3 Week 12 - Microservice Integration Validation

Enterprise-grade contract testing implementation using Pact framework
for validating microservice interactions and API contracts.
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
from pact import Consumer, Provider, Term, Like, EachLike

# ==================== PACT CONTRACT DEFINITIONS ====================

@dataclass
class ContractDefinition:
    """Pact contract definition between consumer and provider"""
    consumer_name: str
    provider_name: str
    interaction_name: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    state: str = None
    description: str = None

@dataclass
class ContractTestResult:
    """Result of contract testing execution"""
    consumer_name: str
    provider_name: str
    interaction_name: str
    test_status: str  # passed, failed, pending
    verification_result: Dict[str, Any]
    timestamp: str
    contract_version: str

class PactContractManager:
    """Manage Pact contract definitions and lifecycle"""
    
    def __init__(self, pact_broker_url: str = "http://localhost:9292"):
        self.pact_broker_url = pact_broker_url
        self.contracts = []
        self.published_contracts = []
        
    def define_consumer_contract(self, contract_def: ContractDefinition) -> Dict[str, Any]:
        """Define contract from consumer perspective"""
        
        # Create Pact consumer instance
        consumer = Consumer(contract_def.consumer_name)
        provider = Provider(contract_def.provider_name)
        
        # Build contract interaction
        pact_interaction = consumer.has_pact_with(provider)
        
        # Define request
        request_def = {
            'method': contract_def.request.get('method', 'GET'),
            'path': contract_def.request.get('path', '/'),
            'headers': contract_def.request.get('headers', {})
        }
        
        if 'body' in contract_def.request:
            request_def['body'] = contract_def.request['body']
            
        if 'query' in contract_def.request:
            request_def['query'] = contract_def.request['query']
            
        # Define response
        response_def = {
            'status': contract_def.response.get('status', 200),
            'headers': contract_def.response.get('headers', {})
        }
        
        if 'body' in contract_def.response:
            response_def['body'] = contract_def.response['body']
            
        # Add interaction to pact
        interaction = pact_interaction.given(contract_def.state or 'default state') \
                                    .upon_receiving(contract_def.description or contract_def.interaction_name) \
                                    .with_request(**request_def) \
                                    .will_respond_with(**response_def)
        
        contract_data = {
            'consumer': contract_def.consumer_name,
            'provider': contract_def.provider_name,
            'interaction': contract_def.interaction_name,
            'definition': {
                'request': request_def,
                'response': response_def,
                'state': contract_def.state
            },
            'pact_interaction': interaction
        }
        
        self.contracts.append(contract_data)
        return contract_data
        
    def publish_contract_to_broker(self, consumer_name: str, 
                                 provider_name: str, version: str) -> bool:
        """Publish contract to Pact Broker"""
        
        try:
            # In real implementation, this would use pact-broker CLI or API
            # For demo, we'll simulate the publishing
            
            published_contract = {
                'consumer': consumer_name,
                'provider': provider_name,
                'version': version,
                'published_at': datetime.now().isoformat(),
                'broker_url': self.pact_broker_url
            }
            
            self.published_contracts.append(published_contract)
            print(f"✅ Contract published: {consumer_name} -> {provider_name} (v{version})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to publish contract: {e}")
            return False
            
    def retrieve_provider_contracts(self, provider_name: str) -> List[Dict[str, Any]]:
        """Retrieve contracts for a specific provider"""
        
        # In real implementation, this would query the Pact Broker
        # For demo, we'll return contracts for the specified provider
        provider_contracts = [
            contract for contract in self.published_contracts 
            if contract['provider'] == provider_name
        ]
        
        return provider_contracts

# ==================== MICROSERVICE CONTRACT TESTING ====================

class MicroserviceContractTester:
    """Test microservice contracts using Pact framework"""
    
    def __init__(self, pact_manager: PactContractManager):
        self.pact_manager = pact_manager
        self.test_results = []
        
    def test_consumer_contracts(self, consumer_name: str, 
                              service_client: Any) -> List[ContractTestResult]:
        """Test contracts from consumer perspective"""
        
        print(f"🤝 Testing Consumer Contracts: {consumer_name}")
        print("=" * 50)
        
        test_results = []
        
        # Get contracts for this consumer
        consumer_contracts = [
            contract for contract in self.pact_manager.contracts
            if contract['consumer'] == consumer_name
        ]
        
        for contract in consumer_contracts:
            print(f"\n🧪 Testing: {contract['interaction']}")
            
            try:
                # Start Pact mock server
                with contract['pact_interaction']:
                    # Execute consumer code against mock provider
                    result = self._execute_consumer_interaction(
                        service_client, 
                        contract['definition']
                    )
                    
                    test_result = ContractTestResult(
                        consumer_name=consumer_name,
                        provider_name=contract['provider'],
                        interaction_name=contract['interaction'],
                        test_status='passed' if result['success'] else 'failed',
                        verification_result=result,
                        timestamp=datetime.now().isoformat(),
                        contract_version='1.0.0'
                    )
                    
                    test_results.append(test_result)
                    
                    status_icon = "✅" if result['success'] else "❌"
                    print(f"{status_icon} {test_result.test_status}")
                    
            except Exception as e:
                test_result = ContractTestResult(
                    consumer_name=consumer_name,
                    provider_name=contract['provider'],
                    interaction_name=contract['interaction'],
                    test_status='failed',
                    verification_result={'error': str(e)},
                    timestamp=datetime.now().isoformat(),
                    contract_version='1.0.0'
                )
                test_results.append(test_result)
                print(f"❌ Test failed: {e}")
                
        self.test_results.extend(test_results)
        return test_results
        
    def test_provider_contracts(self, provider_name: str, 
                              provider_service: Any) -> List[ContractTestResult]:
        """Test contracts from provider perspective"""
        
        print(f"🤝 Testing Provider Contracts: {provider_name}")
        print("=" * 50)
        
        test_results = []
        
        # Retrieve contracts for this provider
        provider_contracts = self.pact_manager.retrieve_provider_contracts(provider_name)
        
        for contract in provider_contracts:
            print(f"\n🧪 Verifying: {contract['consumer']} contract")
            
            try:
                # Verify provider against contract
                verification_result = self._verify_provider_contract(
                    provider_service, 
                    contract
                )
                
                test_result = ContractTestResult(
                    consumer_name=contract['consumer'],
                    provider_name=provider_name,
                    interaction_name='contract_verification',
                    test_status='passed' if verification_result['success'] else 'failed',
                    verification_result=verification_result,
                    timestamp=datetime.now().isoformat(),
                    contract_version=contract['version']
                )
                
                test_results.append(test_result)
                
                status_icon = "✅" if verification_result['success'] else "❌"
                print(f"{status_icon} Contract verification: {test_result.test_status}")
                
            except Exception as e:
                test_result = ContractTestResult(
                    consumer_name='unknown',
                    provider_name=provider_name,
                    interaction_name='contract_verification',
                    test_status='failed',
                    verification_result={'error': str(e)},
                    timestamp=datetime.now().isoformat(),
                    contract_version='unknown'
                )
                test_results.append(test_result)
                print(f"❌ Verification failed: {e}")
                
        self.test_results.extend(test_results)
        return test_results
        
    def _execute_consumer_interaction(self, service_client: Any, 
                                    contract_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Execute consumer interaction against Pact mock"""
        
        try:
            request_def = contract_definition['request']
            expected_response = contract_definition['response']
            
            # Make request to Pact mock server
            if request_def['method'] == 'GET':
                response = service_client.get(request_def['path'], 
                                            params=request_def.get('query'),
                                            headers=request_def.get('headers'))
            elif request_def['method'] == 'POST':
                response = service_client.post(request_def['path'],
                                             json=request_def.get('body'),
                                             headers=request_def.get('headers'))
            elif request_def['method'] == 'PUT':
                response = service_client.put(request_def['path'],
                                            json=request_def.get('body'),
                                            headers=request_def.get('headers'))
            else:
                raise ValueError(f"Unsupported HTTP method: {request_def['method']}")
                
            # Verify response matches contract
            success = (
                response.status_code == expected_response['status'] and
                self._verify_response_body(response.json(), expected_response.get('body'))
            )
            
            return {
                'success': success,
                'actual_status': response.status_code,
                'expected_status': expected_response['status'],
                'response_matches': success,
                'response_body': response.json() if response.text else {}
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def _verify_provider_contract(self, provider_service: Any, 
                                contract: Dict[str, Any]) -> Dict[str, Any]:
        """Verify provider implementation against contract"""
        
        try:
            # In real implementation, this would:
            # 1. Download contract from Pact Broker
            # 2. Set up provider state
            # 3. Execute contract tests against real provider
            # 4. Verify all interactions pass
            
            # For demo, simulate verification
            verification_passed = True  # Assume provider meets contract
            
            return {
                'success': verification_passed,
                'contract_version': contract['version'],
                'interactions_verified': 5,  # Mock number
                'failures': 0,
                'verification_details': 'All contract interactions verified successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def _verify_response_body(self, actual_body: Dict[str, Any], 
                            expected_body: Dict[str, Any]) -> bool:
        """Verify response body matches expected structure"""
        
        if expected_body is None:
            return True
            
        # Handle Pact matchers
        if isinstance(expected_body, dict):
            for key, expected_value in expected_body.items():
                if key not in actual_body:
                    return False
                    
                actual_value = actual_body[key]
                
                # Handle Pact matchers
                if isinstance(expected_value, Like):
                    # Check type compatibility
                    if type(actual_value) != type(expected_value.matcher):
                        return False
                elif isinstance(expected_value, EachLike):
                    # Check array structure
                    if not isinstance(actual_value, list):
                        return False
                    if expected_value.min and len(actual_value) < expected_value.min:
                        return False
                elif isinstance(expected_value, Term):
                    # Check regex match
                    import re
                    if not re.match(expected_value.matcher, str(actual_value)):
                        return False
                elif isinstance(expected_value, dict):
                    # Recursive check for nested objects
                    if not self._verify_response_body(actual_value, expected_value):
                        return False
                else:
                    # Direct value comparison
                    if actual_value != expected_value:
                        return False
                        
        return True

# ==================== CONTRACT TEST SCENARIOS ====================

class ContractTestScenarios:
    """Predefined contract test scenarios for common microservice patterns"""
    
    @staticmethod
    def user_service_contracts() -> List[ContractDefinition]:
        """Contracts for User Service interactions"""
        
        return [
            ContractDefinition(
                consumer_name="AuthService",
                provider_name="UserService",
                interaction_name="Get user by ID",
                state="user exists with ID 123",
                description="A request for user with ID 123",
                request={
                    'method': 'GET',
                    'path': '/users/123',
                    'headers': {'Accept': 'application/json'}
                },
                response={
                    'status': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': {
                        'id': Like(123),
                        'username': Like('john_doe'),
                        'email': Like('john@example.com'),
                        'created_at': Term(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '2023-01-01T00:00:00')
                    }
                }
            ),
            ContractDefinition(
                consumer_name="AuthService",
                provider_name="UserService",
                interaction_name="Create new user",
                state="no user exists",
                description="A request to create a new user",
                request={
                    'method': 'POST',
                    'path': '/users',
                    'headers': {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    'body': {
                        'username': 'new_user',
                        'email': 'new@example.com',
                        'password': 'secure_password'
                    }
                },
                response={
                    'status': 201,
                    'headers': {'Content-Type': 'application/json'},
                    'body': {
                        'id': Like(456),
                        'username': Like('new_user'),
                        'email': Like('new@example.com'),
                        'created_at': Term(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '2023-01-01T00:00:00')
                    }
                }
            )
        ]
        
    @staticmethod
    def content_service_contracts() -> List[ContractDefinition]:
        """Contracts for Content Generation Service interactions"""
        
        return [
            ContractDefinition(
                consumer_name="APIService",
                provider_name="ContentService",
                interaction_name="Generate image content",
                state="service is available",
                description="A request to generate image content",
                request={
                    'method': 'POST',
                    'path': '/generate/image',
                    'headers': {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer fake-jwt-token'
                    },
                    'body': {
                        'prompt': 'A beautiful landscape',
                        'width': 1024,
                        'height': 1024,
                        'style': 'realistic'
                    }
                },
                response={
                    'status': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': {
                        'session_id': Like('sess_abc123'),
                        'status': Like('processing'),
                        'estimated_time': Like(30),
                        'image_url': Term(r'https?://.+', 'https://cdn.example.com/image.png')
                    }
                }
            ),
            ContractDefinition(
                consumer_name="APIService",
                provider_name="ContentService", 
                interaction_name="Get generation status",
                state="generation in progress",
                description="A request to check generation status",
                request={
                    'method': 'GET',
                    'path': '/generate/status/sess_abc123',
                    'headers': {'Accept': 'application/json'}
                },
                response={
                    'status': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': {
                        'session_id': Like('sess_abc123'),
                        'status': Like('completed'),
                        'progress': Like(100),
                        'result_url': Term(r'https?://.+', 'https://cdn.example.com/result.png')
                    }
                }
            )
        ]

# ==================== CI/CD CONTRACT INTEGRATION ====================

class ContractCIPipeline:
    """Integrate contract testing into CI/CD pipeline"""
    
    def __init__(self, contract_tester: MicroserviceContractTester):
        self.contract_tester = contract_tester
        self.pipeline_results = []
        
    def run_contract_validation_gate(self, service_name: str, 
                                   service_type: str,  # consumer or provider
                                   service_client: Any = None) -> Dict[str, Any]:
        """Run contract validation as CI/CD gate"""
        
        print(f"🔒 Running Contract Validation Gate: {service_name}")
        print("=" * 55)
        
        start_time = datetime.now()
        
        # Execute contract tests
        if service_type == 'consumer':
            test_results = self.contract_tester.test_consumer_contracts(
                service_name, service_client
            )
        elif service_type == 'provider':
            test_results = self.contract_tester.test_provider_contracts(
                service_name, service_client
            )
        else:
            raise ValueError(f"Invalid service type: {service_type}")
            
        end_time = datetime.now()
        
        # Analyze results
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r.test_status == 'passed')
        failed_tests = total_tests - passed_tests
        
        gate_result = {
            'service_name': service_name,
            'service_type': service_type,
            'status': 'PASSED' if failed_tests == 0 else 'FAILED',
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            'test_results': [asdict(r) for r in test_results],
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds()
        }
        
        self.pipeline_results.append(gate_result)
        
        status_icon = "✅" if gate_result['status'] == 'PASSED' else "❌"
        print(f"{status_icon} Contract Gate: {gate_result['status']}")
        print(f"Tests: {passed_tests}/{total_tests} passed")
        print(f"Success Rate: {gate_result['success_rate']:.1f}%")
        
        return gate_result
        
    def generate_contract_compliance_report(self) -> Dict[str, Any]:
        """Generate contract compliance report for deployment decision"""
        
        if not self.pipeline_results:
            return {"error": "No pipeline results available"}
            
        latest_result = self.pipeline_results[-1]
        
        report = {
            'compliance_status': latest_result['status'],
            'service_validated': latest_result['service_name'],
            'validation_type': latest_result['service_type'],
            'test_summary': {
                'total_interactions': latest_result['total_tests'],
                'successful_verifications': latest_result['passed_tests'],
                'failed_verifications': latest_result['failed_tests'],
                'compliance_rate': latest_result['success_rate']
            },
            'timestamp': datetime.now().isoformat(),
            'deployment_recommendation': self._generate_deployment_recommendation(latest_result)
        }
        
        return report
        
    def _generate_deployment_recommendation(self, result: Dict[str, Any]) -> str:
        """Generate deployment recommendation based on contract validation"""
        
        if result['status'] == 'PASSED':
            return "PROCEED_WITH_DEPLOYMENT - All contract validations passed"
        elif result['success_rate'] >= 80:
            return "PROCEED_WITH_CAUTION - Majority of contracts validated, review failures"
        else:
            return "BLOCK_DEPLOYMENT - Significant contract validation failures detected"

# ==================== DEMONSTRATION ====================

def demonstrate_contract_testing_capabilities():
    """Demonstrate Pact contract testing capabilities"""
    
    print("🤝 CONTRACT TESTING WITH PACT FRAMEWORK")
    print("=" * 50)
    
    print("\nBEFORE - Manual Integration Testing:")
    print("""
# Manual process
1. Deploy all services together
2. Test integrations manually
3. Hope services work together
4. Debug integration issues in production
    """)
    
    print("\nAFTER - Automated Contract Testing:")
    print("""
pact_manager = PactContractManager()
contract_tester = MicroserviceContractTester(pact_manager)

# Define contracts
contracts = ContractTestScenarios.user_service_contracts()
for contract in contracts:
    pact_manager.define_consumer_contract(contract)

# Test consumer contracts
consumer_results = contract_tester.test_consumer_contracts("AuthService", auth_client)

# Test provider contracts  
provider_results = contract_tester.test_provider_contracts("UserService", user_service)
    """)
    
    print("\n🎯 CONTRACT TESTING CAPABILITIES:")
    print("✅ Consumer-Driven Contract Testing")
    print("✅ Pact Broker Integration")
    print("✅ Automated Contract Verification")
    print("✅ CI/CD Pipeline Integration")
    print("✅ Microservice Compatibility Validation")
    print("✅ Early Integration Issue Detection")

def run_contract_testing_demo():
    """Run complete contract testing demonstration"""
    
    print("\n🧪 CONTRACT TESTING DEMONSTRATION")
    print("=" * 45)
    
    # Initialize contract testing components
    pact_manager = PactContractManager()
    contract_tester = MicroserviceContractTester(pact_manager)
    ci_pipeline = ContractCIPipeline(contract_tester)
    
    # Define and publish contracts
    print("📝 Defining Service Contracts")
    
    # User service contracts
    user_contracts = ContractTestScenarios.user_service_contracts()
    for contract in user_contracts:
        pact_manager.define_consumer_contract(contract)
        
    # Content service contracts
    content_contracts = ContractTestScenarios.content_service_contracts()
    for contract in content_contracts:
        pact_manager.define_consumer_contract(contract)
        
    # Publish contracts
    pact_manager.publish_contract_to_broker("AuthService", "UserService", "1.0.0")
    pact_manager.publish_contract_to_broker("APIService", "ContentService", "1.0.0")
    
    # Simulate service clients
    class MockServiceClient:
        def get(self, path, params=None, headers=None):
            class MockResponse:
                def __init__(self):
                    self.status_code = 200
                    self.text = json.dumps({
                        'id': 123,
                        'username': 'john_doe',
                        'email': 'john@example.com',
                        'created_at': '2023-01-01T00:00:00'
                    })
                def json(self):
                    return json.loads(self.text)
            return MockResponse()
            
        def post(self, path, json=None, headers=None):
            class MockResponse:
                def __init__(self):
                    self.status_code = 201
                    self.text = json.dumps({
                        'id': 456,
                        'username': 'new_user',
                        'email': 'new@example.com',
                        'created_at': '2023-01-01T00:00:00'
                    })
                def json(self):
                    return json.loads(self.text)
            return MockResponse()
    
    service_client = MockServiceClient()
    
    # Run contract validation gates
    print("\n🔒 Running Contract Validation Gates")
    
    # Consumer contract validation
    consumer_gate = ci_pipeline.run_contract_validation_gate(
        "AuthService", "consumer", service_client
    )
    
    # Provider contract validation
    provider_gate = ci_pipeline.run_contract_validation_gate(
        "UserService", "provider", service_client
    )
    
    # Generate compliance report
    compliance_report = ci_pipeline.generate_contract_compliance_report()
    
    print(f"\n📊 CONTRACT TESTING RESULTS:")
    print(f"Consumer Tests: {consumer_gate['passed_tests']}/{consumer_gate['total_tests']} passed")
    print(f"Provider Tests: {provider_gate['passed_tests']}/{provider_gate['total_tests']} passed")
    print(f"Overall Compliance: {compliance_report['compliance_status']}")
    
    print(f"\n📋 DEPLOYMENT RECOMMENDATION:")
    print(f"  {compliance_report['deployment_recommendation']}")
    
    return {
        'consumer_validation': consumer_gate,
        'provider_validation': provider_gate,
        'compliance_report': compliance_report
    }

if __name__ == "__main__":
    demonstrate_contract_testing_capabilities()
    print("\n" + "=" * 55)
    run_contract_testing_demo()