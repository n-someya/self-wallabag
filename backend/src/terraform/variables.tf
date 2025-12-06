# Google Cloud Run variables
variable "project_id" {
  description = "The ID of the GCP project"
  type        = string
}

variable "region" {
  description = "The GCP region to deploy resources"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "wallabag"
}

variable "container_image" {
  description = "The Docker image URL for Wallabag"
  type        = string
}

variable "memory" {
  description = "Memory allocation for the Cloud Run service"
  type        = string
  default     = "512Mi"
}

variable "cpu" {
  description = "CPU allocation for the Cloud Run service"
  type        = string
  default     = "1"
}

variable "concurrency" {
  description = "Maximum number of concurrent requests per container"
  type        = number
  default     = 80
}

variable "timeout" {
  description = "Request timeout in seconds"
  type        = number
  default     = 300
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 2
}

variable "env_vars" {
  description = "Environment variables for the Cloud Run service"
  type        = map(string)
  default     = {}
}

variable "secret_env_vars" {
  description = "Secret environment variables for the Cloud Run service"
  type = map(object({
    secret_name = string
    secret_key  = string
  }))
  default = {}
}

# API authentication variables
variable "enable_api_auth" {
  description = "Enable IAM authentication for API endpoints"
  type        = bool
  default     = true
}

variable "api_client_name" {
  description = "Name for the API client service account"
  type        = string
  default     = "wallabag-api-client"
}

variable "api_key_rotation_days" {
  description = "Number of days before API key rotation"
  type        = number
  default     = 90
}

# Application API key variables
variable "app_api_key_length" {
  description = "Length of application-level API keys"
  type        = number
  default     = 64
}

variable "app_api_key_expiry_days" {
  description = "Expiry days for application-level API keys"
  type        = number
  default     = 365
}

# IAM permissions
variable "api_permissions" {
  description = "List of IAM permissions to grant to API service account"
  type        = list(string)
  default = [
    "run.routes.invoke",
    "run.services.get"
  ]
}

# Supabase variables
variable "supabase_access_token" {
  description = "Supabase access token"
  type        = string
  sensitive   = true
}

variable "supabase_project_ref" {
  description = "Supabase project reference"
  type        = string
}

variable "supabase_host" {
  description = "Supabase PostgreSQL host"
  type        = string
}

variable "supabase_port" {
  description = "Supabase PostgreSQL port"
  type        = number
  default     = 5432
}

variable "supabase_db_password" {
  description = "Password for Wallabag database user"
  type        = string
  sensitive   = true
}


# Domain and TLS settings
variable "domain_name" {
  description = "Custom domain name for the Wallabag service"
  type        = string
  default     = ""
}

variable "enable_custom_domain" {
  description = "Enable custom domain mapping"
  type        = bool
  default     = false
}

# Security settings
variable "enable_https_redirect" {
  description = "Enable HTTPS redirect"
  type        = bool
  default     = true
}

variable "security_headers" {
  description = "Security headers to be added to responses"
  type        = map(string)
  default = {
    "Strict-Transport-Security" = "max-age=31536000; includeSubDomains"
    "X-Content-Type-Options"    = "nosniff"
    "X-Frame-Options"           = "DENY"
    "X-XSS-Protection"          = "1; mode=block"
    "Content-Security-Policy"   = "default-src 'self'"
  }
}

# Monitoring and logging
variable "enable_monitoring" {
  description = "Enable Cloud Monitoring for the service"
  type        = bool
  default     = true
}

variable "log_level" {
  description = "Log level for the application"
  type        = string
  default     = "info"
  validation {
    condition     = contains(["debug", "info", "warning", "error"], var.log_level)
    error_message = "Log level must be one of: debug, info, warning, error"
  }
}