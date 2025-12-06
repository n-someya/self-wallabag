# Data Model: Self-hosted Wallabag on Google Cloud Run

This document outlines the key entities and their relationships for the Wallabag deployment on Google Cloud Run with the existing Supabase PostgreSQL instance. Most of the data model is defined by Wallabag's internal structure, but we document the key entities here for reference and focus on the customizations required for our deployment.

## Core Entities

### Article

The primary entity representing a saved web article.

#### Attributes
- `id`: Unique identifier (UUID)
- `url`: Original URL of the article
- `title`: Article title extracted from content
- `content`: HTML content of the article
- `created_at`: Timestamp when the article was saved
- `updated_at`: Timestamp when the article was last modified
- `read_at`: Timestamp when the article was marked as read (nullable)
- `reading_time`: Estimated time to read the article in minutes
- `domain_name`: Extracted domain from the URL
- `mimetype`: Content type of the article
- `language`: Detected language of the article
- `preview_picture`: URL to a preview image (nullable)
- `is_archived`: Boolean indicating if the article is archived
- `is_starred`: Boolean indicating if the article is starred
- `user_id`: Reference to the user who saved the article

#### Validation Rules
- `url` must be a valid URL
- `content` must not be empty
- `created_at` cannot be in the future

#### State Transitions
- New → Unread
- Unread → Read (when `read_at` is set)
- Any → Archived (when `is_archived` is set to true)
- Any → Starred (when `is_starred` is set to true)

### User

Represents the authenticated user of the Wallabag instance.

#### Attributes
- `id`: Unique identifier (UUID)
- `username`: User's login name
- `email`: User's email address
- `password`: Hashed password
- `created_at`: Timestamp when the user was created
- `updated_at`: Timestamp when the user was last modified
- `last_login`: Timestamp of last successful login (nullable)
- `is_active`: Boolean indicating if the user account is active

#### Validation Rules
- `username` must be unique
- `email` must be a valid email format
- `password` must meet security requirements

### API Key

Represents an API key used for authentication to the service.

#### Attributes
- `id`: Unique identifier (UUID)
- `key`: The actual API key (hashed in storage)
- `name`: A descriptive name for the key
- `created_at`: Timestamp when the key was created
- `expires_at`: Timestamp when the key expires (nullable)
- `last_used_at`: Timestamp when the key was last used (nullable)
- `is_active`: Boolean indicating if the key is currently active

#### Validation Rules
- `key` must be sufficiently random (min 32 characters)
- `key` must be unique
- API key can only be used if `is_active` is true and current time is before `expires_at`

### Tag

Represents a user-defined tag for organizing articles.

#### Attributes
- `id`: Unique identifier (UUID)
- `label`: The display name of the tag
- `created_at`: Timestamp when the tag was created
- `user_id`: Reference to the user who created the tag

#### Validation Rules
- `label` must be unique per user

## Relationships

### Article_Tag

A join table representing the many-to-many relationship between Articles and Tags.

#### Attributes
- `article_id`: Reference to an Article
- `tag_id`: Reference to a Tag
- `created_at`: Timestamp when the association was created

#### Validation Rules
- Each combination of `article_id` and `tag_id` must be unique

## Configuration Entities

### Database Connection

Represents the configuration for connecting to the existing Supabase PostgreSQL database.

#### Attributes
- `host`: Database hostname (Supabase connection string)
- `port`: Database port (typically 5432 for PostgreSQL)
- `name`: Database name
- `user`: Database username
- `password`: Database password
- `ssl_mode`: SSL connection mode

#### Validation Rules
- All fields are required
- Connection must be testable with provided credentials
- Connection string will be provided rather than generated

#### Implementation Notes
- Connection string will be passed as environment variables
- No database creation will be performed as the instance already exists
- Scripts will be modified to accept existing connection details

### Cloud Run Configuration

Represents the configuration for the Google Cloud Run service.

#### Attributes
- `service_name`: Name of the Cloud Run service
- `region`: Google Cloud region for deployment
- `memory`: Memory allocation (minimum 512MB)
- `cpu`: CPU allocation
- `concurrency`: Maximum concurrent requests
- `timeout`: Request timeout setting
- `environment_variables`: Key-value map of environment variables including database connection string

#### Validation Rules
- `memory` must be at least 512MB
- `region` must be a valid Google Cloud region
- `service_name` must follow Google Cloud naming conventions

## Database Integration Strategy

### Connection Configuration

The system will be configured to connect to the existing Supabase PostgreSQL instance using the following approach:

1. **Environment Variables**:
   - Database connection parameters will be stored as environment variables in the Cloud Run service
   - Variables will include: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

2. **Configuration Files**:
   - Wallabag's `parameters.yml` configuration file will be templated to use these environment variables
   - The Docker build process will configure these parameters during image creation

3. **Deployment Scripts**:
   - `deploy.sh` will be modified to accept the connection string as an input parameter
   - The script will validate the connection before proceeding with deployment

### Schema Handling

Since we're connecting to an existing Supabase instance:

1. **Table Creation**:
   - Wallabag's first-run migration will create required tables in the database if they don't exist
   - No schema modifications will be performed on existing tables

2. **Table Namespacing**:
   - All Wallabag tables will be prefixed with `wallabag_` to avoid conflicts with other applications using the same database

3. **Backup Strategy**:
   - Regular database backups should be configured using Supabase's existing backup mechanisms
   - No additional backup procedures will be implemented in this phase