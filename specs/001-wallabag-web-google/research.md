# Research: Self-hosted Wallabag on Google Cloud Run

## Wallabag v2 System Requirements and Performance

### Decision
Use Wallabag v2.5+ in a Docker container with PHP 8.1+, requiring at least 512MB memory allocation on Cloud Run.

### Rationale
- Wallabag v2.5+ has improved performance and security compared to older versions
- Docker deployment simplifies environment consistency and meets Cloud Run requirements
- 512MB memory allocation is sufficient for single-user deployment based on official recommendations
- PHP 8.1+ provides better performance and security than older PHP versions

### Alternatives Considered
- Custom PHP application: Rejected due to reinventing existing solution
- Self-hosted on VM: Rejected due to higher maintenance overhead
- Managed service: Rejected as Wallabag has no official managed offering

### Performance Characteristics
- Typical response time: 200-500ms for page loading
- Article parsing performance: 1-3 seconds depending on article complexity
- Storage requirements: Approximately 10KB per article (text only), 20-50KB with metadata
- Scaling: For single-user, can handle hundreds of saved articles without performance degradation

## API Key Authentication Options for Wallabag

### Decision
Implement API key authentication at the Cloud Run level using Identity and Access Management (IAM) combined with Wallabag's built-in user authentication.

### Rationale
- Cloud Run IAM provides robust API key management for service-level authentication
- Wallabag's existing user system can be used as a second authentication layer
- This approach separates infrastructure security from application security
- Allows future integration with other Google Cloud services

### Alternatives Considered
- Nginx reverse proxy with authentication: More complex to manage in serverless environment
- Custom authentication middleware: Would require modifying Wallabag code
- HTTP basic authentication: Less secure and less flexible than API keys

## Deploying PHP Applications on Google Cloud Run

### Decision
Use the official PHP Docker base image with Apache, adding Wallabag installation within a custom Dockerfile.

### Rationale
- Google Cloud Run natively supports Docker containers
- PHP + Apache is the recommended Wallabag deployment stack
- Containerization provides environment consistency and easy updates
- Official PHP images receive security updates

### Alternatives Considered
- PHP-FPM with Nginx: More complex configuration with minimal performance benefit
- Cloud Functions: Not suitable for full PHP application deployment
- App Engine: More expensive and less flexible than Cloud Run for this use case

## Connecting Wallabag to External PostgreSQL Database

### Decision
Configure Wallabag to use the existing Supabase PostgreSQL instance by customizing the `parameters.yml` file in the Docker container build process, using the provided connection string.

### Rationale
- Wallabag supports PostgreSQL natively
- The user already has a deployed Supabase PostgreSQL instance that should be reused
- Configuration can be injected during container build or via environment variables
- Separation of application and database improves maintainability

### Alternatives Considered
- SQLite: Insufficient for persistent storage in Cloud Run's ephemeral environment
- MySQL/MariaDB: Supported by Wallabag but adds complexity with minimal benefit over PostgreSQL
- Redis for caching: Will be added if performance issues arise

## Terraform Configuration for Google Cloud Run

### Decision
Use Terraform to define Cloud Run service with environment variables for PostgreSQL connection and authentication settings.

### Rationale
- Infrastructure as Code follows constitutional requirements
- Terraform has good support for Google Cloud Run
- Environment variables provide a clean way to inject configuration
- Makes deployment repeatable and consistent

### Alternatives Considered
- Manual deployment: Violates Infrastructure as Code principle
- Cloud Build: Would still need IaC and adds complexity
- Docker Compose: Not suitable for cloud deployment

## Terraform Configuration for Existing Supabase Instance

### Decision
Use Terraform to configure access to the existing Supabase PostgreSQL instance, focusing on connection management and access policies.

### Rationale
- Keeps all infrastructure defined in code
- Enables consistent access configuration
- Manages access policies centrally
- Facilitates future migration if needed
- Uses the existing Supabase instance as requested by the user

### Alternatives Considered
- Creating a new Supabase instance: Conflicts with requirement to use existing instance
- Manual Supabase setup: Violates Infrastructure as Code principle
- Direct PostgreSQL on Google Cloud: Conflicts with requirement to use Supabase

## Securing Wallabag with API Keys

### Decision
Implement a two-layer authentication approach:
1. Cloud Run IAM for service-level API key validation
2. Wallabag internal user for application-level authentication

### Rationale
- Defense in depth security strategy
- Leverages Google's robust IAM system for API keys
- Maintains Wallabag's built-in security features
- Simplifies future integration with other services

### Alternatives Considered
- Application-level API key only: Less secure
- Custom authentication proxy: Adds unnecessary complexity
- OAuth integration: Overkill for single-user system

## Future Integration for Article Analysis

### Decision
Plan for integration via direct database access from a separate analysis service, with a read-only role in Supabase.

### Rationale
- Separation of concerns between content storage and analysis
- Read-only access ensures analysis service cannot corrupt data
- Supabase supports fine-grained access control
- Enables independent scaling of analysis capabilities

### Alternatives Considered
- Webhook integration: More complex, requires modifications to Wallabag
- API-based integration: Would require additional authentication management
- Shared file storage: Less efficient for structured data

## Modification Requirements for Using Existing PostgreSQL Connection

### Decision
Modify deployment scripts and configuration to accept external PostgreSQL connection string as input rather than creating new instances.

### Rationale
- Aligns with user requirement to use existing Supabase PostgreSQL instance
- Simplifies deployment by removing database provisioning steps
- Ensures system works with provided connection string
- Maintains security by using environment variables for sensitive connection details

### Alternatives Considered
- Hardcoding connection strings: Security risk and reduces flexibility
- Creating a new database within existing Supabase instance: Unnecessary if existing database is suitable
- Using a connection proxy: Adds complexity with minimal benefit