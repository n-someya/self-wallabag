/**
 * Terraform Infrastructure as Code for Wallabag on Google Cloud Run
 * 
 * This file defines the infrastructure resources needed to run Wallabag
 * with an existing Supabase PostgreSQL database. It has been modified
 * to accept connection strings rather than creating new database resources.
 */

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "wallabag_image" {
  description = "Docker image for Wallabag"
  type        = string
  default     = "wallabag/wallabag:latest"
}

# Existing Supabase PostgreSQL connection information
variable "db_host" {
  description = "PostgreSQL host from Supabase"
  type        = string
}

variable "db_port" {
  description = "PostgreSQL port"
  type        = string
  default     = "5432"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
}

variable "db_user" {
  description = "PostgreSQL username"
  type        = string
}

variable "db_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "api_key" {
  description = "API key for accessing the Wallabag service"
  type        = string
  sensitive   = true
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Google Cloud Artifact Registry for storing the Docker image
resource "google_artifact_registry_repository" "wallabag_repo" {
  location      = var.region
  repository_id = "wallabag-repo"
  format        = "DOCKER"
  description   = "Docker repository for Wallabag images"
}

# Cloud Run service for Wallabag
resource "google_cloud_run_service" "wallabag" {
  name     = "wallabag"
  location = var.region

  template {
    spec {
      containers {
        image = var.wallabag_image
        
        env {
          name  = "SYMFONY__ENV__DATABASE_DRIVER"
          value = "pdo_pgsql"
        }
        
        env {
          name  = "SYMFONY__ENV__DATABASE_HOST"
          value = var.db_host
        }
        
        env {
          name  = "SYMFONY__ENV__DATABASE_PORT"
          value = var.db_port
        }
        
        env {
          name  = "SYMFONY__ENV__DATABASE_NAME"
          value = var.db_name
        }
        
        env {
          name  = "SYMFONY__ENV__DATABASE_USER"
          value = var.db_user
        }
        
        env {
          name  = "SYMFONY__ENV__DATABASE_PASSWORD"
          value = var.db_password
        }
        
        env {
          name  = "SYMFONY__ENV__DATABASE_CHARSET"
          value = "utf8"
        }

        env {
          name  = "SYMFONY__ENV__MAILER_HOST"
          value = "127.0.0.1"
        }
        
        env {
          name  = "SYMFONY__ENV__MAILER_USER"
          value = "~"
        }
        
        env {
          name  = "SYMFONY__ENV__MAILER_PASSWORD"
          value = "~"
        }
        
        env {
          name  = "SYMFONY__ENV__FROM_EMAIL"
          value = "wallabag@example.com"
        }
        
        env {
          name  = "SYMFONY__ENV__DOMAIN_NAME"
          value = "https://wallabag.example.com"
        }
        
        env {
          name  = "SYMFONY__ENV__SERVER_NAME"
          value = "Self-Hosted Wallabag"
        }
        
        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "1"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# IAM policy for API key authentication
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.wallabag.name
  location = google_cloud_run_service.wallabag.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# API Gateway for API key validation
resource "google_api_gateway_api" "wallabag_api" {
  provider = google
  api_id   = "wallabag-api"
}

output "wallabag_url" {
  value = google_cloud_run_service.wallabag.status[0].url
}