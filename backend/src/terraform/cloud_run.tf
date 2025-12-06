# Google Cloud Run service for Wallabag

# Service account for Cloud Run
resource "google_service_account" "wallabag" {
  account_id   = var.service_name
  display_name = "Service Account for ${var.service_name}"
  description  = "Service account for Wallabag running on Cloud Run"
}

# Cloud Run service
resource "google_cloud_run_service" "wallabag" {
  name     = var.service_name
  location = var.region

  template {
    spec {
      containers {
        image = var.container_image

        # Environment variables for Wallabag
        dynamic "env" {
          for_each = local.base_env_vars_pre_service
          content {
            name  = env.key
            value = env.value
          }
        }

        # Add secrets as environment variables if needed
        dynamic "env" {
          for_each = local.secret_env_vars
          content {
            name = env.key
            value_from {
              secret_key_ref {
                name = env.value.secret_name
                key  = env.value.secret_key
              }
            }
          }
        }

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        # Configure ports
        ports {
          container_port = 80
        }
      }

      # Service account to use
      service_account_name = google_service_account.wallabag.email

      # Container concurrency
      container_concurrency = var.concurrency

      # Timeout
      timeout_seconds = var.timeout
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = tostring(var.max_instances)
        "autoscaling.knative.dev/minScale" = tostring(var.min_instances)
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  depends_on = [
    google_project_service.required_apis,
    google_service_account.wallabag
  ]
}

# Cloud Run API is enabled in main.tf via required_apis

# Make the Cloud Run service publicly accessible
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location = google_cloud_run_service.wallabag.location
  project  = google_cloud_run_service.wallabag.project
  service  = google_cloud_run_service.wallabag.name

  policy_data = data.google_iam_policy.noauth.policy_data
}

# Output the service URL
output "cloud_run_url" {
  value       = google_cloud_run_service.wallabag.status[0].url
  description = "The URL of the deployed Cloud Run service"
}