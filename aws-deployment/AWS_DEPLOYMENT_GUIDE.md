# AWS ECS Deployment Guide for ATS Resume Application

This guide provides step-by-step instructions for deploying the ATS Resume application to AWS ECS (Elastic Container Service).

## Prerequisites

### 1. AWS CLI Setup
```bash
# Install AWS CLI
# Download from: https://aws.amazon.com/cli/

# Configure AWS credentials
aws configure
# Enter your Access Key ID, Secret Access Key, region, and output format
```

### 2. Required AWS Services
- **ECS (Elastic Container Service)** - Container orchestration
- **ECR (Elastic Container Registry)** - Docker image registry
- **EFS (Elastic File System)** - Persistent storage for data
- **ALB (Application Load Balancer)** - Load balancing and SSL
- **Secrets Manager** - Secure API key storage
- **CloudWatch** - Logging and monitoring
- **VPC** - Network infrastructure

## Deployment Steps

### Step 1: Prepare AWS Infrastructure

#### 1.1 Create VPC and Subnets (if not exists)
```bash
# Use default VPC or create new one with public/private subnets
# Ensure at least 2 availability zones for high availability
```

#### 1.2 Create EFS for Persistent Storage
```bash
# Create EFS file system
aws efs create-file-system \
    --creation-token ats-resume-storage-$(date +%s) \
    --performance-mode generalPurpose \
    --throughput-mode provisioned \
    --provisioned-throughput-in-mibps 10 \
    --encrypted

# Note the FileSystemId from the response
```

#### 1.3 Create IAM Roles
```bash
# Create ECS Task Execution Role (if not exists)
aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }'

# Attach required policies
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create ECS Task Role for application permissions
aws iam create-role \
    --role-name ecsTaskRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }
        ]
    }'
```

#### 1.4 Store Secrets
```bash
# Store OpenAI API key in Secrets Manager
aws secretsmanager create-secret \
    --name "ats-resume/openai-api-key" \
    --description "OpenAI API key for ATS Resume application" \
    --secret-string "your-openai-api-key-here"
```

### Step 2: Deploy Docker Images

#### 2.1 Run Deployment Script
```bash
# Make script executable
chmod +x aws-deployment/deploy.sh

# Run deployment script
./aws-deployment/deploy.sh
```

### Step 3: Create CloudWatch Log Groups
```bash
# Create log groups
aws logs create-log-group --log-group-name /ecs/ats-backend
aws logs create-log-group --log-group-name /ecs/ats-frontend
```

### Step 4: Update Task Definitions
1. Edit `backend-task-definition.json`:
   - Replace `YOUR_ACCOUNT_ID` with your AWS account ID
   - Replace `fs-YOUR_EFS_ID` with your EFS file system ID
   - Update image URI from deployment script output

2. Edit `frontend-task-definition.json`:
   - Replace `YOUR_ACCOUNT_ID` with your AWS account ID
   - Update image URI from deployment script output
   - Update `VITE_API_URL` with your backend ALB domain

### Step 5: Register Task Definitions
```bash
# Register backend task definition
aws ecs register-task-definition \
    --cli-input-json file://aws-deployment/backend-task-definition.json

# Register frontend task definition
aws ecs register-task-definition \
    --cli-input-json file://aws-deployment/frontend-task-definition.json
```

### Step 6: Create Application Load Balancer
```bash
# Create ALB for backend
aws elbv2 create-load-balancer \
    --name ats-backend-alb \
    --subnets subnet-12345678 subnet-87654321 \
    --security-groups sg-12345678 \
    --scheme internet-facing \
    --type application

# Create target group
aws elbv2 create-target-group \
    --name ats-backend-targets \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-12345678 \
    --target-type ip \
    --health-check-path /health

# Create ALB for frontend
aws elbv2 create-load-balancer \
    --name ats-frontend-alb \
    --subnets subnet-12345678 subnet-87654321 \
    --security-groups sg-12345678 \
    --scheme internet-facing \
    --type application

# Create target group for frontend
aws elbv2 create-target-group \
    --name ats-frontend-targets \
    --protocol HTTP \
    --port 80 \
    --vpc-id vpc-12345678 \
    --target-type ip \
    --health-check-path /
```

