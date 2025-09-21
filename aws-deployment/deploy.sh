#!/bin/bash

# AWS ECS Deployment Script for ATS Resume Application
# This script builds images, pushes to ECR, and deploys to ECS

set -e

# Configuration
AWS_REGION="us-east-1"
ECR_REPOSITORY_BASE="ats-resume"
CLUSTER_NAME="ats-resume-cluster"
SERVICE_NAME_BACKEND="ats-backend-service"
SERVICE_NAME_FRONTEND="ats-frontend-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting AWS ECS Deployment for ATS Resume Application${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Check AWS credentials
echo -e "${YELLOW}📋 Checking AWS credentials...${NC}"
aws sts get-caller-identity || {
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
}

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"

# ECR Login
echo -e "${YELLOW}🔐 Logging into Amazon ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Function to create ECR repository if it doesn't exist
create_ecr_repo() {
    local repo_name=$1
    echo -e "${YELLOW}📦 Checking ECR repository: ${repo_name}${NC}"
    
    if ! aws ecr describe-repositories --repository-names $repo_name --region $AWS_REGION &> /dev/null; then
        echo -e "${YELLOW}📦 Creating ECR repository: ${repo_name}${NC}"
        aws ecr create-repository --repository-name $repo_name --region $AWS_REGION
        
        # Set lifecycle policy to manage image versions
        aws ecr put-lifecycle-policy --repository-name $repo_name --region $AWS_REGION --lifecycle-policy-text '{
            "rules": [
                {
                    "rulePriority": 1,
                    "selection": {
                        "tagStatus": "untagged",
                        "countType": "sinceImagePushed",
                        "countUnit": "days",
                        "countNumber": 7
                    },
                    "action": {
                        "type": "expire"
                    }
                },
                {
                    "rulePriority": 2,
                    "selection": {
                        "tagStatus": "tagged",
                        "countType": "imageCountMoreThan",
                        "countNumber": 10
                    },
                    "action": {
                        "type": "expire"
                    }
                }
            ]
        }'
    else
        echo -e "${GREEN}✅ ECR repository exists: ${repo_name}${NC}"
    fi
}

# Create ECR repositories
create_ecr_repo "${ECR_REPOSITORY_BASE}-backend"
create_ecr_repo "${ECR_REPOSITORY_BASE}-frontend"

# Build and push backend image
echo -e "${YELLOW}🔨 Building backend Docker image...${NC}"
cd backend
docker build -t $ECR_REPOSITORY_BASE-backend .

# Tag and push backend image
BACKEND_IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_BASE-backend:latest"
docker tag $ECR_REPOSITORY_BASE-backend:latest $BACKEND_IMAGE_URI
echo -e "${YELLOW}📤 Pushing backend image to ECR...${NC}"
docker push $BACKEND_IMAGE_URI
echo -e "${GREEN}✅ Backend image pushed: ${BACKEND_IMAGE_URI}${NC}"

cd ..

# Build and push frontend image
echo -e "${YELLOW}🔨 Building frontend Docker image...${NC}"
cd frontend
docker build -t $ECR_REPOSITORY_BASE-frontend .

# Tag and push frontend image
FRONTEND_IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_BASE-frontend:latest"
docker tag $ECR_REPOSITORY_BASE-frontend:latest $FRONTEND_IMAGE_URI
echo -e "${YELLOW}📤 Pushing frontend image to ECR...${NC}"
docker push $FRONTEND_IMAGE_URI
echo -e "${GREEN}✅ Frontend image pushed: ${FRONTEND_IMAGE_URI}${NC}"

cd ..

# Create ECS cluster if it doesn't exist
echo -e "${YELLOW}🏗️ Checking ECS cluster...${NC}"
if ! aws ecs describe-clusters --clusters $CLUSTER_NAME --region $AWS_REGION --query 'clusters[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
    echo -e "${YELLOW}🏗️ Creating ECS cluster: ${CLUSTER_NAME}${NC}"
    aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION
else
    echo -e "${GREEN}✅ ECS cluster exists: ${CLUSTER_NAME}${NC}"
fi

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${YELLOW}📋 Next steps:${NC}"
echo -e "1. Update task definitions with new image URIs:"
echo -e "   - Backend: ${BACKEND_IMAGE_URI}"
echo -e "   - Frontend: ${FRONTEND_IMAGE_URI}"
echo -e "2. Deploy using task definitions and service configurations"
echo -e "3. Configure Load Balancer and update security groups"
echo -e "4. Set up environment variables in ECS task definitions"