# PowerShell script for Windows deployment
# AWS ECS Deployment Script for ATS Resume Application

param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "ats-resume-cluster"
)

# Configuration
$ECR_REPOSITORY_BASE = "ats-resume"
$SERVICE_NAME_BACKEND = "ats-backend-service"
$SERVICE_NAME_FRONTEND = "ats-frontend-service"

Write-Host "🚀 Starting AWS ECS Deployment for ATS Resume Application" -ForegroundColor Green

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
    Write-Host "✅ AWS CLI is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI is not installed. Please install it first." -ForegroundColor Red
    Write-Host "Download from: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check AWS credentials
Write-Host "📋 Checking AWS credentials..." -ForegroundColor Yellow
try {
    $CallerIdentity = aws sts get-caller-identity | ConvertFrom-Json
    $AWS_ACCOUNT_ID = $CallerIdentity.Account
    Write-Host "✅ AWS Account ID: $AWS_ACCOUNT_ID" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not configured. Run 'aws configure' first." -ForegroundColor Red
    exit 1
}

# ECR Login
Write-Host "🔐 Logging into Amazon ECR..." -ForegroundColor Yellow
$LoginCommand = aws ecr get-login-password --region $Region
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to get ECR login token" -ForegroundColor Red
    exit 1
}

$LoginCommand | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$Region.amazonaws.com"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to login to ECR" -ForegroundColor Red
    exit 1
}

# Function to create ECR repository if it doesn't exist
function Create-ECR-Repository {
    param([string]$RepoName)
    
    Write-Host "📦 Checking ECR repository: $RepoName" -ForegroundColor Yellow
    
    try {
        aws ecr describe-repositories --repository-names $RepoName --region $Region 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ ECR repository exists: $RepoName" -ForegroundColor Green
        }
    } catch {
        Write-Host "📦 Creating ECR repository: $RepoName" -ForegroundColor Yellow
        aws ecr create-repository --repository-name $RepoName --region $Region
        
        if ($LASTEXITCODE -eq 0) {
            # Set lifecycle policy
            $LifecyclePolicy = @"
{
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
}
"@
            
            $LifecyclePolicy | aws ecr put-lifecycle-policy --repository-name $RepoName --region $Region --lifecycle-policy-text file://- 2>&1 | Out-Null
        }
    }
}

# Create ECR repositories
Create-ECR-Repository "$ECR_REPOSITORY_BASE-backend"
Create-ECR-Repository "$ECR_REPOSITORY_BASE-frontend"

# Build and push backend image
Write-Host "🔨 Building backend Docker image..." -ForegroundColor Yellow
Set-Location backend
docker build -t "$ECR_REPOSITORY_BASE-backend" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build backend image" -ForegroundColor Red
    exit 1
}

# Tag and push backend image
$BACKEND_IMAGE_URI = "$AWS_ACCOUNT_ID.dkr.ecr.$Region.amazonaws.com/$ECR_REPOSITORY_BASE-backend:latest"
docker tag "$ECR_REPOSITORY_BASE-backend:latest" $BACKEND_IMAGE_URI
Write-Host "📤 Pushing backend image to ECR..." -ForegroundColor Yellow
docker push $BACKEND_IMAGE_URI

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Backend image pushed: $BACKEND_IMAGE_URI" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to push backend image" -ForegroundColor Red
    exit 1
}

Set-Location ..

# Build and push frontend image
Write-Host "🔨 Building frontend Docker image..." -ForegroundColor Yellow
Set-Location frontend
docker build -t "$ECR_REPOSITORY_BASE-frontend" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build frontend image" -ForegroundColor Red
    exit 1
}

# Tag and push frontend image
$FRONTEND_IMAGE_URI = "$AWS_ACCOUNT_ID.dkr.ecr.$Region.amazonaws.com/$ECR_REPOSITORY_BASE-frontend:latest"
docker tag "$ECR_REPOSITORY_BASE-frontend:latest" $FRONTEND_IMAGE_URI
Write-Host "📤 Pushing frontend image to ECR..." -ForegroundColor Yellow
docker push $FRONTEND_IMAGE_URI

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend image pushed: $FRONTEND_IMAGE_URI" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to push frontend image" -ForegroundColor Red
    exit 1
}

Set-Location ..

# Create ECS cluster if it doesn't exist
Write-Host "🏗️ Checking ECS cluster..." -ForegroundColor Yellow
try {
    $ClusterStatus = aws ecs describe-clusters --clusters $ClusterName --region $Region --query 'clusters[0].status' --output text 2>&1
    if ($ClusterStatus -eq "ACTIVE") {
        Write-Host "✅ ECS cluster exists: $ClusterName" -ForegroundColor Green
    } else {
        Write-Host "🏗️ Creating ECS cluster: $ClusterName" -ForegroundColor Yellow
        aws ecs create-cluster --cluster-name $ClusterName --region $Region
    }
} catch {
    Write-Host "🏗️ Creating ECS cluster: $ClusterName" -ForegroundColor Yellow
    aws ecs create-cluster --cluster-name $ClusterName --region $Region
}

Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Update task definitions with new image URIs:"
Write-Host "   - Backend: $BACKEND_IMAGE_URI"
Write-Host "   - Frontend: $FRONTEND_IMAGE_URI"
Write-Host "2. Deploy using task definitions and service configurations"
Write-Host "3. Configure Load Balancer and update security groups"
Write-Host "4. Set up environment variables in ECS task definitions"