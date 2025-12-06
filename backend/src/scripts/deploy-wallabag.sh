#!/bin/bash
set -eo pipefail

# Script to deploy Wallabag to Google Cloud Run
# This script handles the deployment of the Wallabag Docker image to Google Cloud Run

# ======================
# Configuration
# ======================

# Default values
IMAGE_NAME="self-wallabag"
IMAGE_TAG="latest"
GCP_PROJECT_ID=""
GCP_REGION="asia-northeast1"
SERVICE_NAME="wallabag"
MIN_INSTANCES=0
MAX_INSTANCES=2
MEMORY="512Mi"
CPU="1"
CONCURRENCY=80
TIMEOUT="300s"

# Configuration file
CONFIG_FILE=".env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ======================
# Functions
# ======================

function print_usage {
    echo -e "${BLUE}Usage:${NC} $0 [OPTIONS]"
    echo 
    echo "Options:"
    echo "  -h, --help                 Display this help message"
    echo "  -t, --tag TAG              Docker image tag (default: latest)"
    echo "  -n, --name NAME            Docker image name (default: self-wallabag)"
    echo "  -p, --project PROJECT_ID   GCP project ID (required if not in config file)"
    echo "  -r, --region REGION        GCP region (default: asia-northeast1)"
    echo "  -s, --service SERVICE_NAME Service name (default: wallabag)"
    echo "  -c, --config CONFIG_FILE   Config file path (default: .env)"
    echo
}

function log_info {
    echo -e "${GREEN}[INFO]${NC} $1"
}

function log_warn {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

function log_error {
    echo -e "${RED}[ERROR]${NC} $1"
}

function check_command {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it and try again."
        exit 1
    fi
}

# ======================
# Parse arguments
# ======================

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            print_usage
            exit 0
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -p|--project)
            GCP_PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            GCP_REGION="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# ======================
# Validation
# ======================

# Check required commands
check_command "docker"
check_command "gcloud"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    log_error "Config file $CONFIG_FILE not found!"
    exit 1
fi

# Load environment variables from config file
log_info "Loading configuration from $CONFIG_FILE..."
source "$CONFIG_FILE"

# Check for GCP project ID
if [ -z "$GCP_PROJECT_ID" ]; then
    # Try to get it from gcloud config
    GCP_PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$GCP_PROJECT_ID" ]; then
        log_error "GCP project ID is required. Please specify it with --project or set it in gcloud config."
        exit 1
    else
        log_info "Using GCP project ID from gcloud config: $GCP_PROJECT_ID"
    fi
fi

# ======================
# Preparation
# ======================

# Set GCP project
log_info "Setting GCP project to $GCP_PROJECT_ID..."
gcloud config set project "$GCP_PROJECT_ID"

# Check if user is logged in to GCP
if ! gcloud auth print-identity-token &>/dev/null; then
    log_error "Not logged in to GCP. Please run 'gcloud auth login' first."
    exit 1
fi

# Check if Artifact Registry API is enabled
if ! gcloud services list --enabled | grep -q artifactregistry.googleapis.com; then
    log_warn "Artifact Registry API is not enabled. Enabling it now..."
    gcloud services enable artifactregistry.googleapis.com
fi

# Check if Cloud Run API is enabled
if ! gcloud services list --enabled | grep -q run.googleapis.com; then
    log_warn "Cloud Run API is not enabled. Enabling it now..."
    gcloud services enable run.googleapis.com
fi

# ======================
# Docker Image Handling
# ======================

# Set full image name with GCP Artifact Registry
REGISTRY_URL="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}"
REPOSITORY="wallabag-images"
FULL_IMAGE_NAME="${REGISTRY_URL}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"

# Create repository if it doesn't exist
if ! gcloud artifacts repositories describe "$REPOSITORY" --location="$GCP_REGION" &>/dev/null; then
    log_info "Creating Artifact Registry repository $REPOSITORY..."
    gcloud artifacts repositories create "$REPOSITORY" \
        --repository-format=docker \
        --location="$GCP_REGION" \
        --description="Repository for Wallabag Docker images"
fi

# Configure Docker to use GCP credentials
log_info "Configuring Docker to use GCP credentials..."
gcloud auth configure-docker "${GCP_REGION}-docker.pkg.dev" --quiet

# Tag and push the Docker image
log_info "Tagging Docker image..."
docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "$FULL_IMAGE_NAME"

log_info "Pushing Docker image to $FULL_IMAGE_NAME..."
docker push "$FULL_IMAGE_NAME"

# ======================
# Deployment to Cloud Run
# ======================

log_info "Deploying to Cloud Run as service $SERVICE_NAME..."

# Build the command with all environment variables
DEPLOY_CMD="gcloud run deploy $SERVICE_NAME \
    --image=$FULL_IMAGE_NAME \
    --region=$GCP_REGION \
    --platform=managed \
    --allow-unauthenticated \
    --min-instances=$MIN_INSTANCES \
    --max-instances=$MAX_INSTANCES \
    --memory=$MEMORY \
    --cpu=$CPU \
    --concurrency=$CONCURRENCY \
    --timeout=$TIMEOUT \
    --set-env-vars="

# Add environment variables from config file
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip comments and empty lines
    if [[ $line =~ ^[^#]*= ]] && [[ -n $line ]]; then
        # Extract variable name and value
        varname=$(echo "$line" | cut -d= -f1)
        value=$(echo "$line" | cut -d= -f2-)
        
        # Skip if value is empty or line is a function definition
        if [[ -n $value ]] && [[ ! $line =~ \(\) ]]; then
            # Escape quotes in value
            value=$(echo "$value" | sed 's/"/\\"/g')
            DEPLOY_CMD="$DEPLOY_CMD$varname=$value,"
        fi
    fi
done < "$CONFIG_FILE"

# Remove trailing comma
DEPLOY_CMD="${DEPLOY_CMD%,}"

# Execute the deployment command
eval "$DEPLOY_CMD"

# ======================
# Post-Deployment
# ======================

# Get the service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$GCP_REGION" --format='value(status.url)')

log_info "Deployment completed successfully!"
log_info "Wallabag is now available at: $SERVICE_URL"

# Display important information about accessing the service
echo
log_info "Important information:"
echo "  - The admin password is available in the container at /var/www/html/data/initial-admin-password.txt"
echo "  - API key (if enabled) is available at /var/www/html/data/keys/api-key.txt"
echo "  - To view logs: gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\""
echo "  - To get shell access: gcloud run services describe $SERVICE_NAME --region=$GCP_REGION"
echo

exit 0