# Wallabag Deployment Guide

This document provides comprehensive instructions for deploying Wallabag on Google Cloud Run with Supabase PostgreSQL database.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Initial Setup](#initial-setup)
4. [Terraform Deployment](#terraform-deployment)
5. [Manual Deployment](#manual-deployment)
6. [Configuration](#configuration)
7. [Security Considerations](#security-considerations)
8. [Continuous Integration/Continuous Deployment](#continuous-integrationcontinuous-deployment)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deployment, ensure you have:

1. **Google Cloud Platform Account**
   - Billing enabled
   - Google Cloud CLI installed (`gcloud`)
   - Project created with required APIs enabled:
     - Cloud Run API
     - Cloud Build API
     - Secret Manager API
     - Container Registry API

2. **Supabase Account**
   - Project created
   - PostgreSQL database credentials

3. **Required Tools**
   - Docker
   - Terraform >= 1.0.0
   - Git

4. **API Keys and Credentials**
   - Supabase API key
   - Supabase PostgreSQL connection details

## Architecture Overview

The deployment consists of:

- **Wallabag Application**: Containerized PHP application running on Cloud Run
- **Database**: Supabase PostgreSQL database
- **Authentication**: Dual-layer with Cloud Run IAM and application-level API keys
- **Infrastructure**: Managed through Terraform (IaC)

```
                           ┌────────────────┐
                           │  Google Cloud  │
                           │    Platform    │
                           └────────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                │                   │                 │
        ┌───────▼──────┐    ┌──────▼───────┐  ┌──────▼───────┐
        │  Cloud Run   │    │Secret Manager│  │ Cloud Storage│
        │  (Wallabag)  │    │ (API Keys)   │  │  (Backups)   │
        └──────────────┘    └──────────────┘  └──────────────┘
                │
                │
        ┌───────▼──────┐
        │   Supabase   │
        │  PostgreSQL  │
        └──────────────┘
```

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/self-wallabag.git
cd self-wallabag
```

### 2. Clone Wallabag Source

```bash
# Clone the Wallabag source code
cd backend/src
git clone https://github.com/wallabag/wallabag.git wallabag-source
cd wallabag-source
git checkout 2.5.2  # Or your preferred version
cd ../..
```

### 3. Set Environment Variables

Create a `.env` file at the project root:

```bash
# Generate the environment variables template
./src/config/env.sh generate --project YOUR_GCP_PROJECT_ID --database YOUR_SUPABASE_HOST
```

Edit the generated `.env` file with your specific credentials.

## Terraform Deployment

### 1. Initialize Terraform

```bash
cd backend/src/terraform
terraform init
```

### 2. Configure Terraform Variables

Create a `terraform.tfvars` file:

```
project_id              = "your-gcp-project-id"
region                  = "us-central1"
service_name            = "wallabag"
container_image         = "gcr.io/your-gcp-project-id/wallabag:latest"
memory                  = "512Mi"
cpu                     = "1"
supabase_access_token   = "your-supabase-token"
supabase_project_ref    = "your-supabase-project-ref"
supabase_host           = "your-supabase-host"
supabase_db_password    = "your-db-password"
```

### 3. Apply Terraform Configuration

```bash
terraform plan
terraform apply
```

This will:
1. Create Cloud Run service
2. Set up IAM permissions
3. Configure Supabase PostgreSQL database
4. Set up Secret Manager for sensitive values

### 4. Build and Deploy Container

Use the deploy script to build and push the Docker image:

```bash
cd ../
./deploy.sh build --project YOUR_GCP_PROJECT_ID
./deploy.sh push --project YOUR_GCP_PROJECT_ID

# Deploy with terraform
./deploy.sh terraform apply
```

## Manual Deployment

If you prefer not to use Terraform, you can deploy manually:

### 1. Build the Docker Image

```bash
cd backend/src
./docker/build.sh --image wallabag:latest --clean
```

### 2. Push to Container Registry

```bash
# Tag and push the image
docker tag wallabag:latest gcr.io/YOUR_PROJECT_ID/wallabag:latest
docker push gcr.io/YOUR_PROJECT_ID/wallabag:latest
```

### 3. Deploy to Cloud Run

```bash
gcloud run deploy wallabag \
  --image=gcr.io/YOUR_PROJECT_ID/wallabag:latest \
  --platform=managed \
  --region=us-central1 \
  --memory=512Mi \
  --cpu=1 \
  --allow-unauthenticated \
  --set-env-vars="WALLABAG_DATABASE_HOST=YOUR_SUPABASE_HOST,WALLABAG_DATABASE_NAME=wallabag,WALLABAG_DATABASE_USER=YOUR_DB_USER,SYMFONY_ENV=prod"
```

### 4. Set Up Secrets

```bash
# Create a secret for the database password
echo -n "YOUR_DB_PASSWORD" | gcloud secrets create wallabag-db-password --data-file=-

# Grant the Cloud Run service access to the secret
gcloud secrets add-iam-policy-binding wallabag-db-password \
  --member=serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

## Configuration

### Database Migrations

Run database migrations after deployment:

```bash
# Option 1: Using the script
./backend/src/config/migrations/apply_migrations.sh --env prod --force

# Option 2: Using the container
gcloud run jobs create wallabag-migrations \
  --image=gcr.io/YOUR_PROJECT_ID/wallabag:latest \
  --command="bin/console" \
  --args="doctrine:migrations:migrate,--no-interaction,--env=prod" \
  --region=us-central1
```

### Application Configuration

Key configuration files:
- `backend/src/config/parameters.yml.dist` - Application parameters template
- `backend/src/docker/entrypoint.sh` - Container startup script

To update configuration after deployment:
1. Edit environment variables in the Cloud Run console
2. Or update the Terraform configuration and reapply

## Security Considerations

### API Authentication

Two layers of authentication are implemented:
1. **Cloud Run IAM** - For service-level authentication
2. **Application API Keys** - For user-level authentication

To create an API key:

```bash
./backend/src/auth/generate-api-key.sh --user admin --name "Integration Name"
```

### HTTPS and Security Headers

Security headers are automatically configured in `backend/src/config/security.php`.

When using a custom domain:
1. Configure the domain in Google Cloud Run
2. Update the `domain_name` variable in Terraform
3. Enable `enable_custom_domain` in Terraform

### Secrets Management

Sensitive information is stored in Google Cloud Secret Manager:
- Database passwords
- Application secrets
- API keys

## Continuous Integration/Continuous Deployment

Example GitHub Actions workflow:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v0
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        export_default_credentials: true
    
    - name: Build and push
      run: |
        cd backend/src
        ./docker/build.sh --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/wallabag:${{ github.sha }} --clean
        docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/wallabag:${{ github.sha }}
    
    - name: Deploy to Cloud Run
      run: |
        cd backend/src
        ./deploy.sh deploy --project ${{ secrets.GCP_PROJECT_ID }} --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/wallabag:${{ github.sha }}
```

## Troubleshooting

### Common Issues

#### Database Connection Failures

1. Check Supabase status at the Supabase dashboard
2. Verify connection string parameters in Cloud Run environment variables
3. Check database permissions for the Wallabag user
4. Review Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wallabag"`

#### Container Startup Issues

1. Check container logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wallabag" --limit=50`
2. Verify environment variables are properly set
3. Confirm permissions for service account
4. Test the Docker container locally:
   ```bash
   docker run -p 8080:80 --env-file .env gcr.io/YOUR_PROJECT_ID/wallabag:latest
   ```

#### API Authentication Issues

1. Check if API key is properly created and active
2. Verify the IAM permissions for the Cloud Run service
3. Use the API key generation script to create a new key:
   ```bash
   ./backend/src/auth/generate-api-key.sh --user admin --name "New Key"
   ```

### Getting Support

If you encounter issues not covered in this guide:
1. Check Cloud Run and Supabase documentation
2. Review logs and error messages
3. Open an issue on the project repository
4. Consult the Wallabag community forums

---

For further assistance or feature requests, please contact the system administrator.

*Last updated: October 2025*