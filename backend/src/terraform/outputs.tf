# Output variables for Terraform

# Cloud Run service outputs
output "wallabag_url" {
  value       = google_cloud_run_service.wallabag.status[0].url
  description = "The URL of the deployed Wallabag instance"
}

output "wallabag_service_name" {
  value       = google_cloud_run_service.wallabag.name
  description = "The name of the Cloud Run service"
}

output "wallabag_service_region" {
  value       = google_cloud_run_service.wallabag.location
  description = "The region where the service is deployed"
}

# Database outputs
output "database_name" {
  value       = var.env_vars["SYMFONY__ENV__DATABASE_NAME"]
  description = "The name of the Wallabag database"
}

output "database_user" {
  value       = var.env_vars["SYMFONY__ENV__DATABASE_USER"]
  description = "The database user for the Wallabag application"
}

output "database_connection_string" {
  value       = "postgresql://${var.env_vars["SYMFONY__ENV__DATABASE_USER"]}:${var.supabase_db_password}@${var.supabase_host}:${var.supabase_port}/${var.env_vars["SYMFONY__ENV__DATABASE_NAME"]}"
  description = "The database connection string for the Wallabag application"
  sensitive   = true
}

# API authentication outputs
output "api_client_service_account" {
  value       = google_service_account.api_client.email
  description = "The service account email for API clients"
}

output "api_client_key_id" {
  value       = google_service_account_key.api_client_key.name
  description = "The ID of the service account key for API clients"
}

output "api_client_key_created_at" {
  value       = "Use 'gcloud iam service-accounts keys describe' to check creation time"
  description = "The creation time of the service account key"
}

output "api_endpoints_url" {
  value       = "${google_cloud_run_service.wallabag.status[0].url}/api"
  description = "The base URL for API endpoints"
}

# Command to get API key (for reference)
output "api_key_command" {
  value       = "gcloud secrets versions access latest --secret=${var.service_name}-api-keys --project=${var.project_id}"
  description = "Command to retrieve API keys from Secret Manager"
}

# IAM policy outputs
output "api_role_id" {
  value       = google_project_iam_custom_role.wallabag_api_role.id
  description = "The custom IAM role ID for API access"
}

# Security outputs
output "security_enabled" {
  value       = var.enable_https_redirect
  description = "Whether HTTPS redirect is enabled"
}

# Deployment information
output "deployment_time" {
  value       = timestamp()
  description = "The time when this infrastructure was deployed"
}

output "terraform_version" {
  value       = "See documentation for required version"
  description = "The version of Terraform used for deployment"
}