# Main Terraform configuration for Wallabag on Google Cloud Run
# with Supabase PostgreSQL integration

# Configure required Terraform providers
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Set minimum Terraform version
  required_version = ">= 1.0.0"
}

# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Generate random string for secrets and keys
resource "random_string" "wallabag_secret" {
  length  = 32
  special = true
}

# Enable required APIs for the project
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "iam.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com"
  ])

  service            = each.key
  disable_on_destroy = false
}

# Store application secrets in Secret Manager
resource "google_secret_manager_secret" "wallabag_secrets" {
  for_each = {
    wallabag-db-password    = "Database password for Wallabag",
    wallabag-secret         = "Secret key for Wallabag application",
    wallabag-admin-password = "Admin password for Wallabag"
  }

  secret_id = each.key

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [
    google_project_service.required_apis
  ]
}

# Grant access to each secret for the Cloud Run service account
resource "google_secret_manager_secret_iam_member" "wallabag_secrets_access" {
  for_each  = google_secret_manager_secret.wallabag_secrets
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.wallabag.email}"
}

# Store the values in Secret Manager
resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.wallabag_secrets["wallabag-db-password"].id
  secret_data = var.supabase_db_password
}

resource "google_secret_manager_secret_version" "wallabag_secret" {
  secret      = google_secret_manager_secret.wallabag_secrets["wallabag-secret"].id
  secret_data = random_string.wallabag_secret.result
}

resource "google_secret_manager_secret_version" "admin_password" {
  secret      = google_secret_manager_secret.wallabag_secrets["wallabag-admin-password"].id
  secret_data = "wallabag-admin-password" # This should be changed after initial deployment
}

# Create environment variables for Cloud Run
locals {
  base_env_vars_pre_service = merge(var.env_vars, {
    SYMFONY__ENV__LOG_LEVEL               = var.log_level
    SYMFONY_ENV                           = "prod"
    SYMFONY_DEBUG                         = "0"
    SYMFONY__ENV__MAILER_TRANSPORT        = "smtp"
    SYMFONY__ENV__MAILER_USER             = "~"
    SYMFONY__ENV__MAILER_PASSWORD         = "~"
    SYMFONY__ENV__DOMAIN_NAME             = var.enable_custom_domain ? "https://${var.domain_name}" : "https://wallabag-gobijnh4fa-uc.a.run.app"
    SYMFONY__ENV__FOSUSER_REGISTRATION_CONFIRMATION_ENABLED = "false"
    GCP_PROJECT_ID                        = var.project_id
    GCP_REGION                            = var.region
  })

  secret_env_vars = merge(var.secret_env_vars, {
    POSTGRES_PASSWORD = {
      secret_name = google_secret_manager_secret.wallabag_secrets["wallabag-db-password"].secret_id
      secret_key  = "latest"
    }
    SYMFONY__ENV__DATABASE_PASSWORD = {
      secret_name = google_secret_manager_secret.wallabag_secrets["wallabag-db-password"].secret_id
      secret_key  = "latest"
    }
    SYMFONY__ENV__SECRET = {
      secret_name = google_secret_manager_secret.wallabag_secrets["wallabag-secret"].secret_id
      secret_key  = "latest"
    }
  })
}

# Set up custom domain mapping if enabled
resource "google_cloud_run_domain_mapping" "wallabag_domain" {
  count    = var.enable_custom_domain ? 1 : 0
  name     = var.domain_name
  location = var.region

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_service.wallabag.name
  }

  depends_on = [
    google_cloud_run_service.wallabag
  ]
}

# Note: base_env_vars is no longer needed as DOMAIN_NAME is now set in base_env_vars_pre_service

# Configure monitoring if enabled
resource "google_monitoring_alert_policy" "service_health" {
  count        = var.enable_monitoring ? 1 : 0
  display_name = "Wallabag Service Health"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Run Response Latency"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 2000 # 2 seconds

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  conditions {
    display_name = "Cloud Run Error Rate"

    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.labels.response_code_class = \"4xx\" OR metric.labels.response_code_class = \"5xx\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05 # 5% error rate

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_COUNT"
      }
    }
  }

  notification_channels = [] # Add notification channels as needed

  depends_on = [
    google_cloud_run_service.wallabag,
    google_project_service.required_apis
  ]
}

# Main outputs
output "deployment_complete" {
  value = "Wallabag has been deployed successfully to ${google_cloud_run_service.wallabag.status[0].url}"
}