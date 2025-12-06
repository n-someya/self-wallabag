# IAM configuration for Cloud Run API authentication
# This file configures the IAM policies for secure API key authentication

# Create a custom IAM role for API access
resource "google_project_iam_custom_role" "wallabag_api_role" {
  role_id     = "wallabagApiRole"
  title       = "Wallabag API Role"
  description = "Custom role for Wallabag API access"
  permissions = [
    "run.routes.invoke",
    "run.services.get"
  ]
}

# Create service account for API clients
resource "google_service_account" "api_client" {
  account_id   = "${var.service_name}-api-client"
  display_name = "Wallabag API Client"
  description  = "Service account for authorized API clients"
}

# Grant the API role to the service account
resource "google_project_iam_binding" "api_client_role_binding" {
  project = var.project_id
  role    = google_project_iam_custom_role.wallabag_api_role.id

  members = [
    "serviceAccount:${google_service_account.api_client.email}"
  ]
}

# IAM policy for the Cloud Run service
# NOTE: Commented out to avoid conflict with noauth policy in cloud_run.tf
# resource "google_cloud_run_service_iam_policy" "api_auth" {
#   location = google_cloud_run_service.wallabag.location
#   project  = google_cloud_run_service.wallabag.project
#   service  = google_cloud_run_service.wallabag.name
#
#   policy_data = data.google_iam_policy.api_auth_policy.policy_data
# }

# Define the IAM policy for API authentication
# data "google_iam_policy" "api_auth_policy" {
#   binding {
#     role = "roles/run.invoker"
#     members = [
#       "serviceAccount:${google_service_account.api_client.email}",
#       # Allow specific service accounts to access the API
#       # Additional service accounts can be added here as needed
#     ]
#   }
# }

# Create service account key for API clients (optional, only if needed)
resource "google_service_account_key" "api_client_key" {
  service_account_id = google_service_account.api_client.name

  # Set to true to prevent storing the private key in the state file
  # keepers = {
  #   rotation = var.key_rotation_timestamp
  # }
}

# Output the service account key (sensitive - will not be displayed in console output)
output "api_client_key" {
  value       = google_service_account_key.api_client_key.private_key
  description = "Service account key for API clients (base64-encoded)"
  sensitive   = true
}

# Configure IAM Binding to restrict specific API endpoints
# NOTE: Commented out to avoid conflict with noauth policy in cloud_run.tf
# resource "google_cloud_run_service_iam_member" "api_endpoints" {
#   location = google_cloud_run_service.wallabag.location
#   project  = google_cloud_run_service.wallabag.project
#   service  = google_cloud_run_service.wallabag.name
#   role     = "roles/run.invoker"
#   member   = "serviceAccount:${google_service_account.api_client.email}"
#
#   # Conditional binding to restrict access to specific paths
#   condition {
#     title       = "ApiEndpointsOnly"
#     description = "Only allow access to API endpoints"
#     expression  = "request.path.startsWith('/api/')"
#   }
# }

# Secrets for API key storage (for application-level authentication)
resource "google_secret_manager_secret" "api_keys" {
  secret_id = "${var.service_name}-api-keys"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

# Grant access to the Cloud Run service to read the API keys secret
resource "google_secret_manager_secret_iam_member" "api_keys_access" {
  secret_id = google_secret_manager_secret.api_keys.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.wallabag.email}"
}

# Grant the service account access to Secret Manager secrets
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.wallabag.email}"
}