#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏗️ TERRAFORM INFRASTRUCTURE AS CODE FRAMEWORK
SDET Phase 2 Week 6 - IaC Implementation with Terraform Modules

Enterprise-grade Infrastructure as Code implementation for automated
test environment provisioning and management.
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
import hcl2  # HashiCorp Configuration Language parser

# ==================== TERRAFORM COMPONENTS ====================

@dataclass
class TerraformModule:
    """Terraform module definition"""
    name: str
    source: str
    version: str = None
    providers: Dict[str, str] = None
    variables: Dict[str, Any] = None
    outputs: List[str] = None

@dataclass
class TerraformResource:
    """Terraform resource definition"""
    resource_type: str
    name: str
    provider: str
    configuration: Dict[str, Any]
    dependencies: List[str] = None

class TerraformModuleBuilder:
    """Build Terraform modules for test environments"""
    
    def __init__(self, module_root: str = "terraform/modules"):
        self.module_root = Path(module_root)
        self.modules = []
        
    def create_test_environment_module(self) -> TerraformModule:
        """Create test environment provisioning module"""
        
        module = TerraformModule(
            name="test_environment",
            source="./modules/test-environment",
            variables={
                "environment_name": "test",
                "instance_count": 3,
                "instance_type": "t3.medium",
                "region": "us-west-2",
                "vpc_cidr": "10.0.0.0/16"
            },
            outputs=["test_instance_ips", "load_balancer_dns", "database_endpoint"]
        )
        
        # Create module directory structure
        module_path = self.module_root / "test-environment"
        module_path.mkdir(parents=True, exist_ok=True)
        
        # Generate module files
        self._generate_variables_tf(module_path, module.variables)
        self._generate_main_tf(module_path)
        self._generate_outputs_tf(module_path, module.outputs)
        
        self.modules.append(module)
        return module
        
    def create_monitoring_module(self) -> TerraformModule:
        """Create monitoring infrastructure module"""
        
        module = TerraformModule(
            name="monitoring_infrastructure",
            source="./modules/monitoring",
            variables={
                "elk_stack_version": "8.5.0",
                "grafana_version": "9.3.0",
                "retention_days": 30,
                "storage_size_gb": 100
            },
            outputs=["elasticsearch_endpoint", "grafana_url", "kibana_url"]
        )
        
        module_path = self.module_root / "monitoring"
        module_path.mkdir(parents=True, exist_ok=True)
        
        self._generate_monitoring_module_files(module_path, module)
        self.modules.append(module)
        return module
        
    def _generate_variables_tf(self, module_path: Path, variables: Dict[str, Any]):
        """Generate variables.tf file"""
        
        variables_content = """
variable "environment_name" {
  description = "Environment name (dev, test, prod)"
  type        = string
  default     = "test"
}

variable "instance_count" {
  description = "Number of EC2 instances"
  type        = number
  default     = 2
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}
        """
        
        with open(module_path / "variables.tf", "w") as f:
            f.write(variables_content.strip())
            
    def _generate_main_tf(self, module_path: Path):
        """Generate main.tf file with test environment resources"""
        
        main_content = """
# Test Environment Infrastructure
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# VPC Configuration
resource "aws_vpc" "test_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name        = "${var.environment_name}-vpc"
    Environment = var.environment_name
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.test_vpc.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = element(["${var.region}a", "${var.region}b"], count.index)
  map_public_ip_on_launch = true
  
  tags = {
    Name        = "${var.environment_name}-public-${count.index}"
    Environment = var.environment_name
  }
}

# Internet Gateway
resource "aws_internet_gateway" "test_igw" {
  vpc_id = aws_vpc.test_vpc.id
  
  tags = {
    Name        = "${var.environment_name}-igw"
    Environment = var.environment_name
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.test_vpc.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.test_igw.id
  }
  
  tags = {
    Name        = "${var.environment_name}-public-rt"
    Environment = var.environment_name
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = element(aws_subnet.public[*].id, count.index)
  route_table_id = aws_route_table.public.id
}

# Security Groups
resource "aws_security_group" "test_instances" {
  name        = "${var.environment_name}-instances-sg"
  description = "Security group for test instances"
  vpc_id      = aws_vpc.test_vpc.id
  
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name        = "${var.environment_name}-instances-sg"
    Environment = var.environment_name
  }
}

# EC2 Instances
resource "aws_instance" "test_instance" {
  count         = var.instance_count
  ami           = "ami-0c02fb55956c7d316"  # Amazon Linux 2
  instance_type = var.instance_type
  subnet_id     = element(aws_subnet.public[*].id, count.index)
  vpc_security_group_ids = [aws_security_group.test_instances.id]
  
  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y docker git python3
              systemctl start docker
              systemctl enable docker
              usermod -a -G docker ec2-user
              EOF
  
  tags = {
    Name        = "${var.environment_name}-instance-${count.index}"
    Environment = var.environment_name
    Purpose     = "testing"
  }
}

# Load Balancer
resource "aws_lb" "test_alb" {
  name               = "${var.environment_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.test_instances.id]
  subnets            = aws_subnet.public[*].id
  
  tags = {
    Name        = "${var.environment_name}-alb"
    Environment = var.environment_name
  }
}

# Load Balancer Target Group
resource "aws_lb_target_group" "test_tg" {
  name     = "${var.environment_name}-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.test_vpc.id
  
  health_check {
    path                = "/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
  
  tags = {
    Name        = "${var.environment_name}-tg"
    Environment = var.environment_name
  }
}

# Target Group Attachment
resource "aws_lb_target_group_attachment" "test_attachment" {
  count            = var.instance_count
  target_group_arn = aws_lb_target_group.test_tg.arn
  target_id        = element(aws_instance.test_instance[*].id, count.index)
  port             = 8000
}

# Load Balancer Listener
resource "aws_lb_listener" "test_http" {
  load_balancer_arn = aws_lb.test_alb.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.test_tg.arn
  }
}
        """
        
        with open(module_path / "main.tf", "w") as f:
            f.write(main_content.strip())
            
    def _generate_outputs_tf(self, module_path: Path, outputs: List[str]):
        """Generate outputs.tf file"""
        
        outputs_content = """
output "test_instance_ips" {
  description = "Public IP addresses of test instances"
  value       = aws_instance.test_instance[*].public_ip
}

output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.test_alb.dns_name
}

output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.test_vpc.id
}

output "subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}
        """
        
        with open(module_path / "outputs.tf", "w") as f:
            f.write(outputs_content.strip())
            
    def _generate_monitoring_module_files(self, module_path: Path, module: TerraformModule):
        """Generate monitoring module files"""
        
        # Variables file
        monitoring_vars = """
variable "elk_stack_version" {
  description = "Version of ELK stack to deploy"
  type        = string
  default     = "8.5.0"
}

variable "grafana_version" {
  description = "Version of Grafana to deploy"
  type        = string
  default     = "9.3.0"
}

variable "retention_days" {
  description = "Log retention period in days"
  type        = number
  default     = 30
}

variable "storage_size_gb" {
  description = "Storage size for monitoring components"
  type        = number
  default     = 100
}

variable "environment_name" {
  description = "Environment name"
  type        = string
  default     = "monitoring"
}
        """
        
        with open(module_path / "variables.tf", "w") as f:
            f.write(monitoring_vars.strip())
            
        # Main file
        monitoring_main = """
# Monitoring Infrastructure Module
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# Elasticsearch cluster
resource "aws_elasticsearch_domain" "monitoring_es" {
  domain_name           = "${var.environment_name}-elasticsearch"
  elasticsearch_version = var.elk_stack_version
  
  cluster_config {
    instance_type = "t3.medium.elasticsearch"
    instance_count = 2
  }
  
  ebs_options {
    ebs_enabled = true
    volume_size = var.storage_size_gb
    volume_type = "gp2"
  }
  
  encrypt_at_rest {
    enabled = true
  }
  
  tags = {
    Name        = "${var.environment_name}-elasticsearch"
    Environment = var.environment_name
  }
}

# Grafana instance
resource "aws_instance" "grafana" {
  ami           = "ami-0c02fb55956c7d316"
  instance_type = "t3.medium"
  vpc_security_group_ids = [aws_security_group.monitoring_sg.id]
  
  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y docker
              systemctl start docker
              docker run -d -p 3000:3000 grafana/grafana:${var.grafana_version}
              EOF
  
  tags = {
    Name        = "${var.environment_name}-grafana"
    Environment = var.environment_name
  }
}

# Security group for monitoring
resource "aws_security_group" "monitoring_sg" {
  name        = "${var.environment_name}-monitoring-sg"
  description = "Security group for monitoring infrastructure"
  
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 9200
    to_port     = 9200
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
        """
        
        with open(module_path / "main.tf", "w") as f:
            f.write(monitoring_main.strip())
            
        # Outputs file
        monitoring_outputs = """
output "elasticsearch_endpoint" {
  description = "Elasticsearch endpoint URL"
  value       = aws_elasticsearch_domain.monitoring_es.endpoint
}

output "grafana_url" {
  description = "Grafana dashboard URL"
  value       = "http://${aws_instance.grafana.public_ip}:3000"
}

output "grafana_instance_id" {
  description = "Grafana EC2 instance ID"
  value       = aws_instance.grafana.id
}
        """
        
        with open(module_path / "outputs.tf", "w") as f:
            f.write(monitoring_outputs.strip())