### Step 7: Create ECS Services
```bash
# Create backend service
aws ecs create-service \
    --cluster ats-resume-cluster \
    --service-name ats-backend-service \
    --task-definition ats-backend-task:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration '{
        "awsvpcConfiguration": {
            "subnets": ["subnet-12345678", "subnet-87654321"],
            "securityGroups": ["sg-12345678"],
            "assignPublicIp": "ENABLED"
        }
    }' \
    --load-balancers '[{
        "targetGroupArn": "arn:aws:elasticloadbalancing:region:account:targetgroup/ats-backend-targets/1234567890123456",
        "containerName": "ats-backend",
        "containerPort": 8000
    }]'

# Create frontend service
aws ecs create-service \
    --cluster ats-resume-cluster \
    --service-name ats-frontend-service \
    --task-definition ats-frontend-task:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration '{
        "awsvpcConfiguration": {
            "subnets": ["subnet-12345678", "subnet-87654321"],
            "securityGroups": ["sg-12345678"],
            "assignPublicIp": "ENABLED"
        }
    }' \
    --load-balancers '[{
        "targetGroupArn": "arn:aws:elasticloadbalancing:region:account:targetgroup/ats-frontend-targets/1234567890123456",
        "containerName": "ats-frontend",
        "containerPort": 80
    }]'
```

## Security Configuration

### Security Groups
```bash
# Backend security group (allow ALB traffic)
# Inbound: Port 8000 from ALB security group
# Outbound: All traffic

# Frontend security group (allow ALB traffic)
# Inbound: Port 80 from ALB security group
# Outbound: All traffic

# ALB security group
# Inbound: Port 80, 443 from 0.0.0.0/0
# Outbound: All traffic
```

## Monitoring and Logging

### CloudWatch Alarms
```bash
# Create CPU utilization alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "ats-backend-high-cpu" \
    --alarm-description "Backend CPU utilization is too high" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2
```

## SSL Certificate (Optional)
```bash
# Request SSL certificate through ACM
aws acm request-certificate \
    --domain-name yourdomain.com \
    --subject-alternative-names *.yourdomain.com \
    --validation-method DNS

# Add HTTPS listener to ALB after certificate validation
```

## Scaling Configuration
```bash
# Enable auto-scaling
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/ats-resume-cluster/ats-backend-service \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 1 \
    --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
    --policy-name ats-backend-scale-up \
    --service-namespace ecs \
    --resource-id service/ats-resume-cluster/ats-backend-service \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{
        "TargetValue": 70.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
        }
    }'
```

## Cost Optimization

1. **Fargate Spot**: Use Fargate Spot for non-critical workloads
2. **Right-sizing**: Monitor and adjust CPU/memory allocations
3. **Scheduled Scaling**: Scale down during off-hours
4. **Reserved Capacity**: Consider Savings Plans for predictable workloads

## Troubleshooting

### Common Issues
```bash
# Check service status
aws ecs describe-services --cluster ats-resume-cluster --services ats-backend-service

# View service events
aws ecs describe-services --cluster ats-resume-cluster --services ats-backend-service --query 'services[0].events'

# Check task logs
aws logs get-log-events \
    --log-group-name /ecs/ats-backend \
    --log-stream-name ecs/ats-backend/task-id

# Check task definition
aws ecs describe-task-definition --task-definition ats-backend-task:1
```

### Health Check Issues
- Ensure health check endpoints are accessible
- Verify security group rules allow health check traffic
- Check container startup time vs. health check grace period

## Maintenance

### Updates
```bash
# Update task definition with new image
# Re-register task definition
# Update service to use new task definition revision
aws ecs update-service \
    --cluster ats-resume-cluster \
    --service ats-backend-service \
    --task-definition ats-backend-task:2
```

### Backups
- EFS automatic backups
- Database backups (if using RDS)
- Configuration backup in version control