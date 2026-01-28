#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ OWASP ZAP SECURITY TESTING AUTOMATION
SDET Phase 3 Week 10 - AppSec Integration with Active/Passive Scanning

Enterprise-grade security testing automation integrating OWASP ZAP for 
comprehensive application security assessment of Secure AI Studio.
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
import xml.etree.ElementTree as ET
from zapv2 import ZAPv2

# ==================== SECURITY TESTING FRAMEWORK ====================

@dataclass
class SecurityScanConfig:
    """Security scan configuration"""
    target_url: str
    scan_type: str  # 'active', 'passive', 'both'
    authentication: Dict[str, Any]
    scan_policy: str = "Default Policy"
    context_name: str = "SecureAIStudio"
    spider_max_depth: int = 5
    ajax_spider: bool = True

@dataclass
class VulnerabilityFinding:
    """Security vulnerability finding"""
    id: str
    name: str
    risk: str  # HIGH, MEDIUM, LOW, INFO
    confidence: str  # HIGH, MEDIUM, LOW, FALSE_POSITIVE
    url: str
    description: str
    solution: str
    reference: List[str]
    cwe_id: Optional[str]
    wasc_id: Optional[str]
    timestamp: str

@dataclass
class SecurityScanResult:
    """Complete security scan result"""
    scan_id: str
    target_url: str
    start_time: str
    end_time: str
    duration_seconds: float
    total_findings: int
    findings_by_risk: Dict[str, int]
    findings_by_type: Dict[str, int]
    vulnerabilities: List[VulnerabilityFinding]
    scan_summary: Dict[str, Any]

