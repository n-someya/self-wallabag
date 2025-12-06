#!/bin/bash

# Wallabag Environment Setup Script
# This script helps you create a .env file from the template

set -e

echo "=========================================="
echo "  Wallabag Environment Setup"
echo "=========================================="
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  Warning: .env file already exists."
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        echo "Aborted. Keeping existing .env file."
        exit 0
    fi
fi

# Copy template
cp .env.example .env
echo "✓ Created .env file from template"
echo ""

# Function to prompt for value
prompt_value() {
    local var_name=$1
    local prompt_text=$2
    local default_value=$3
    local is_secret=$4

    if [ -n "$default_value" ]; then
        read -p "$prompt_text [$default_value]: " value
        value=${value:-$default_value}
    else
        if [ "$is_secret" = "true" ]; then
            read -sp "$prompt_text: " value
            echo ""
        else
            read -p "$prompt_text: " value
        fi
    fi

    # Escape special characters for sed
    value_escaped=$(echo "$value" | sed 's/[\/&]/\\&/g')

    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/${var_name}=.*/${var_name}=${value_escaped}/" .env
    else
        sed -i "s/${var_name}=.*/${var_name}=${value_escaped}/" .env
    fi
}

echo "Please provide the following information:"
echo ""

# GCP Configuration
echo "--- Google Cloud Configuration ---"
prompt_value "GCP_PROJECT_ID" "GCP Project ID" "" false
prompt_value "GCP_REGION" "GCP Region" "us-central1" false
echo ""

# Supabase Configuration
echo "--- Supabase PostgreSQL Configuration ---"
prompt_value "SUPABASE_PROJECT_REF" "Supabase Project Reference" "" false
prompt_value "SUPABASE_HOST" "Supabase Host" "aws-0-ap-northeast-1.pooler.supabase.com" false
prompt_value "SUPABASE_DB_PASSWORD" "Supabase Database Password" "" true
echo ""

# Derive SUPABASE_DB_USER from project ref
SUPABASE_PROJECT_REF=$(grep "^SUPABASE_PROJECT_REF=" .env | cut -d'=' -f2)
SUPABASE_DB_USER="postgres.${SUPABASE_PROJECT_REF}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/SUPABASE_DB_USER=.*/SUPABASE_DB_USER=${SUPABASE_DB_USER}/" .env
else
    sed -i "s/SUPABASE_DB_USER=.*/SUPABASE_DB_USER=${SUPABASE_DB_USER}/" .env
fi
echo "✓ Set SUPABASE_DB_USER to ${SUPABASE_DB_USER}"
echo ""

# Cloud Run URL (optional for initial setup)
echo "--- Cloud Run Configuration ---"
echo "Note: Cloud Run URL can be set after first deployment"
prompt_value "CLOUD_RUN_URL" "Cloud Run URL (press Enter to skip)" "https://your-service-name-XXXXXXXXXX-uc.a.run.app" false
echo ""

# Container Image
echo "--- Docker Configuration ---"
GCP_PROJECT_ID=$(grep "^GCP_PROJECT_ID=" .env | cut -d'=' -f2)
DEFAULT_IMAGE="us-central1-docker.pkg.dev/${GCP_PROJECT_ID}/wallabag/wallabag:latest"
prompt_value "CONTAINER_IMAGE" "Container Image" "$DEFAULT_IMAGE" false
echo ""

# Wallabag Secret
echo "--- Security Configuration ---"
echo "Generating random secret for WALLABAG_SECRET..."
RANDOM_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/WALLABAG_SECRET=.*/WALLABAG_SECRET=${RANDOM_SECRET}/" .env
else
    sed -i "s/WALLABAG_SECRET=.*/WALLABAG_SECRET=${RANDOM_SECRET}/" .env
fi
echo "✓ Generated random secret"
echo ""

# Local Development
echo "--- Local Development Configuration ---"
prompt_value "LOCAL_PORT" "Local Port" "8080" false
echo ""

echo "=========================================="
echo "✓ Environment setup complete!"
echo "=========================================="
echo ""
echo "Your .env file has been created with the following configuration:"
echo ""
echo "  GCP Project ID: $(grep "^GCP_PROJECT_ID=" .env | cut -d'=' -f2)"
echo "  Supabase Host: $(grep "^SUPABASE_HOST=" .env | cut -d'=' -f2)"
echo "  Local Port: $(grep "^LOCAL_PORT=" .env | cut -d'=' -f2)"
echo ""
echo "Next steps:"
echo "  1. Review the .env file and make any necessary adjustments"
echo "  2. Run 'docker-compose -f docker-compose.supabase.yml up' to test locally"
echo "  3. Update backend/src/terraform/terraform.tfvars with the same values for deployment"
echo ""
echo "⚠️  Important: Never commit the .env or terraform.tfvars files to version control!"
echo ""
