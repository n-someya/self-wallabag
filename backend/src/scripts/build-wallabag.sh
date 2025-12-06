#!/bin/bash
set -eo pipefail

# Script to build Wallabag Docker image safely
# This script handles the Docker build process for Wallabag with PostgreSQL support

# ======================
# Configuration
# ======================

# Default values
WALLABAG_VERSION="2.5.2"
IMAGE_NAME="self-wallabag"
IMAGE_TAG="latest"
BUILD_DIR="$(pwd)/backend/src/docker/build_temp"
WALLABAG_SOURCE_DIR="$(pwd)/backend/src/wallabag-source"

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
    echo "  -v, --version VERSION      Wallabag version to use (default: ${WALLABAG_VERSION})"
    echo "  -t, --tag TAG              Docker image tag (default: latest)"
    echo "  -n, --name NAME            Docker image name (default: self-wallabag)"
    echo "  -s, --source DIR           Wallabag source directory (default: ./backend/wallabag-source)"
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

function cleanup {
    log_info "Cleaning up temporary files..."
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
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
        -v|--version)
            WALLABAG_VERSION="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -s|--source)
            WALLABAG_SOURCE_DIR="$2"
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
# Preparation
# ======================

# Set trap to clean up temporary files on exit
trap cleanup EXIT

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Create temporary build directory
log_info "Creating temporary build directory..."
mkdir -p "$BUILD_DIR"

# Check if Wallabag source exists
if [ ! -d "$WALLABAG_SOURCE_DIR" ]; then
    log_info "Wallabag source directory does not exist. Downloading Wallabag ${WALLABAG_VERSION}..."
    mkdir -p "$WALLABAG_SOURCE_DIR"
    
    # Download and extract Wallabag source
    TEMP_DIR=$(mktemp -d)
    curl -L -o "${TEMP_DIR}/wallabag.tar.gz" "https://github.com/wallabag/wallabag/releases/download/${WALLABAG_VERSION}/wallabag-${WALLABAG_VERSION}.tar.gz"
    tar -xzf "${TEMP_DIR}/wallabag.tar.gz" -C "$TEMP_DIR"
    cp -r "${TEMP_DIR}/wallabag/"* "$WALLABAG_SOURCE_DIR/"
    rm -rf "$TEMP_DIR"
    
    log_info "Wallabag ${WALLABAG_VERSION} downloaded to $WALLABAG_SOURCE_DIR"
else
    log_info "Using existing Wallabag source at $WALLABAG_SOURCE_DIR"
fi

# ======================
# Build Docker Image
# ======================

log_info "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}..."

# Copy Docker files to build directory
mkdir -p "$BUILD_DIR/docker"
mkdir -p "$BUILD_DIR/config"
cp "$(pwd)/backend/src/docker/Dockerfile" "$BUILD_DIR/docker/"
cp "$(pwd)/backend/src/docker/entrypoint.sh" "$BUILD_DIR/docker/"
cp "$(pwd)/backend/src/docker/crontab" "$BUILD_DIR/docker/"
cp "$(pwd)/backend/src/docker/healthcheck.sh" "$BUILD_DIR/docker/"
cp -r "$(pwd)/backend/src/config/"* "$BUILD_DIR/config/"

# Ensure build directory has all necessary files
ls -la "$BUILD_DIR/docker/"
ls -la "$BUILD_DIR/config/"

# Build the Docker image
IMAGE_ID="${IMAGE_NAME}:${IMAGE_TAG}"

# Create a temporary context directory for the build
CONTEXT_DIR="$BUILD_DIR/context"
mkdir -p "$CONTEXT_DIR"

# Copy source code and configuration files to context directory
cp -r "$WALLABAG_SOURCE_DIR" "$CONTEXT_DIR/wallabag-source"
cp -r "$BUILD_DIR/config" "$CONTEXT_DIR/config"
cp -r "$BUILD_DIR/docker" "$CONTEXT_DIR/docker"

docker build \
    --build-arg WALLABAG_VERSION="$WALLABAG_VERSION" \
    --build-arg PHP_VERSION="8.1" \
    --build-arg COMPOSER_VERSION="2" \
    -t "$IMAGE_ID" \
    -f "$CONTEXT_DIR/docker/Dockerfile" \
    --no-cache \
    "$CONTEXT_DIR"

# Check if build was successful
if [ $? -eq 0 ]; then
    log_info "Docker image ${IMAGE_ID} built successfully!"
    
    # Display image information
    log_info "Image details:"
    docker images "$IMAGE_ID"
    
    echo
    log_info "To run the image locally:"
    echo "  docker run -d -p 8080:80 --env-file .env $IMAGE_ID"
    echo
    log_info "To push the image to a registry:"
    echo "  docker tag $IMAGE_ID your-registry/your-repo:$IMAGE_TAG"
    echo "  docker push your-registry/your-repo:$IMAGE_TAG"
    echo
else
    log_error "Docker build failed!"
    exit 1
fi

exit 0