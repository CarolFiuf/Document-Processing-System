# Infrastructure Setup

This directory contains infrastructure code for deploying and managing the ML platform infrastructure.

## Directory Structure

```
infrastructure/
├── terraform/
│   ├── main.tf          # Core infrastructure (VPC, EKS)
│   └── variables.tf     # Variable definitions
└── ansible/
    ├── jenkins.yml      # Jenkins deployment and configuration
    └── compute.yml      # Compute instance deployment and configuration
```

## Components

### Terraform Resources
- VPC with public and private subnets
- EKS cluster with auto-scaling node groups
- Network components (NAT Gateway, Internet Gateway)
- Minimal required IAM roles for EKS functionality

### Ansible Resources
- Jenkins server
  - Deployed in public subnet
  - Java 11, Git, Docker
  - Automated Jenkins installation and configuration
  - Secure access through admin CIDR
- Compute instance
  - Deployed in private subnet
  - Development tools (Python, Docker, Git)
  - Pre-configured Python environment
  - Secure access through VPC

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform >= 0.13
3. Ansible >= 2.9
4. Python 3.x with boto3 package
5. SSH key pair for instance access

## Deployment Steps

1. Deploy Kubernetes Infrastructure:
```bash
cd terraform
terraform init
terraform apply -var="environment=dev"
```

2. Deploy Jenkins:
```bash
cd ../ansible
ansible-playbook jenkins.yml \
  -e "vpc_id=$(terraform output -raw vpc_id)" \
  -e "public_subnet_id=$(terraform output -raw public_subnet_ids | jq -r '.[0]')" \
  -e "admin_cidr=YOUR_IP_CIDR" \
  -e "key_name=YOUR_KEY_NAME" \
  -e "ssh_key_file=PATH_TO_KEY_FILE"
```

3. Deploy Compute Instance:
```bash
ansible-playbook compute.yml \
  -e "vpc_id=$(terraform output -raw vpc_id)" \
  -e "private_subnet_id=$(terraform output -raw private_subnet_ids | jq -r '.[0]')" \
  -e "vpc_cidr=10.0.0.0/16" \
  -e "key_name=YOUR_KEY_NAME" \
  -e "ssh_key_file=PATH_TO_KEY_FILE"
```

## Access Information

### Jenkins
- Web Interface: http://<jenkins-public-ip>:8080
- Initial admin password will be displayed during deployment
- SSH access: `ssh -i <key-file> ec2-user@<jenkins-public-ip>`

### Compute Instance
- Only accessible through VPC (private subnet)
- SSH access through bastion host or VPN
- Docker and Python development environment pre-configured

### EKS Cluster
- Access using kubectl: 
```bash
aws eks update-kubeconfig --name ml-platform-dev --region ap-southeast-1
kubectl get nodes
```

## Security Notes

1. Jenkins server:
   - Only accessible from specified admin CIDR
   - SSH and web interface ports (22, 8080) restricted
   - Located in public subnet for accessibility

2. Compute instance:
   - Located in private subnet
   - SSH access only from within VPC
   - All outbound traffic allowed for package installation

3. EKS cluster:
   - Control plane in AWS-managed VPC
   - Worker nodes in private subnets
   - Minimal IAM roles for operation

## Maintenance

1. Updating Jenkins:
```bash
ansible-playbook jenkins.yml --tags update
```

2. Updating Compute Instance:
```bash
ansible-playbook compute.yml --tags update
```

3. Scaling EKS:
```bash
terraform apply -var="min_size=2" -var="max_size=10" -var="desired_size=3"