class OWASPZAPIntegration:
    """Integrate with OWASP ZAP for automated security testing"""
    
    def __init__(self, zap_api_key: str = None, zap_proxy: str = "http://localhost:8080"):
        self.zap_proxy = zap_proxy
        self.zap = ZAPv2(proxies={'http': zap_proxy, 'https': zap_proxy}, apikey=zap_api_key)
        self.scan_results = []
        
    def start_zap_daemon(self, headless: bool = True) -> bool:
        """Start ZAP daemon process"""
        
        print("🛡️ Starting OWASP ZAP Daemon")
        
        try:
            zap_cmd = [
                "zap.sh" if not headless else "zap-x.sh",
                "-daemon",
                "-host", "localhost",
                "-port", "8080",
                "-config", "api.addrs.addr.name=.*",
                "-config", "api.addrs.addr.regex=true"
            ]
            
            if headless:
                zap_cmd.extend(["-silent"])
                
            # Start ZAP process
            process = subprocess.Popen(zap_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for ZAP to be ready
            max_wait = 120  # 2 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                try:
                    self.zap.core.version()
                    print("✅ ZAP daemon started successfully")
                    return True
                except:
                    time.sleep(2)
                    wait_time += 2
                    
            print("❌ ZAP daemon failed to start within timeout")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start ZAP daemon: {e}")
            return False
            
    def configure_authentication(self, auth_config: Dict[str, Any]) -> bool:
        """Configure authentication for security scanning"""
        
        try:
            # Create context for the application
            context_id = self.zap.context.new_context("SecureAIStudio")
            
            # Include application URLs in context
            self.zap.context.include_in_context("SecureAIStudio", auth_config["target_urls"])
            
            # Configure authentication method
            if auth_config["type"] == "form":
                self.zap.authentication.set_authentication_method(
                    context_id,
                    "formBasedAuthentication",
                    f"loginUrl={auth_config['login_url']}&loginRequestData={auth_config['request_data']}"
                )
                
                # Set logged-in indicator
                self.zap.authentication.set_logged_in_indicator(context_id, auth_config["logged_in_indicator"])
                
            elif auth_config["type"] == "http":
                self.zap.authentication.set_authentication_method(
                    context_id,
                    "httpAuthentication",
                    f"hostname={auth_config['hostname']}&realm={auth_config['realm']}&port={auth_config['port']}"
                )
                
            elif auth_config["type"] == "script":
                self.zap.authentication.set_authentication_method(
                    context_id,
                    "scriptBasedAuthentication",
                    f"scriptName={auth_config['script_name']}"
                )
                
            # Create user if needed
            if "username" in auth_config:
                user_id = self.zap.users.new_user(context_id, auth_config["username"])
                self.zap.users.set_authentication_credentials(
                    context_id,
                    user_id,
                    auth_config["credentials"]
                )
                self.zap.users.set_user_enabled(context_id, user_id, True)
                
            return True
            
        except Exception as e:
            print(f"❌ Authentication configuration failed: {e}")
            return False
            
    def perform_active_scan(self, target_url: str, 
                          scan_policy: str = "Default Policy") -> str:
        """Perform active security scan"""
        
        print(f"⚔️ Starting Active Scan: {target_url}")
        
        try:
            # Access the target URL first
            self.zap.urlopen(target_url)
            time.sleep(2)
            
            # Start active scan
            scan_id = self.zap.ascan.scan(
                url=target_url,
                recurse=True,
                inscopeonly=True,
                scanpolicyname=scan_policy,
                method="GET"
            )
            
            # Wait for scan to complete
            while int(self.zap.ascan.status(scan_id)) < 100:
                print(f"Active scan progress: {self.zap.ascan.status(scan_id)}%")
                time.sleep(10)
                
            print("✅ Active scan completed")
            return scan_id
            
        except Exception as e:
            print(f"❌ Active scan failed: {e}")
            return None
            
    def perform_passive_scan(self, target_url: str) -> str:
        """Perform passive security scan"""
        
        print(f"🕵️ Starting Passive Scan: {target_url}")
        
        try:
            # Spider the application to discover URLs
            print("🕷️ Starting spider...")
            spider_scan_id = self.zap.spider.scan(target_url, maxchildren=10, recurse=True)
            
            # Wait for spider to complete
            while int(self.zap.spider.status(spider_scan_id)) < 100:
                print(f"Spider progress: {self.zap.spider.status(spider_scan_id)}%")
                time.sleep(5)
                
            print("✅ Spider completed")
            
            # AJAX spider for JavaScript-heavy applications
            print("🕷️ Starting AJAX spider...")
            ajax_scan_id = self.zap.ajaxSpider.scan(target_url)
            
            # Wait for AJAX spider to complete
            while self.zap.ajaxSpider.status == 'running':
                print("AJAX spider running...")
                time.sleep(5)
                
            print("✅ AJAX spider completed")
            
            # Wait for passive scanning to process all requests
            time.sleep(30)
            
            print("✅ Passive scan completed")
            return "passive_scan_complete"
            
        except Exception as e:
            print(f"❌ Passive scan failed: {e}")
            return None
            
    def get_scan_results(self) -> List[VulnerabilityFinding]:
        """Retrieve and parse security scan results"""
        
        try:
            alerts = self.zap.core.alerts()
            findings = []
            
            for alert in alerts:
                finding = VulnerabilityFinding(
                    id=alert.get('id', str(uuid.uuid4())),
                    name=alert.get('name', 'Unknown Vulnerability'),
                    risk=alert.get('risk', 'LOW'),
                    confidence=alert.get('confidence', 'LOW'),
                    url=alert.get('url', ''),
                    description=alert.get('description', ''),
                    solution=alert.get('solution', ''),
                    reference=alert.get('reference', '').split(',') if alert.get('reference') else [],
                    cwe_id=alert.get('cweid'),
                    wasc_id=alert.get('wascid'),
                    timestamp=datetime.now().isoformat()
                )
                findings.append(finding)
                
            return findings
            
        except Exception as e:
            print(f"❌ Failed to retrieve scan results: {e}")
            return []

# ==================== AUTOMATED SECURITY TESTING ====================

class AutomatedSecurityTester:
    """Automate comprehensive security testing workflows"""
    
    def __init__(self, zap_integration: OWASPZAPIntegration):
        self.zap = zap_integration
        self.test_results = []
        
    def run_comprehensive_security_assessment(self, 
                                            config: SecurityScanConfig) -> SecurityScanResult:
        """Run complete security assessment with active and passive scanning"""
        
        print("🛡️ COMPREHENSIVE SECURITY ASSESSMENT")
        print("=" * 50)
        
        start_time = datetime.now()
        
        # Configure authentication if provided
        if config.authentication:
            auth_success = self.zap.configure_authentication(config.authentication)
            if not auth_success:
                print("❌ Authentication configuration failed")
                return None
                
        # Perform passive scanning
        passive_result = None
        if config.scan_type in ['passive', 'both']:
            passive_result = self.zap.perform_passive_scan(config.target_url)
            
        # Perform active scanning
        active_scan_id = None
        if config.scan_type in ['active', 'both']:
            active_scan_id = self.zap.perform_active_scan(
                config.target_url,
                config.scan_policy
            )
            
        end_time = datetime.now()
        
        # Retrieve results
        vulnerabilities = self.zap.get_scan_results()
        
        # Generate summary statistics
        findings_by_risk = {}
        findings_by_type = {}
        
        for vuln in vulnerabilities:
            # Count by risk level
            risk = vuln.risk
            findings_by_risk[risk] = findings_by_risk.get(risk, 0) + 1
            
            # Count by vulnerability type
            vuln_type = vuln.name
            findings_by_type[vuln_type] = findings_by_type.get(vuln_type, 0) + 1
            
        # Create scan result
        scan_result = SecurityScanResult(
            scan_id=str(uuid.uuid4()),
            target_url=config.target_url,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=(end_time - start_time).total_seconds(),
            total_findings=len(vulnerabilities),
            findings_by_risk=findings_by_risk,
            findings_by_type=findings_by_type,
            vulnerabilities=vulnerabilities,
            scan_summary={
                "passive_scan_performed": config.scan_type in ['passive', 'both'],
                "active_scan_performed": config.scan_type in ['active', 'both'],
                "active_scan_id": active_scan_id,
                "authentication_configured": bool(config.authentication),
                "scan_policy_used": config.scan_policy
            }
        )
        
        self.test_results.append(scan_result)
        
        print(f"✅ Security assessment completed")
        print(f"Total Findings: {scan_result.total_findings}")
        print(f"High Risk: {findings_by_risk.get('HIGH', 0)}")
        print(f"Medium Risk: {findings_by_risk.get('MEDIUM', 0)}")
        print(f"Low Risk: {findings_by_risk.get('LOW', 0)}")
        
        return scan_result
        
    def generate_security_report(self, scan_result: SecurityScanResult) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        
        report = {
            "report_title": "Secure AI Studio Security Assessment Report",
            "generated_at": datetime.now().isoformat(),
            "target_application": scan_result.target_url,
            "scan_duration": f"{scan_result.duration_seconds:.2f} seconds",
            "executive_summary": self._generate_executive_summary(scan_result),
            "risk_breakdown": scan_result.findings_by_risk,
            "detailed_findings": [asdict(vuln) for vuln in scan_result.vulnerabilities],
            "remediation_priorities": self._prioritize_remediations(scan_result.vulnerabilities),
            "compliance_status": self._assess_compliance(scan_result)
        }
        
        return report
        
    def _generate_executive_summary(self, scan_result: SecurityScanResult) -> str:
        """Generate executive summary of security findings"""
        
        high_risk = scan_result.findings_by_risk.get('HIGH', 0)
        medium_risk = scan_result.findings_by_risk.get('MEDIUM', 0)
        low_risk = scan_result.findings_by_risk.get('LOW', 0)
        
        if high_risk > 0:
            return f"CRITICAL: {high_risk} high-risk vulnerabilities identified requiring immediate attention"
        elif medium_risk > 5:
            return f"HIGH: {medium_risk} medium-risk vulnerabilities identified requiring prompt remediation"
        elif medium_risk > 0:
            return f"MODERATE: {medium_risk} medium-risk vulnerabilities identified for scheduled remediation"
        else:
            return f"LOW: Security posture is strong with only {low_risk} low-risk findings"
            
    def _prioritize_remediations(self, vulnerabilities: List[VulnerabilityFinding]) -> List[Dict[str, Any]]:
        """Prioritize vulnerabilities for remediation"""
        
        priorities = []
        
        # Sort by risk and confidence
        sorted_vulns = sorted(vulnerabilities, 
                            key=lambda x: (self._risk_priority(x.risk), self._confidence_priority(x.confidence)),
                            reverse=True)
        
        for vuln in sorted_vulns[:10]:  # Top 10 priorities
            priority_level = self._determine_priority(vuln.risk, vuln.confidence)
            priorities.append({
                "vulnerability": vuln.name,
                "risk": vuln.risk,
                "confidence": vuln.confidence,
                "priority": priority_level,
                "url": vuln.url,
                "remediation": vuln.solution[:100] + "..." if len(vuln.solution) > 100 else vuln.solution
            })
            
        return priorities
        
    def _risk_priority(self, risk: str) -> int:
        """Convert risk level to priority number"""
        priority_map = {'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'INFO': 1}
        return priority_map.get(risk.upper(), 0)
        
    def _confidence_priority(self, confidence: str) -> int:
        """Convert confidence level to priority number"""
        priority_map = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'FALSE_POSITIVE': 0}
        return priority_map.get(confidence.upper(), 0)
        
    def _determine_priority(self, risk: str, confidence: str) -> str:
        """Determine remediation priority"""
        risk_score = self._risk_priority(risk)
        conf_score = self._confidence_priority(confidence)
        
        total_score = risk_score + conf_score
        
        if total_score >= 6:
            return "CRITICAL"
        elif total_score >= 4:
            return "HIGH"
        elif total_score >= 3:
            return "MEDIUM"
        else:
            return "LOW"
            
    def _assess_compliance(self, scan_result: SecurityScanResult) -> Dict[str, Any]:
        """Assess compliance with security standards"""
        
        findings = scan_result.vulnerabilities
        compliance = {
            "owasp_top_10_compliance": self._check_owasp_compliance(findings),
            "cwe_compliance": self._check_cwe_compliance(findings),
            "overall_rating": "COMPLIANT" if not any(v.risk == 'HIGH' for v in findings) else "NON_COMPLIANT"
        }
        
        return compliance
        
    def _check_owasp_compliance(self, findings: List[VulnerabilityFinding]) -> Dict[str, Any]:
        """Check compliance with OWASP Top 10"""
        
        owasp_categories = {
            'A01:2021-Broken Access Control': ['Access Control', 'Authorization'],
            'A02:2021-Cryptographic Failures': ['Encryption', 'SSL', 'TLS'],
            'A03:2021-Injection': ['SQL Injection', 'Command Injection'],
            'A04:2021-Insecure Design': ['Design Flaws'],
            'A05:2021-Security Misconfiguration': ['Configuration'],
            'A06:2021-Vulnerable and Outdated Components': ['Dependencies'],
            'A07:2021-Identification and Authentication Failures': ['Authentication'],
            'A08:2021-Software and Data Integrity Failures': ['Integrity'],
            'A09:2021-Security Logging and Monitoring Failures': ['Logging'],
            'A10:2021-Server-Side Request Forgery': ['SSRF']
        }
        
        compliance_status = {}
        for category, keywords in owasp_categories.items():
            found_issues = any(
                any(keyword.lower() in finding.name.lower() for keyword in keywords)
                for finding in findings
            )
            compliance_status[category] = "NON_COMPLIANT" if found_issues else "COMPLIANT"
            
        return compliance_status
        
    def _check_cwe_compliance(self, findings: List[VulnerabilityFinding]) -> Dict[str, Any]:
        """Check compliance with CWE standards"""
        
        cwe_mapping = {
            'CWE-79': 'Cross-site Scripting',
            'CWE-89': 'SQL Injection', 
            'CWE-20': 'Improper Input Validation',
            'CWE-352': 'Cross-Site Request Forgery',
            'CWE-287': 'Improper Authentication'
        }
        
        compliance_status = {}
        for cwe_id, description in cwe_mapping.items():
            found_issues = any(finding.cwe_id == cwe_id for finding in findings)
            compliance_status[cwe_id] = {
                "description": description,
                "status": "NON_COMPLIANT" if found_issues else "COMPLIANT"
            }
            
        return compliance_status

# ==================== CI/CD SECURITY INTEGRATION ====================

class SecurityCIPipeline:
    """Integrate security testing into CI/CD pipeline"""
    
    def __init__(self, security_tester: AutomatedSecurityTester):
        self.security_tester = security_tester
        self.pipeline_results = []
        
    def run_security_gate_validation(self, target_config: SecurityScanConfig,
                                   fail_on_risk: str = 'HIGH') -> Dict[str, Any]:
        """Run security validation as CI/CD gate"""
        
        print("🔒 Running Security Gate Validation")
        print("=" * 40)
        
        # Run security assessment
        scan_result = self.security_tester.run_comprehensive_security_assessment(target_config)
        
        if not scan_result:
            return {
                "status": "FAILED",
                "reason": "Security assessment failed to complete",
                "blocking_issues": ["Assessment execution failure"]
            }
            
        # Check for blocking vulnerabilities
        blocking_findings = [
            vuln for vuln in scan_result.vulnerabilities 
            if vuln.risk == fail_on_risk and vuln.confidence in ['HIGH', 'MEDIUM']
        ]
        
        gate_result = {
            "status": "PASSED" if not blocking_findings else "FAILED",
            "scan_result": asdict(scan_result),
            "blocking_issues": len(blocking_findings),
            "high_risk_findings": scan_result.findings_by_risk.get('HIGH', 0),
            "medium_risk_findings": scan_result.findings_by_risk.get('MEDIUM', 0),
            "timestamp": datetime.now().isoformat()
        }
        
        if blocking_findings:
            gate_result["blocking_details"] = [
                {
                    "vulnerability": vuln.name,
                    "url": vuln.url,
                    "risk": vuln.risk,
                    "confidence": vuln.confidence
                }
                for vuln in blocking_findings[:5]  # Show top 5
            ]
            
        self.pipeline_results.append(gate_result)
        
        status_icon = "✅" if gate_result["status"] == "PASSED" else "❌"
        print(f"{status_icon} Security Gate: {gate_result['status']}")
        print(f"Blocking Issues: {gate_result['blocking_issues']}")
        print(f"High Risk Findings: {gate_result['high_risk_findings']}")
        
        return gate_result
        
    def generate_pipeline_security_report(self) -> Dict[str, Any]:
        """Generate security report for CI/CD pipeline"""
        
        if not self.pipeline_results:
            return {"error": "No pipeline results available"}
            
        latest_result = self.pipeline_results[-1]
        
        report = {
            "pipeline_security_status": latest_result["status"],
            "assessment_timestamp": latest_result["timestamp"],
            "risk_summary": {
                "high_risk": latest_result["high_risk_findings"],
                "medium_risk": latest_result["medium_risk_findings"],
                "blocking_issues": latest_result["blocking_issues"]
            },
            "recommendations": self._generate_pipeline_recommendations(latest_result)
        }
        
        return report
        
    def _generate_pipeline_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on pipeline security results"""
        
        recommendations = []
        
        if result["status"] == "FAILED":
            recommendations.append("Block deployment due to high-risk security vulnerabilities")
            recommendations.append("Address blocking issues before proceeding with release")
            
        if result["high_risk_findings"] > 0:
            recommendations.append("Conduct immediate security review and remediation")
            
        if result["medium_risk_findings"] > 5:
            recommendations.append("Schedule security fixes in next sprint")
            
        recommendations.append("Continue regular security scanning in CI/CD pipeline")
        
        return recommendations

# ==================== DEMONSTRATION ====================

def demonstrate_security_testing_capabilities():
    """Demonstrate OWASP ZAP security testing capabilities"""
    
    print("🛡️ APPSEC AUTOMATION WITH OWASP ZAP")
    print("=" * 45)
    
    print("\nBEFORE - Manual Security Testing:")
    print("""
# Manual process
1. Start OWASP ZAP manually
2. Configure target application
3. Run spider manually
4. Perform active scan manually
5. Review results in GUI
6. Export findings manually
    """)
    
    print("\nAFTER - Automated Security Testing:")
    print("""
tester = AutomatedSecurityTester(zap_integration)
config = SecurityScanConfig(
    target_url="https://secure-ai-studio.com",
    scan_type="both",
    authentication=auth_config
)

result = tester.run_comprehensive_security_assessment(config)
report = tester.generate_security_report(result)
    """)
    
    print("\n🎯 SECURITY TESTING CAPABILITIES:")
    print("✅ Automated OWASP ZAP Integration")
    print("✅ Active and Passive Scanning")
    print("✅ Authentication Configuration")
    print("✅ Vulnerability Classification")
    print("✅ Risk Prioritization")
    print("✅ Compliance Assessment")
    print("✅ CI/CD Pipeline Integration")

def run_security_testing_demo():
    """Run complete security testing demonstration"""
    
    print("\n🧪 SECURITY TESTING DEMONSTRATION")
    print("=" * 45)
    
    # Initialize security testing components
    zap_integration = OWASPZAPIntegration()
    security_tester = AutomatedSecurityTester(zap_integration)
    ci_pipeline = SecurityCIPipeline(security_tester)
    
    # Configuration for demo
    scan_config = SecurityScanConfig(
        target_url="http://localhost:8000",
        scan_type="both",
        authentication={
            "type": "form",
            "target_urls": ["http://localhost:8000/.*"],
            "login_url": "http://localhost:8000/auth/login",
            "request_data": "username={%username%}&password={%password%}",
            "logged_in_indicator": "Welcome|Dashboard",
            "username": "test_user",
            "credentials": "username=test_user&password=test_password"
        }
    )
    
    # Run security gate validation
    gate_result = ci_pipeline.run_security_gate_validation(scan_config)
    
    # Generate security report
    security_report = security_tester.generate_security_report(
        SecurityScanResult(
            scan_id="demo_scan_001",
            target_url="http://localhost:8000",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            duration_seconds=120.0,
            total_findings=15,
            findings_by_risk={"HIGH": 2, "MEDIUM": 5, "LOW": 8},
            findings_by_type={"XSS": 3, "SQL Injection": 2, "CSRF": 1},
            vulnerabilities=[
                VulnerabilityFinding(
                    id="VULN-001",
                    name="Cross-site Scripting (XSS)",
                    risk="HIGH",
                    confidence="HIGH",
                    url="http://localhost:8000/generate/image",
                    description="Reflected XSS vulnerability found",
                    solution="Implement proper input sanitization",
                    reference=["https://owasp.org/www-community/attacks/xss/"],
                    cwe_id="CWE-79",
                    wasc_id="WASC-8",
                    timestamp=datetime.now().isoformat()
                )
            ],
            scan_summary={"demo": True}
        )
    )
    
    print(f"\n📊 SECURITY TESTING RESULTS:")
    print(f"Gate Status: {gate_result['status']}")
    print(f"High Risk Findings: {gate_result['high_risk_findings']}")
    print(f"Blocking Issues: {gate_result['blocking_issues']}")
    
    if "blocking_details" in gate_result:
        print(f"\n🚨 BLOCKING VULNERABILITIES:")
        for issue in gate_result["blocking_details"]:
            print(f"  • {issue['vulnerability']} - {issue['url']}")
    
    print(f"\n📋 EXECUTIVE SUMMARY:")
    print(f"  {security_report['executive_summary']}")
    
    return {
        "gate_result": gate_result,
        "security_report": security_report
    }

if __name__ == "__main__":
    demonstrate_security_testing_capabilities()
    print("\n" + "=" * 50)
    run_security_testing_demo()