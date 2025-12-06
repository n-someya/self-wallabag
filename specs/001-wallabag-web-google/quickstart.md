# Quickstart Guide: Self-hosted Wallabag on Google Cloud Run

This guide walks through the initial setup and testing of your self-hosted Wallabag service on Google Cloud Run with the existing Supabase PostgreSQL database and API key authentication.

## Prerequisites

- Google Cloud account with billing enabled
- Existing Supabase PostgreSQL connection details:
  - Host URL
  - Port
  - Database name
  - Username
  - Password
- Docker installed locally for testing
- Terraform CLI installed
- Git repository cloned

## Step 1: Infrastructure Setup

### Configure Environment Variables

Create a `.env` file with your configuration:

```shell
# Create environment file with your existing Supabase PostgreSQL details
cat > .env <<EOL
# Google Cloud settings
GCP_PROJECT_ID=your-gcp-project-id
GCP_REGION=us-central1

# Existing Supabase PostgreSQL connection details
DB_HOST=your-supabase-db-host
DB_PORT=5432
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password

# API authentication
API_KEY=$(openssl rand -base64 32)
EOL

# Load the environment variables
source .env
```

### Deploy Infrastructure with Terraform

```shell
# Navigate to the infrastructure directory
cd backend/terraform

# Initialize Terraform
terraform init

# Preview the changes
terraform plan \
  -var="project_id=$GCP_PROJECT_ID" \
  -var="region=$GCP_REGION" \
  -var="db_host=$DB_HOST" \
  -var="db_port=$DB_PORT" \
  -var="db_name=$DB_NAME" \
  -var="db_user=$DB_USER" \
  -var="db_password=$DB_PASSWORD" \
  -var="api_key=$API_KEY"

# Apply the infrastructure changes
terraform apply \
  -var="project_id=$GCP_PROJECT_ID" \
  -var="region=$GCP_REGION" \
  -var="db_host=$DB_HOST" \
  -var="db_port=$DB_PORT" \
  -var="db_name=$DB_NAME" \
  -var="db_user=$DB_USER" \
  -var="db_password=$DB_PASSWORD" \
  -var="api_key=$API_KEY"

# Note the outputs for the next steps
# - wallabag_url: The URL of your Wallabag service
```

### Verify Resources

After deployment, verify the following resources:

1. Google Cloud Run service is running
2. Connection to the existing Supabase database is successful
3. API key authentication is configured

## Step 2: Build and Deploy Custom Wallabag Image

```shell
# Navigate to the Docker build directory
cd ../docker

# Build the custom Wallabag image with your existing database connection
docker build \
  --build-arg DB_HOST=$DB_HOST \
  --build-arg DB_PORT=$DB_PORT \
  --build-arg DB_NAME=$DB_NAME \
  --build-arg DB_USER=$DB_USER \
  --build-arg DB_PASSWORD=$DB_PASSWORD \
  -t gcr.io/$GCP_PROJECT_ID/wallabag:latest .

# Push to Google Container Registry
docker push gcr.io/$GCP_PROJECT_ID/wallabag:latest

# Update the Cloud Run service to use your custom image
gcloud run services update wallabag \
  --image gcr.io/$GCP_PROJECT_ID/wallabag:latest \
  --region $GCP_REGION
```

## Step 3: Test Basic Access

### Verify Service Access with API Key

```shell
# Store the service URL
WALLABAG_URL=$(terraform output -raw wallabag_url)

# Test basic access to the service with your API key
curl -H "X-API-Key: $API_KEY" $WALLABAG_URL

# You should see the Wallabag login page or a JSON response
```

### Login to Wallabag

1. Open your browser and navigate to your Cloud Run URL
2. Add your API key to the request using a browser extension like ModHeader
3. Log in with the default credentials:
   - Username: `wallabag`
   - Password: `wallabag`
4. Change the default password immediately after first login

## Step 4: Configure Browser Extension

### Install Browser Extension

1. Install the Wallabag browser extension for your browser:
   - [Chrome Extension](https://chrome.google.com/webstore/detail/wallabager/gbmgphmejlcoihgedabhgjdkcahacjlj)
   - [Firefox Add-on](https://addons.mozilla.org/en-US/firefox/addon/wallabagger/)

### Configure Extension

1. Open the extension settings
2. Set the Wallabag URL to your Cloud Run URL
3. Configure API credentials (your Wallabag credentials, not the API key)
4. Test saving an article to verify functionality

## Step 5: Test Key Scenarios

### Test Article Clipping

1. Navigate to a webpage you want to save
2. Use the browser extension to clip the article
3. Verify the article appears in your Wallabag instance

### Test Article Management

1. Tag a saved article
2. Mark an article as read
3. Archive an article
4. Search for articles using the search functionality

### Test API Access

```shell
# First get an OAuth token
TOKEN_RESPONSE=$(curl -s -X POST "$WALLABAG_URL/oauth/v2/token" \
  -H "X-API-Key: $API_KEY" \
  -d "grant_type=password&client_id=wallabag_api&client_secret=wallabag_api_secret&username=wallabag&password=wallabag")

# Extract access token
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

# List all articles
curl -H "Authorization: Bearer $ACCESS_TOKEN" -H "X-API-Key: $API_KEY" "$WALLABAG_URL/api/entries"

# Save a new article
curl -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/article"}' \
  "$WALLABAG_URL/api/entries"
```

## Troubleshooting

### API Key Issues

If you encounter "Unauthorized" errors:
1. Verify your API key is valid and not expired
2. Check that you're including it in the `X-API-Key` header
3. Verify IAM permissions in Google Cloud

### Database Connection Issues

If database connections fail:
1. Check the Supabase console for database status
2. Verify connection strings in environment variables
3. Examine Cloud Run logs for connection errors:
   ```shell
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wallabag" --limit 10
   ```

### Article Parsing Issues

If articles aren't parsing correctly:
1. Check if the source website blocks content scrapers
2. Try using the "Reparse article" function in Wallabag
3. Check for content compatibility issues in the logs

## Next Steps

After completing this quickstart:

1. Create a backup strategy for your database
2. Set up HTTPS with a custom domain if desired
3. Explore Wallabag's tagging and organization features
4. Prepare for future article analysis service integration

## Verifying Database Connection

To ensure your Wallabag instance is correctly using the existing Supabase PostgreSQL database:

```shell
# Check database tables in Supabase
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" -c "\dt wallabag_*"

# Verify article data is stored in the database
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" -c "SELECT COUNT(*) FROM wallabag_entry;"
```

You should see Wallabag's tables created in your existing Supabase database with the prefix `wallabag_`.