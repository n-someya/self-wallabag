#!/bin/bash
set -e

# Deployment script for Wallabag on Google Cloud Run
# with Supabase PostgreSQL database
#
# This script automates the following steps:
# 1. Initialize Terraform
# 2. Build and push the Docker image
# 3. Apply Terraform configuration
# 4. Apply database migrations

# Configuration
PROJECT_ID="YOUR_GCP_PROJECT_ID"
REGION="us-central1"
SERVICE_NAME="wallabag"
IMAGE_TAG=$(date +%Y%m%d%H%M%S)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display steps
step() {
  echo -e "${GREEN}==>${NC} $1"
}

error() {
  echo -e "${RED}ERROR:${NC} $1"
  exit 1
}

warn() {
  echo -e "${YELLOW}WARNING:${NC} $1"
}

# Check required tools
for tool in gcloud docker terraform; do
  if ! command -v $tool &> /dev/null; then
    error "$tool is required but not installed. Please install it and try again."
  fi
done

# Check if user is logged in to gcloud
if ! gcloud auth print-access-token &> /dev/null; then
  error "You need to be logged in to gcloud. Run 'gcloud auth login' and try again."
fi

# Set project
step "Setting Google Cloud project to $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
step "Enabling required APIs"
gcloud services enable run.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com iam.googleapis.com artifactregistry.googleapis.com

# Create Artifact Registry repository if it doesn't exist
step "Creating Artifact Registry repository if needed"
if ! gcloud artifacts repositories describe $SERVICE_NAME --location=$REGION &> /dev/null; then
  gcloud artifacts repositories create $SERVICE_NAME --repository-format=docker --location=$REGION --description="Docker repository for $SERVICE_NAME"
fi

# Build Docker image
step "Building Docker image"
cd backend/src
./docker/build.sh --image $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:$IMAGE_TAG --clean
./docker/build.sh --image $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:latest --clean

# Configure Docker to use Google Cloud credentials
step "Configuring Docker authentication"
gcloud auth configure-docker $REGION-docker.pkg.dev --quiet

# Push Docker image to Artifact Registry
step "Pushing Docker image to Artifact Registry"
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:$IMAGE_TAG
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:latest

# Update container image in Terraform configuration
step "Updating Terraform configuration"
cd terraform
cat > terraform.tfvars <<EOL
# GCP Configuration
project_id          = "${PROJECT_ID}"
region              = "${REGION}"
service_name        = "${SERVICE_NAME}"

# Supabase Configuration
supabase_project_ref      = "xxxxxxxxxxxxxxxxxxxxxxx"
supabase_host             = "db.xxxxxxxxxxxxxxxxxxxxxxx.supabase.co"
supabase_port             = 5432
supabase_db_password      = "***********************************"
supabase_access_token     = ""  # Will be populated during deployment if needed

# Database Connection Information
env_vars = {
  "WALLABAG_DATABASE_HOST"     = "db.xxxxxxxxxxxxxxxxxxxxxxx.supabase.co"
  "WALLABAG_DATABASE_PORT"     = "5432"
  "WALLABAG_DATABASE_NAME"     = "postgres"
  "WALLABAG_DATABASE_USER"     = "postgres"
  "WALLABAG_DATABASE_SSL_MODE" = "require"
}

# Secret environment variables
secret_env_vars = {
  "WALLABAG_DATABASE_PASSWORD" = {
    secret_name = "wallabag-db-password"
    secret_key  = "latest"
  }
}

# Container Image Configuration
container_image     = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:${IMAGE_TAG}"

# Application Configuration
log_level           = "info"
enable_monitoring   = true
enable_custom_domain = false
EOL

# Initialize and apply Terraform
step "Initializing Terraform"
terraform init

step "Applying Terraform configuration"
terraform apply -auto-approve

# Get the Cloud Run URL
SERVICE_URL=$(terraform output -raw cloud_run_url)

# Apply database migrations
step "Creating database schema and applying migrations"
gcloud run jobs create wallabag-migrations \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/$SERVICE_NAME:$IMAGE_TAG \
  --command="bin/console" \
  --args="doctrine:migrations:migrate,--no-interaction,--env=prod" \
  --region=$REGION \
  --execute-now

# Print completion message
echo -e "\n${GREEN}Deployment completed!${NC}"
echo -e "Wallabag is now available at: ${GREEN}${SERVICE_URL}${NC}"
echo -e "Default credentials: username: wallabag, password: wallabag"
echo -e "\n${YELLOW}Note:${NC} For security, you should change the default password after first login."