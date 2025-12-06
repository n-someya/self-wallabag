# Wallabag on Google Cloud Run

This directory contains documentation for the Wallabag web clipping service deployed on Google Cloud Run with Supabase PostgreSQL.

## Documentation

- [API Documentation](api.md): Comprehensive guide to using the Wallabag API
- [Deployment Guide](deployment.md): Instructions for deploying Wallabag on Google Cloud Run
- [Maintenance Guide](maintenance.md): System maintenance procedures and best practices
- [Quickstart Test Report](quickstart_test_report.md): Results of system testing following the quickstart guide

## Getting Started

To get started with your Wallabag deployment:

1. Follow the instructions in the [Deployment Guide](deployment.md)
2. Configure authentication using the API key generation script
3. Connect browser extensions or mobile apps to your instance

## Architecture

The Wallabag deployment consists of:

- **Application**: Wallabag running in a container on Google Cloud Run
- **Database**: PostgreSQL database hosted on Supabase
- **Authentication**: Two-layer auth with Cloud Run IAM and API keys
- **Infrastructure**: Managed via Terraform

## Contact

For support or questions, please contact the system administrator or open an issue in the project repository.

*Last updated: October 2025*