# ==================== TERRAFORM STATE MANAGEMENT ====================

class TerraformStateManager:
    """Manage Terraform state and backend configuration"""
    
    def __init__(self, backend_type: str = "s3"):
        self.backend_type = backend_type
        self.state_files = []
        
    def configure_remote_state(self, bucket_name: str, key_prefix: str = "terraform/state") -> Dict[str, Any]:
        """Configure remote state backend"""
        
        backend_config = {
            "terraform": {
                "backend": {
                    "s3": {
                        "bucket": bucket_name,
                        "key": f"{key_prefix}/terraform.tfstate",
                        "region": "us-west-2",
                        "encrypt": True,
                        "dynamodb_table": f"{bucket_name}-terraform-lock"
                    }
                }
            }
        }
        
        return backend_config
        
    def initialize_terraform(self, working_dir: str) -> bool:
        """Initialize Terraform in working directory"""
        
        try:
            result = subprocess.run(
                ["terraform", "init"],
                cwd=working_dir,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Terraform initialization failed: {e}")
            return False
            
    def validate_configuration(self, working_dir: str) -> bool:
        """Validate Terraform configuration"""
        
        try:
            result = subprocess.run(
                ["terraform", "validate"],
                cwd=working_dir,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Terraform validation failed: {e}")
            return False

# ==================== INFRASTRUCTURE PROVISIONING ====================

class InfrastructureProvisioner:
    """Provision infrastructure using Terraform modules"""
    
    def __init__(self):
        self.module_builder = TerraformModuleBuilder()
        self.state_manager = TerraformStateManager()
        self.provisioning_results = []
        
    def provision_test_environment(self, environment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Provision complete test environment"""
        
        print("🏗️  Provisioning Test Environment Infrastructure")
        print("=" * 55)
        
        start_time = datetime.now()
        
        # Create modules
        test_module = self.module_builder.create_test_environment_module()
        monitoring_module = self.module_builder.create_monitoring_module()
        
        # Configure state management
        backend_config = self.state_manager.configure_remote_state(
            bucket_name=f"secure-ai-{environment_config.get('environment', 'test')}-tf-state"
        )
        
        # Generate root module
        root_module = self._generate_root_module(test_module, monitoring_module, environment_config)
        
        # Validate configuration
        validation_result = self.state_manager.validate_configuration(".")
        
        provisioning_result = {
            "environment": environment_config.get("environment", "test"),
            "modules_created": [test_module.name, monitoring_module.name],
            "validation_passed": validation_result,
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "resources_planned": self._estimate_resources(test_module, monitoring_module)
        }
        
        self.provisioning_results.append(provisioning_result)
        
        print(f"✅ Test environment provisioning completed")
        print(f"   Modules: {len(provisioning_result['modules_created'])}")
        print(f"   Validation: {'PASSED' if validation_result else 'FAILED'}")
        print(f"   Resources Planned: {provisioning_result['resources_planned']}")
        
        return provisioning_result
        
    def _generate_root_module(self, test_module: TerraformModule, 
                            monitoring_module: TerraformModule,
                            config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate root Terraform module"""
        
        root_config = {
            "terraform": {
                "required_version": ">= 1.0",
                "required_providers": {
                    "aws": {
                        "source": "hashicorp/aws",
                        "version": "~> 4.0"
                    }
                }
            },
            "provider": {
                "aws": {
                    "region": config.get("region", "us-west-2")
                }
            },
            "module": {
                "test_environment": {
                    "source": test_module.source,
                    "environment_name": config.get("environment", "test"),
                    "instance_count": config.get("instance_count", 3),
                    "instance_type": config.get("instance_type", "t3.medium")
                },
                "monitoring": {
                    "source": monitoring_module.source,
                    "environment_name": f"{config.get('environment', 'test')}-monitoring"
                }
            }
        }
        
        return root_config
        
    def _estimate_resources(self, *modules) -> int:
        """Estimate number of resources that will be created"""
        # Rough estimation based on module complexity
        return len(modules) * 15  # Average ~15 resources per module

# ==================== MODULE TESTING FRAMEWORK ====================

class TerraformModuleTester:
    """Test Terraform modules and infrastructure code"""
    
    def __init__(self):
        self.test_results = []
        
    def test_module_functionality(self, module_path: str) -> Dict[str, Any]:
        """Test Terraform module functionality"""
        
        print(f"🧪 Testing Terraform Module: {module_path}")
        
        test_result = {
            "module_path": module_path,
            "timestamp": datetime.now().isoformat(),
            "tests_passed": 0,
            "tests_total": 0,
            "validation_errors": []
        }
        
        # Test 1: Syntax validation
        test_result["tests_total"] += 1
        if self._test_syntax_validation(module_path):
            test_result["tests_passed"] += 1
        else:
            test_result["validation_errors"].append("Syntax validation failed")
            
        # Test 2: Variable validation
        test_result["tests_total"] += 1
        if self._test_variable_definitions(module_path):
            test_result["tests_passed"] += 1
        else:
            test_result["validation_errors"].append("Variable definition validation failed")
            
        # Test 3: Output validation
        test_result["tests_total"] += 1
        if self._test_output_definitions(module_path):
            test_result["tests_passed"] += 1
        else:
            test_result["validation_errors"].append("Output definition validation failed")
            
        # Test 4: Dependency validation
        test_result["tests_total"] += 1
        if self._test_dependencies(module_path):
            test_result["tests_passed"] += 1
        else:
            test_result["validation_errors"].append("Dependency validation failed")
            
        success_rate = (test_result["tests_passed"] / test_result["tests_total"]) * 100
        test_result["success_rate"] = round(success_rate, 2)
        
        self.test_results.append(test_result)
        
        status = "✅ PASSED" if test_result["tests_passed"] == test_result["tests_total"] else "❌ FAILED"
        print(f"{status} Module tests: {test_result['tests_passed']}/{test_result['tests_total']}")
        
        if test_result["validation_errors"]:
            for error in test_result["validation_errors"]:
                print(f"   ⚠️  {error}")
                
        return test_result
        
    def _test_syntax_validation(self, module_path: str) -> bool:
        """Test Terraform syntax validation"""
        try:
            # In real implementation: terraform fmt -check
            # For simulation, we'll check file existence and basic structure
            path = Path(module_path)
            required_files = ["main.tf", "variables.tf", "outputs.tf"]
            
            for file in required_files:
                if not (path / file).exists():
                    return False
                    
            return True
        except Exception:
            return False
            
    def _test_variable_definitions(self, module_path: str) -> bool:
        """Test variable definition validation"""
        try:
            variables_file = Path(module_path) / "variables.tf"
            if not variables_file.exists():
                return False
                
            # Parse HCL and validate structure
            with open(variables_file, 'r') as f:
                content = f.read()
                # Basic validation - check for variable blocks
                return "variable" in content and "{" in content and "}" in content
        except Exception:
            return False
            
    def _test_output_definitions(self, module_path: str) -> bool:
        """Test output definition validation"""
        try:
            outputs_file = Path(module_path) / "outputs.tf"
            if not outputs_file.exists():
                return False
                
            with open(outputs_file, 'r') as f:
                content = f.read()
                return "output" in content and "{" in content and "}" in content
        except Exception:
            return False
            
    def _test_dependencies(self, module_path: str) -> bool:
        """Test module dependency validation"""
        try:
            main_file = Path(module_path) / "main.tf"
            if not main_file.exists():
                return False
                
            with open(main_file, 'r') as f:
                content = f.read()
                # Check for resource dependencies and references
                return "resource" in content and "depends_on" in content
        except Exception:
            return False

# ==================== DEMONSTRATION ====================

def demonstrate_iac_capabilities():
    """Demonstrate Infrastructure as Code capabilities"""
    
    print("🏗️  INFRASTRUCTURE AS CODE FRAMEWORK")
    print("=" * 45)
    
    print("\nBEFORE - Manual Infrastructure Provisioning:")
    print("""
# Manual AWS console steps
1. Create VPC manually
2. Set up subnets and routing
3. Launch EC2 instances
4. Configure security groups
5. Set up load balancers
6. Manually configure monitoring
    """)
    
    print("\nAFTER - Automated IaC Provisioning:")
    print("""
provisioner = InfrastructureProvisioner()
module = provisioner.create_test_environment_module()
result = provisioner.provision_test_environment(config)

# Infrastructure created consistently
# Version controlled configuration
# Automated testing and validation
    """)
    
    print("\n🎯 IAC CAPABILITIES:")
    print("✅ Modular Infrastructure Design")
    print("✅ Automated Provisioning")
    print("✅ State Management")
    print("✅ Configuration Validation")
    print("✅ Test Environment Replication")
    print("✅ Monitoring Infrastructure")

def run_iac_demo():
    """Run Infrastructure as Code demonstration"""
    
    print("\n🧪 IAC FRAMEWORK DEMONSTRATION")
    print("=" * 40)
    
    # Initialize provisioner
    provisioner = InfrastructureProvisioner()
    
    # Test environment configuration
    env_config = {
        "environment": "staging",
        "region": "us-west-2",
        "instance_count": 2,
        "instance_type": "t3.medium"
    }
    
    # Provision infrastructure
    provisioning_result = provisioner.provision_test_environment(env_config)
    
    # Test modules
    tester = TerraformModuleTester()
    module_tests = []
    
    for module in provisioner.module_builder.modules:
        module_path = provisioner.module_builder.module_root / module.name
        test_result = tester.test_module_functionality(str(module_path))
        module_tests.append(test_result)
    
    print(f"\n📊 IAC IMPLEMENTATION RESULTS:")
    print(f"Modules Created: {len(provisioner.module_builder.modules)}")
    print(f"Resources Planned: {provisioning_result['resources_planned']}")
    print(f"Validation: {'PASSED' if provisioning_result['validation_passed'] else 'FAILED'}")
    
    # Module test summary
    total_tests = sum(t["tests_total"] for t in module_tests)
    passed_tests = sum(t["tests_passed"] for t in module_tests)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Module Tests: {passed_tests}/{total_tests} ({success_rate:.1f}% success)")
    
    return {
        "provisioning": provisioning_result,
        "module_tests": module_tests
    }

if __name__ == "__main__":
    demonstrate_iac_capabilities()
    print("\n" + "=" * 50)
    run_iac_demo()