# self-wallabag Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-09

## Active Technologies
- PHP 8.1+ (001-wallabag-web-google)
- Docker (001-wallabag-web-google)
- Terraform (001-wallabag-web-google)
- Google Cloud Run (001-wallabag-web-google)
- Supabase PostgreSQL (001-wallabag-web-google)

## Project Structure
```
backend/
├── src/
│   ├── terraform/        # Infrastructure as Code definitions
│   ├── docker/           # Docker configuration for Wallabag
│   ├── scripts/          # Deployment and configuration scripts
│   └── config/           # Configuration templates
└── tests/
    ├── integration/      # Integration tests for API and database
    └── unit/             # Unit tests for configuration logic
```

## Commands
# Deployment commands
- terraform init - Initialize Terraform configuration
- terraform plan - Preview infrastructure changes
- terraform apply - Apply infrastructure changes
- docker build - Build Wallabag Docker image
- docker push - Push Docker image to registry
- gcloud run deploy - Deploy to Google Cloud Run

## Code Style
- PHP: Follow PSR-12 coding standards
- Terraform: Follow HashiCorp style conventions
- Shell scripts: Follow Google Shell Style Guide

## Recent Changes
- 001-wallabag-web-google: Added support for connecting to existing Supabase PostgreSQL database
- 001-wallabag-web-google: Implemented API key authentication for Wallabag
- 001-wallabag-web-google: Created Terraform infrastructure for Google Cloud Run deployment

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->