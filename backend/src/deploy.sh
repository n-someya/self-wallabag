#!/bin/bash
set -e

# Deployment script for Wallabag on Google Cloud Run
# Handles building, pushing and deploying the application

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DOCKER_DIR="$SCRIPT_DIR/docker"
TERRAFORM_DIR="$SCRIPT_DIR/terraform"

# Default values
IMAGE_NAME=${IMAGE_NAME:-"wallabag"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
PROJECT_ID=${PROJECT_ID:-"$(gcloud config get-value project 2>/dev/null)"}
REGION=${REGION:-"us-central1"}
SERVICE_ACCOUNT=${SERVICE_ACCOUNT:-""}
MEMORY=${MEMORY:-"512Mi"}
CPU=${CPU:-"1"}
CONCURRENCY=${CONCURRENCY:-"80"}
MIN_INSTANCES=${MIN_INSTANCES:-"0"}
MAX_INSTANCES=${MAX_INSTANCES:-"2"}

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
show_help() {
    echo "Usage: $0 [OPTIONS] COMMAND"
    echo
    echo "Deploy Wallabag to Google Cloud Run"
    echo
    echo "Commands:"
    echo "  build         Build the Docker image"
    echo "  push          Push image to Container Registry"
    echo "  deploy        Deploy to Cloud Run"
    echo "  terraform     Run Terraform commands"
    echo "  all           Run build, push, and deploy"
    echo
    echo "Options:"
    echo "  -i, --image NAME[:TAG]    Set the image name and tag (default: wallabag:latest)"
    echo "  -p, --project ID          Google Cloud project ID"
    echo "  -r, --region REGION       Google Cloud region (default: us-central1)"
    echo "  -m, --memory SIZE         Memory allocation (default: 512Mi)"
    echo "  -c, --cpu COUNT           CPU count (default: 1)"
    echo "  -s, --service-account SA  Service account email"
    echo "  --min-instances COUNT     Minimum number of instances (default: 0)"
    echo "  --max-instances COUNT     Maximum number of instances (default: 2)"
    echo "  --concurrency COUNT       Request concurrency per instance (default: 80)"
    echo "  -h, --help                Show this help message"
    echo
}

# Parse arguments
COMMAND=""

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -i|--image)
            FULL_IMAGE_NAME="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -m|--memory)
            MEMORY="$2"
            shift 2
            ;;
        -c|--cpu)
            CPU="$2"
            shift 2
            ;;
        -s|--service-account)
            SERVICE_ACCOUNT="$2"
            shift 2
            ;;
        --min-instances)
            MIN_INSTANCES="$2"
            shift 2
            ;;
        --max-instances)
            MAX_INSTANCES="$2"
            shift 2
            ;;
        --concurrency)
            CONCURRENCY="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        build|push|deploy|terraform|all)
            COMMAND="$1"
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option or command: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check if command was provided
if [ -z "$COMMAND" ]; then
    echo -e "${RED}Error: No command specified${NC}"
    show_help
    exit 1
fi

# Check for required values
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: Google Cloud project ID not specified${NC}"
    echo "Please specify with --project or set gcloud default project"
    exit 1
fi

# Set the full image name with Container Registry path
REGISTRY_IMAGE="gcr.io/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG"

# Build the Docker image
build_image() {
    echo -e "${GREEN}Building Docker image: $REGISTRY_IMAGE${NC}"
    
    # Call the build script
    $DOCKER_DIR/build.sh --image "$REGISTRY_IMAGE" --clean
    
    echo -e "${GREEN}Docker image built successfully${NC}"
}

# Push the Docker image to Container Registry
push_image() {
    echo -e "${GREEN}Pushing Docker image to Container Registry: $REGISTRY_IMAGE${NC}"
    
    # Ensure Docker is authenticated with GCP
    gcloud auth configure-docker --quiet
    
    # Push the image
    docker push "$REGISTRY_IMAGE"
    
    echo -e "${GREEN}Docker image pushed successfully${NC}"
}

# Deploy to Cloud Run using Terraform
deploy_terraform() {
    echo -e "${GREEN}Deploying to Google Cloud Run using Terraform${NC}"
    
    # Create terraform.tfvars file
    cat > "$TERRAFORM_DIR/terraform.tfvars" <<EOL
project_id         = "$PROJECT_ID"
region             = "$REGION"
container_image    = "$REGISTRY_IMAGE"
service_name       = "$IMAGE_NAME"
memory             = "$MEMORY"
cpu                = "$CPU"
min_instances      = $MIN_INSTANCES
max_instances      = $MAX_INSTANCES
concurrency        = $CONCURRENCY
EOL

    # Add service account if specified
    if [ -n "$SERVICE_ACCOUNT" ]; then
        echo "service_account    = \"$SERVICE_ACCOUNT\"" >> "$TERRAFORM_DIR/terraform.tfvars"
    fi
    
    # Change to Terraform directory
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform
    terraform init
    
    # Apply Terraform configuration
    terraform apply -auto-approve
    
    echo -e "${GREEN}Terraform deployment completed${NC}"
    
    # Display the Cloud Run URL
    echo -e "${GREEN}Service URL:${NC} $(terraform output -raw wallabag_url)"
}

# Deploy directly to Cloud Run using gcloud
deploy_gcloud() {
    echo -e "${GREEN}Deploying to Google Cloud Run using gcloud${NC}"
    
    # Set up service account flag if provided
    SA_FLAG=""
    if [ -n "$SERVICE_ACCOUNT" ]; then
        SA_FLAG="--service-account=$SERVICE_ACCOUNT"
    fi
    
    # Deploy the container to Cloud Run
    gcloud run deploy "$IMAGE_NAME" \
        --image="$REGISTRY_IMAGE" \
        --platform=managed \
        --region="$REGION" \
        --cpu="$CPU" \
        --memory="$MEMORY" \
        --min-instances="$MIN_INSTANCES" \
        --max-instances="$MAX_INSTANCES" \
        --concurrency="$CONCURRENCY" \
        --allow-unauthenticated \
        --project="$PROJECT_ID" \
        $SA_FLAG
    
    echo -e "${GREEN}Cloud Run deployment completed${NC}"
    
    # Display the Cloud Run URL
    SERVICE_URL=$(gcloud run services describe "$IMAGE_NAME" --platform=managed --region="$REGION" --project="$PROJECT_ID" --format='value(status.url)')
    echo -e "${GREEN}Service URL:${NC} $SERVICE_URL"
}

# Run Terraform command
run_terraform() {
    echo -e "${GREEN}Running Terraform command${NC}"
    
    # Change to Terraform directory
    cd "$TERRAFORM_DIR"
    
    # Run the provided Terraform command
    terraform "$@"
}

# Execute command
case $COMMAND in
    build)
        build_image
        ;;
    push)
        push_image
        ;;
    deploy)
        # Prefer Terraform if available
        if [ -d "$TERRAFORM_DIR" ] && [ -f "$TERRAFORM_DIR/main.tf" ]; then
            deploy_terraform
        else
            deploy_gcloud
        fi
        ;;
    terraform)
        run_terraform "$@"
        ;;
    all)
        build_image
        push_image
        if [ -d "$TERRAFORM_DIR" ] && [ -f "$TERRAFORM_DIR/main.tf" ]; then
            deploy_terraform
        else
            deploy_gcloud
        fi
        ;;
    *)
        echo -e "${RED}Error: Unknown command: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac

echo -e "${GREEN}Deployment process completed!${NC}"